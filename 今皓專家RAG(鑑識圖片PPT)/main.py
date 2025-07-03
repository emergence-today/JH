"""
FastAPI 服務器 - 提供 RAG 查詢 API
支援 Qdrant 知識庫檢索和圖片 URL 回傳
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
from pathlib import Path
import uvicorn

from rag_system import TeachingRAGSystem
from config import Config

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 FastAPI 應用
app = FastAPI(
    title="圖面識別教學 RAG API",
    description="基於 Qdrant 向量資料庫的教學型 RAG 查詢服務",
    version="1.0.0"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態檔案服務（用於提供圖片）
if os.path.exists("images"):
    app.mount("/images", StaticFiles(directory="images"), name="images")

# 全域變數
rag_system = None

# Pydantic 模型
class QueryRequest(BaseModel):
    """查詢請求模型"""
    question: str

class FlowiseRequest(BaseModel):
    """Flowise 查詢請求模型"""
    question: str
    chatId: str

class FlowiseResponse(BaseModel):
    """Flowise 查詢回應模型"""
    text: str
    question: str
    chatId: str
    sessionId: str
    chatMessageId: str

class ImageInfo(BaseModel):
    """圖片資訊模型"""
    has_images: bool
    image_url: Optional[str] = None
    image_analysis: Optional[str] = None
    technical_symbols: List[str] = []

class SourceInfo(BaseModel):
    """來源資訊模型"""
    page_num: int
    topic: str
    sub_topic: str
    content: str
    content_type: str
    keywords: List[str]
    similarity_score: float
    relevance_reason: str
    image_info: ImageInfo

class QueryResponse(BaseModel):
    """查詢回應模型"""
    answer: str
    sources: List[SourceInfo]
    total_sources: int
    query_time: Optional[float] = None

class HealthResponse(BaseModel):
    """健康檢查回應模型"""
    status: str
    qdrant_connected: bool
    chunks_loaded: int
    images_available: int

@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化 RAG 系統"""
    global rag_system
    try:
        logger.info("正在初始化 RAG 系統...")
        rag_system = TeachingRAGSystem()
        
        # 載入處理後的文件段落
        if os.path.exists("processed_chunks.jsonl"):
            rag_system.load_processed_chunks("processed_chunks.jsonl")
            logger.info(f"已載入 {len(rag_system.chunks)} 個文件段落")
        else:
            logger.warning("未找到 processed_chunks.jsonl 檔案")
        
        # 確保向量已生成
        rag_system.create_embeddings()
        logger.info("RAG 系統初始化完成")
        
    except Exception as e:
        logger.error(f"RAG 系統初始化失敗: {e}")
        raise

def get_image_url(image_path: str) -> Optional[str]:
    """生成圖片的完整 URL - 使用 S3 雲端儲存"""
    if not image_path:
        return None

    # 提取檔案名稱
    filename = os.path.basename(image_path)

    # S3 基礎 URL
    s3_base_url = "https://jh-expert-agent.s3.ap-northeast-1.amazonaws.com"

    # 檔案名稱需要 URL 編碼（因為包含中文）
    from urllib.parse import quote
    encoded_filename = quote(filename)

    # 生成 S3 URL
    image_url = f"{s3_base_url}/{encoded_filename}"

    return image_url

@app.get("/", response_model=Dict[str, str])
async def root():
    """根路徑 - API 資訊"""
    return {
        "message": "圖面識別教學 RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查端點"""
    try:
        # 檢查 RAG 系統狀態
        if rag_system is None:
            return HealthResponse(
                status="error",
                qdrant_connected=False,
                chunks_loaded=0,
                images_available=0
            )
        
        # 檢查 Qdrant 連線
        qdrant_connected = True
        try:
            # 嘗試獲取集合資訊
            collection_info = rag_system.qdrant_client.get_collection(rag_system.collection_name)
            qdrant_connected = True
        except Exception:
            qdrant_connected = False
        
        # 統計圖片數量
        images_count = 0
        if os.path.exists("images"):
            images_count = len([f for f in os.listdir("images") if f.endswith(('.png', '.jpg', '.jpeg'))])
        
        return HealthResponse(
            status="healthy" if qdrant_connected else "degraded",
            qdrant_connected=qdrant_connected,
            chunks_loaded=len(rag_system.chunks) if rag_system.chunks else 0,
            images_available=images_count
        )
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return HealthResponse(
            status="error",
            qdrant_connected=False,
            chunks_loaded=0,
            images_available=0
        )

@app.post("/test", response_model=QueryResponse)
async def test_rag(request: QueryRequest):
    """RAG 查詢端點"""
    if rag_system is None:
        raise HTTPException(status_code=500, detail="RAG 系統未初始化")

    try:
        import time
        start_time = time.time()

        logger.info(f"收到查詢: {request.question}")

        # 使用 RAG 系統生成回答
        response = rag_system.generate_teaching_response(
            query=request.question,
            mode="qa",  # 固定使用問答模式
            topic_filter=None
        )

        # 收集所有圖片 URL
        image_urls = []
        for source in response.get("sources", []):
            if source.get("has_images", False) and source.get("image_path"):
                image_url = get_image_url(source["image_path"])
                if image_url:
                    image_urls.append(image_url)

        # 在回答後面添加圖片 URL
        answer = response["answer"]
        if image_urls:
            answer += "\n\n📷 相關圖片："
            for i, url in enumerate(image_urls, 1):
                answer += f"\n{i}. {url}"

        # 轉換來源資訊格式
        sources = []
        for source in response.get("sources", []):
            # 處理圖片資訊
            image_info = ImageInfo(has_images=False)

            if source.get("has_images", False):
                image_url = None
                if source.get("image_path"):
                    image_url = get_image_url(source["image_path"])

                image_info = ImageInfo(
                    has_images=True,
                    image_url=image_url,
                    image_analysis=source.get("image_analysis", ""),
                    technical_symbols=source.get("technical_symbols", [])
                )

            source_info = SourceInfo(
                page_num=source["page_num"],
                topic=source["topic"],
                sub_topic=source["sub_topic"],
                content=source.get("content", ""),
                content_type=source["content_type"],
                keywords=source["keywords"],
                similarity_score=source["similarity_score"],
                relevance_reason=source["relevance"],
                image_info=image_info
            )
            sources.append(source_info)

        query_time = time.time() - start_time

        return QueryResponse(
            answer=answer,  # 使用修改後的 answer
            sources=sources,
            total_sources=len(sources),
            query_time=query_time
        )

    except Exception as e:
        logger.error(f"查詢處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")

@app.post("/query", response_model=FlowiseResponse)
async def query_rag(request: FlowiseRequest):
    """RAG 查詢端點"""
    if rag_system is None:
        raise HTTPException(status_code=500, detail="RAG 系統未初始化")

    try:
        import time
        import uuid

        logger.info(f"收到查詢: {request.question} (chatId: {request.chatId})")

        # 使用 RAG 系統生成回答
        response = rag_system.generate_teaching_response(
            query=request.question,
            mode="qa",  # 固定使用問答模式
            topic_filter=None
        )

        # 收集所有圖片 URL
        image_urls = []
        for source in response.get("sources", []):
            if source.get("has_images", False) and source.get("image_path"):
                image_url = get_image_url(source["image_path"])
                if image_url:
                    image_urls.append(image_url)

        # 在回答後面添加圖片 URL
        answer = response["answer"]
        if image_urls:
            answer += "\n\n📷 相關圖片："
            for i, url in enumerate(image_urls, 1):
                answer += f"\n{i}. {url}"

        # 生成唯一的 sessionId 和 chatMessageId
        session_id = f"session_{request.chatId}_{int(time.time())}"
        chat_message_id = str(uuid.uuid4())

        return FlowiseResponse(
            text=answer,
            question=request.question,
            chatId=request.chatId,
            sessionId=session_id,
            chatMessageId=chat_message_id
        )

    except Exception as e:
        logger.error(f"查詢處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")

@app.get("/test", response_model=QueryResponse)
async def test_rag_get(
    question: str = Query(..., description="要查詢的問題")
):
    """GET 方式的測試查詢端點（方便測試）"""
    query_request = QueryRequest(question=question)
    return await test_rag(query_request)

@app.get("/topics", response_model=List[str])
async def get_available_topics():
    """獲取可用的主題列表"""
    if rag_system is None or not rag_system.chunks:
        return []
    
    topics = set()
    for chunk in rag_system.chunks:
        if chunk.topic:
            topics.add(chunk.topic)
    
    return sorted(list(topics))

@app.get("/stats", response_model=Dict[str, Any])
async def get_system_stats():
    """獲取系統統計資訊"""
    if rag_system is None:
        return {"error": "RAG 系統未初始化"}
    
    try:
        # 統計文件段落
        total_chunks = len(rag_system.chunks) if rag_system.chunks else 0
        vision_chunks = 0
        topics = set()
        
        if rag_system.chunks:
            for chunk in rag_system.chunks:
                if hasattr(chunk, 'has_images') and chunk.has_images:
                    vision_chunks += 1
                if chunk.topic:
                    topics.add(chunk.topic)
        
        # 統計圖片檔案
        images_count = 0
        if os.path.exists("images"):
            images_count = len([f for f in os.listdir("images") if f.endswith(('.png', '.jpg', '.jpeg'))])
        
        return {
            "total_chunks": total_chunks,
            "vision_chunks": vision_chunks,
            "text_only_chunks": total_chunks - vision_chunks,
            "total_topics": len(topics),
            "available_topics": sorted(list(topics)),
            "images_available": images_count,
            "collection_name": rag_system.collection_name if rag_system else None
        }
        
    except Exception as e:
        logger.error(f"獲取統計資訊失敗: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # 開發模式運行
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
