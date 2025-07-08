"""
FastAPI 服務器 - 提供 RAG 查詢 API
支援 Qdrant 知識庫檢索和圖片 URL 回傳
"""

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import uvicorn
import tempfile
import shutil
import uuid
import time
import tiktoken
import json
import asyncio

from rag_system import TeachingRAGSystem
from config import Config
from pdf_processor import PDFProcessor
from file_converter import FileConverter

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全域變數
rag_system = None
memory_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時初始化
    global rag_system, memory_manager
    try:
        logger.info("正在初始化 RAG 系統...")
        rag_system = TeachingRAGSystem()

        # 檢查是否需要載入處理後的文件段落
        # 只有在 Qdrant 集合不存在或為空時才載入本地檔案
        if rag_system.should_load_local_chunks():
            if os.path.exists("processed_chunks.jsonl"):
                rag_system.load_processed_chunks("processed_chunks.jsonl")
                logger.info(f"已載入 {len(rag_system.chunks)} 個文件段落")
                # 確保向量已生成
                rag_system.create_embeddings()
            else:
                logger.warning("未找到 processed_chunks.jsonl 檔案，且 Qdrant 集合為空")
        else:
            logger.info("Qdrant 集合已存在且包含資料，跳過本地檔案載入")

        logger.info("RAG 系統初始化完成")

        # 初始化記憶管理器
        memory_manager = MemoryManager()
        logger.info("記憶管理器初始化完成")

        # 檢查圖片目錄
        if os.path.exists("images"):
            logger.info(f"圖片目錄存在: images/ - 將通過 /images/{{filename}} 端點提供")
        else:
            logger.warning("images 目錄不存在")

    except Exception as e:
        logger.error(f"系統初始化失敗: {e}")
        raise

    yield

    # 關閉時清理（如果需要）
    logger.info("應用關閉")

# 初始化 FastAPI 應用
app = FastAPI(
    title="圖面識別教學 RAG API",
    description="基於 Qdrant 向量資料庫的教學型 RAG 查詢服務",
    version="1.0.0",
    root_path="/api/v1/JH",
    lifespan=lifespan
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 圖片檔案將通過手動端點 /images/{filename} 提供
# 不使用 StaticFiles 掛載，避免與 root_path 衝突
# 圖片目錄檢查將在應用啟動時進行

# 記憶管理系統
class MemoryManager:
    """聊天記憶管理器"""

    def __init__(self, max_tokens: int = 8000, model_name: str = "gpt-3.5-turbo"):
        self.sessions = {}  # 儲存所有會話的記憶
        self.max_tokens = max_tokens
        self.model_name = model_name
        self.encoding = tiktoken.encoding_for_model(model_name)

    def get_session(self, session_id: str) -> List[Dict]:
        """獲取會話記憶"""
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {
                    "role": "system",
                    "content": """你是一位專業的品管教育訓練講師助手，具有以下特點：
1. 能夠記住對話歷史，提供連貫的對話體驗
2. 基於提供的教材內容回答問題
3. 用清楚、友善的方式解釋技術概念
4. 會參考之前的對話內容來提供更個人化的回答
5. 使用繁體中文回答問題"""
                }
            ]
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        """添加訊息到會話記憶"""
        messages = self.get_session(session_id)
        messages.append({"role": role, "content": content})

        # 檢查token限制並清理記憶
        self._manage_memory(session_id)

    def _calculate_tokens(self, messages: List[Dict]) -> int:
        """計算訊息列表的token數量"""
        total_tokens = 0
        for msg in messages:
            total_tokens += len(self.encoding.encode(msg["content"]))
        return total_tokens

    def _manage_memory(self, session_id: str):
        """管理記憶，避免超過token限制"""
        messages = self.sessions[session_id]
        total_tokens = self._calculate_tokens(messages)

        # 如果超過限制，移除早期的對話（保留system message）
        while total_tokens > self.max_tokens and len(messages) > 1:
            # 移除最早的用戶或助手訊息（保留system message）
            if len(messages) > 1:
                messages.pop(1)
                total_tokens = self._calculate_tokens(messages)

        logger.info(f"會話 {session_id} 目前token數量: {total_tokens}")

    def get_session_summary(self, session_id: str) -> Dict:
        """獲取會話摘要資訊"""
        if session_id not in self.sessions:
            return {"exists": False}

        messages = self.sessions[session_id]
        return {
            "exists": True,
            "message_count": len(messages) - 1,  # 扣除system message
            "total_tokens": self._calculate_tokens(messages),
            "last_activity": time.time()
        }

    def clear_session(self, session_id: str):
        """清除會話記憶"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def list_sessions(self) -> List[str]:
        """列出所有會話ID"""
        return list(self.sessions.keys())



# Pydantic 模型


class FlowiseRequest(BaseModel):
    """Flowise 查詢請求模型"""
    question: str
    chatId: str

class NewChatRequest(BaseModel):
    """新的聊天請求模型"""
    user_query: str
    streaming: bool = False
    sessionId: str

class FlowiseResponse(BaseModel):
    """Flowise 查詢回應模型"""
    text: str
    question: str
    chatId: str
    sessionId: str
    chatMessageId: str

class NewChatResponse(BaseModel):
    """新的聊天回應模型"""
    text: str
    user_query: str
    sessionId: str
    chatMessageId: str
    streaming: bool = False

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



class HealthResponse(BaseModel):
    """健康檢查回應模型"""
    status: str
    qdrant_connected: bool
    chunks_loaded: int
    images_available: int

class ProcessPDFResponse(BaseModel):
    """PDF處理回應模型"""
    success: bool
    message: str
    chunks_processed: int
    images_extracted: int
    collection_name: str
    processing_time: Optional[float] = None
    errors: List[str] = []

class ChatRequest(BaseModel):
    """聊天請求模型"""
    message: str
    session_id: Optional[str] = None
    use_rag: bool = True
    top_k: int = 3

class ChatResponse(BaseModel):
    """聊天回應模型"""
    response: str
    session_id: str
    message_count: int
    total_tokens: int
    sources: List[SourceInfo] = []
    rag_used: bool = False

class SessionInfo(BaseModel):
    """會話資訊模型"""
    session_id: str
    exists: bool
    message_count: int = 0
    total_tokens: int = 0

class CollectionInfo(BaseModel):
    """集合資訊模型"""
    collection_name: str
    vectors_count: int
    points_count: int
    status: str
    exists: bool

class CollectionCountResponse(BaseModel):
    """集合數量檢查回應模型"""
    success: bool
    collection_info: Optional[CollectionInfo] = None
    error_message: Optional[str] = None
    last_activity: Optional[float] = None



def get_image_url(image_path: str) -> Optional[str]:
    """生成圖片的完整 URL - 使用後端API路徑"""
    if not image_path:
        return None

    # 提取檔案名稱，處理可能的路徑分隔符問題
    filename = os.path.basename(image_path.replace('\\', '/'))

    # 後端 API 基礎 URL
    api_base_url = "https://uat.heph-ai.net/api/v1/JH"

    # 檔案名稱需要 URL 編碼（因為包含中文）
    from urllib.parse import quote
    encoded_filename = quote(filename)

    # 生成後端 API URL
    image_url = f"{api_base_url}/images/{encoded_filename}"

    return image_url

async def stream_chat_response(request: NewChatRequest):
    """串流聊天回應生成器"""
    try:
        import uuid
        from openai import OpenAI

        logger.info(f"開始串流回應: {request.user_query} (sessionId: {request.sessionId})")

        # 使用 sessionId 作為 session_id
        session_id = request.sessionId

        # 獲取會話記憶
        messages = memory_manager.get_session(session_id)

        # 添加用戶訊息到記憶
        memory_manager.add_message(session_id, "user", request.user_query)

        # 準備回應內容
        sources = []
        rag_used = False
        image_urls = []

        # 檢索相關內容 (預設啟用RAG)
        # 檢查 Qdrant 集合是否有資料，而不是檢查本地 chunks
        if rag_system.has_vector_data():
            try:
                # 檢索相關文件段落
                retrieval_results = rag_system.retrieve_relevant_chunks(
                    query=request.user_query,
                    top_k=3  # 預設使用3個相關文件
                )

                if retrieval_results:
                    rag_used = True

                    # 準備RAG上下文
                    rag_context = "\n\n".join([
                        f"【{result.chunk.topic} - {result.chunk.sub_topic}】\n{result.chunk.content}"
                        for result in retrieval_results
                    ])

                    # 添加RAG上下文到對話
                    rag_message = f"""基於以下教材內容回答問題：

{rag_context}

用戶問題：{request.user_query}

請結合教材內容和對話歷史，用清楚友善的方式回答問題。如果教材中有相關圖片，請在回答中提及。"""

                    # 收集圖片 URL
                    for result in retrieval_results:
                        chunk = result.chunk
                        if hasattr(chunk, 'image_path') and chunk.image_path:
                            image_url = get_image_url(chunk.image_path)
                            if image_url and image_url not in image_urls:
                                image_urls.append(image_url)

            except Exception as e:
                logger.error(f"RAG檢索失敗: {e}")
                rag_used = False

        # 準備對話訊息
        temp_messages = messages.copy()
        if rag_used:
            temp_messages.append({"role": "user", "content": rag_message})
        else:
            # 如果沒有RAG內容，直接使用原始問題
            temp_messages.append({"role": "user", "content": request.user_query})

        # 調用OpenAI API生成串流回應
        client = OpenAI(api_key=Config.OPENAI_API_KEY)

        stream = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=temp_messages,
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE,
            stream=True
        )

        # 收集完整回應用於記憶儲存
        full_response = ""

        # 串流輸出
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                yield f"data: {json.dumps({'content': content, 'type': 'text'}, ensure_ascii=False)}\n\n"

        # 添加圖片 URL
        if image_urls:
            full_response += "\n\n📷 相關圖片："
            for i, url in enumerate(image_urls, 1):
                full_response += f"\n{i}. {url}"
                newline_content = f'\n{i}. {url}'
                yield f"data: {json.dumps({'content': newline_content, 'type': 'image_url'}, ensure_ascii=False)}\n\n"

        # 發送完成信號
        message_id = str(uuid.uuid4())
        yield f"data: {json.dumps({'type': 'done', 'sessionId': session_id, 'chatMessageId': message_id}, ensure_ascii=False)}\n\n"

        # 添加助手回應到記憶
        memory_manager.add_message(session_id, "assistant", full_response)

        logger.info(f"串流回應完成 - 會話: {session_id}, RAG: {rag_used}")

    except Exception as e:
        logger.error(f"串流回應失敗: {e}")
        yield f"data: {json.dumps({'error': f'串流回應失敗: {str(e)}'}, ensure_ascii=False)}\n\n"

@app.get("/", response_model=Dict[str, str])
async def root():
    """根路徑 - API 資訊"""
    return {
        "message": "圖面識別教學 RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/current-collection")
async def get_current_collection():
    """獲取當前使用的 Qdrant 集合資訊"""
    try:
        if rag_system is None:
            raise HTTPException(status_code=500, detail="RAG系統未初始化")

        collection_info = rag_system.get_collection_info()

        return {
            "current_collection": rag_system.collection_name,
            "qdrant_url": rag_system.qdrant_url,
            "collection_info": collection_info,
            "has_vector_data": rag_system.has_vector_data()
        }
    except Exception as e:
        logger.error(f"獲取當前集合資訊失敗: {e}")
        return {
            "current_collection": rag_system.collection_name if rag_system else "未知",
            "qdrant_url": rag_system.qdrant_url if rag_system else "未知",
            "error": str(e)
        }

@app.get("/images/{filename}")
@app.head("/images/{filename}")
async def serve_image(filename: str):
    """手動提供圖片檔案"""
    try:
        from fastapi.responses import FileResponse
        from urllib.parse import unquote

        # URL解碼檔案名稱
        decoded_filename = unquote(filename)
        logger.info(f"請求的檔案名稱: {filename}")
        logger.info(f"解碼後的檔案名稱: {decoded_filename}")

        # 處理可能的路徑問題
        # 如果檔案名稱包含路徑分隔符，只取檔案名稱部分
        clean_filename = os.path.basename(decoded_filename.replace('\\', '/'))
        file_path = os.path.join("images", clean_filename)

        logger.info(f"清理後的檔案名稱: {clean_filename}")
        logger.info(f"完整檔案路徑: {file_path}")

        # 檢查檔案是否存在
        if not os.path.exists(file_path):
            # 列出images目錄中的相似檔案
            similar_files = []
            if os.path.exists("images"):
                for f in os.listdir("images"):
                    if clean_filename.lower() in f.lower() or f.lower() in clean_filename.lower():
                        similar_files.append(f)

            logger.warning(f"圖片檔案不存在: {file_path}")
            logger.warning(f"相似檔案: {similar_files}")
            raise HTTPException(
                status_code=404,
                detail=f"圖片檔案不存在: {clean_filename}. 相似檔案: {similar_files[:3]}"
            )

        # 檢查是否為圖片檔案
        if not clean_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            raise HTTPException(status_code=400, detail="不支援的檔案格式")

        logger.info(f"成功提供圖片檔案: {file_path}")
        return FileResponse(file_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提供圖片檔案時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")

@app.get("/debug/images")
async def debug_images():
    """調試圖片檔案端點"""
    try:
        if not os.path.exists("images"):
            return {"error": "images目錄不存在"}

        # 列出所有圖片檔案
        image_files = []
        for file in os.listdir("images"):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join("images", file)
                file_size = os.path.getsize(file_path)
                image_files.append({
                    "filename": file,
                    "size": file_size,
                    "url": f"/images/{file}"
                })

        return {
            "total_images": len(image_files),
            "images": image_files[:10],  # 只顯示前10個
            "images_directory_exists": True,
            "static_mount_path": "/images"
        }
    except Exception as e:
        return {"error": str(e)}

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

@app.post("/query-with-memory")
async def query_flowise_with_memory(request: NewChatRequest):
    """
    新格式的記憶對話API

    接收新格式的請求，使用記憶對話功能
    - **user_query**: 用戶問題
    - **sessionId**: 聊天會話ID
    - **streaming**: 是否使用串流模式

    具有完整的會話記憶功能，支援RAG檢索
    """
    if rag_system is None:
        raise HTTPException(status_code=500, detail="RAG系統未初始化")

    # 如果啟用 streaming，返回 StreamingResponse
    if request.streaming:
        return StreamingResponse(
            stream_chat_response(request),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    try:
        import uuid

        logger.info(f"收到記憶對話查詢: {request.user_query} (sessionId: {request.sessionId})")

        # 使用 sessionId 作為 session_id
        session_id = request.sessionId

        # 獲取會話記憶
        messages = memory_manager.get_session(session_id)

        # 添加用戶訊息到記憶
        memory_manager.add_message(session_id, "user", request.user_query)

        # 準備回應內容
        response_content = ""
        sources = []
        rag_used = False

        # 檢索相關內容 (預設啟用RAG)
        if rag_system.has_vector_data():
            try:
                # 檢索相關文件段落
                retrieval_results = rag_system.retrieve_relevant_chunks(
                    query=request.user_query,
                    top_k=3  # 預設使用3個相關文件
                )

                if retrieval_results:
                    rag_used = True

                    # 準備RAG上下文
                    rag_context = "\n\n".join([
                        f"【{result.chunk.topic} - {result.chunk.sub_topic}】\n{result.chunk.content}"
                        for result in retrieval_results
                    ])

                    # 添加RAG上下文到對話
                    rag_message = f"""基於以下教材內容回答問題：

{rag_context}

用戶問題：{request.user_query}

請結合教材內容和對話歷史，用清楚友善的方式回答問題。如果教材中有相關圖片，請在回答中提及。"""

                    # 準備來源資訊
                    for result in retrieval_results:
                        chunk = result.chunk

                        # 安全地存取視覺相關屬性
                        has_images = hasattr(chunk, 'has_images') and getattr(chunk, 'has_images', False)
                        image_path = getattr(chunk, 'image_path', None) if has_images else None
                        image_analysis = getattr(chunk, 'image_analysis', "") if has_images else ""
                        technical_symbols = getattr(chunk, 'technical_symbols', []) if has_images else []

                        # 調試日誌
                        logger.info(f"檢索結果調試 - 頁面: {chunk.page_num}, has_images: {has_images}, image_path: {image_path}")

                        image_info = ImageInfo(
                            has_images=has_images,
                            image_url=get_image_url(image_path) if image_path else None,
                            image_analysis=image_analysis,
                            technical_symbols=technical_symbols
                        )

                        sources.append(SourceInfo(
                            page_num=chunk.page_num,
                            topic=chunk.topic,
                            sub_topic=chunk.sub_topic,
                            content=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                            content_type=chunk.content_type,
                            keywords=chunk.keywords or [],
                            similarity_score=result.similarity_score,
                            relevance_reason=f"與問題相關度: {result.similarity_score:.3f}",
                            image_info=image_info
                        ))

            except Exception as e:
                logger.warning(f"RAG檢索失敗: {e}")

        # 準備發送給OpenAI的訊息
        temp_messages = messages.copy()
        if rag_used:
            temp_messages.append({"role": "user", "content": rag_message})
        else:
            # 如果沒有RAG內容，直接使用原始問題
            temp_messages.append({"role": "user", "content": request.user_query})

        # 調用OpenAI API生成回應
        from openai import OpenAI
        client = OpenAI(api_key=Config.OPENAI_API_KEY)

        completion = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=temp_messages,
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE
        )

        response_content = completion.choices[0].message.content

        # 收集圖片URL並添加到回應中
        image_urls = []
        for source in sources:
            if source.image_info.has_images and source.image_info.image_url:
                image_urls.append(source.image_info.image_url)

        # 在回答後面添加圖片 URL (保持與原始 /query 端點一致的格式)
        if image_urls:
            response_content += "\n\n📷 相關圖片："
            for i, url in enumerate(image_urls, 1):
                response_content += f"\n{i}. {url}"

        # 添加助手回應到記憶
        memory_manager.add_message(session_id, "assistant", response_content)

        # 生成回應ID
        message_id = str(uuid.uuid4())

        # 獲取會話統計
        session_summary = memory_manager.get_session_summary(session_id)

        logger.info(f"記憶對話完成 - 會話: {session_id}, RAG: {rag_used}, 訊息數: {session_summary['message_count']}")

        # 對於非串流模式，回傳簡化的 JSON 格式
        return {"reply": response_content}

    except Exception as e:
        logger.error(f"記憶對話處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"記憶對話處理失敗: {str(e)}")






@app.post("/process-file", response_model=ProcessPDFResponse)
async def process_file(
    file: UploadFile = File(..., description="支援的文件格式：PDF、Excel(.xlsx/.xls)、Word(.docx/.doc)、PowerPoint(.pptx/.ppt)"),
    collection_name: Optional[str] = Query(None, description="自定義集合名稱，如不提供則使用預設"),
    enable_vision: bool = Query(True, description="是否啟用視覺分析"),
    force_recreate: bool = Query(False, description="是否強制重新創建集合")
):
    """
    處理上傳的多格式文件並自動embedding到Qdrant

    支援的格式：
    - PDF (.pdf) - 直接處理
    - Excel (.xlsx, .xls) - 自動轉換為PDF後處理
    - Word (.docx, .doc) - 自動轉換為PDF後處理
    - PowerPoint (.pptx, .ppt) - 自動轉換為PDF後處理

    - **file**: 要處理的文件
    - **collection_name**: 可選的自定義集合名稱
    - **enable_vision**: 是否啟用GPT-4o視覺分析
    - **force_recreate**: 是否強制重新創建向量集合
    """
    import time
    start_time = time.time()
    errors = []

    # 初始化檔案轉換器
    file_converter = FileConverter()

    # 檢查文件類型
    if not file_converter.is_supported_format(file.filename):
        supported_formats = list(file_converter.supported_formats.keys())
        raise HTTPException(
            status_code=400,
            detail=f"不支援的檔案格式。支援的格式: {', '.join(supported_formats)}"
        )

    try:
        # 獲取檔案副檔名
        file_ext = Path(file.filename).suffix.lower()

        # 創建臨時文件來儲存上傳的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            # 將上傳的文件內容寫入臨時文件
            shutil.copyfileobj(file.file, temp_file)
            temp_input_path = temp_file.name

        logger.info(f"開始處理文件: {file.filename} (格式: {file_ext})")

        # 如果不是PDF，先轉換為PDF
        if file_ext != '.pdf':
            logger.info(f"正在將 {file_ext} 格式轉換為PDF...")
            temp_pdf_path = temp_input_path.replace(file_ext, '.pdf')

            # 執行格式轉換
            converted_pdf = file_converter.convert_to_pdf(temp_input_path, temp_pdf_path)
            if not converted_pdf:
                raise HTTPException(
                    status_code=500,
                    detail=f"檔案格式轉換失敗：無法將 {file_ext} 轉換為PDF"
                )
            logger.info(f"格式轉換成功: {converted_pdf}")
        else:
            # 如果已經是PDF，直接使用
            temp_pdf_path = temp_input_path

        # 初始化PDF處理器
        pdf_processor = PDFProcessor(enable_vision_analysis=enable_vision)

        # 處理PDF文件
        chunks = pdf_processor.process_pdf(
            pdf_path=temp_pdf_path,
            output_path="temp_processed_chunks.jsonl"
        )

        if not chunks:
            raise HTTPException(status_code=400, detail="PDF處理失敗，未能提取到任何內容")

        # 統計圖片數量
        images_count = len([c for c in chunks if hasattr(c, 'has_images') and c.has_images])

        # 初始化RAG系統
        target_collection = collection_name or f"pdf_{int(time.time())}"
        rag_system_temp = TeachingRAGSystem()
        rag_system_temp.collection_name = target_collection
        rag_system_temp.chunks = chunks

        # 創建或更新向量嵌入
        if force_recreate:
            logger.info("強制重新創建向量嵌入...")
            rag_system_temp.force_recreate_embeddings()
        else:
            logger.info("創建向量嵌入...")
            rag_system_temp.create_embeddings()

        # 更新全域RAG系統（如果使用預設集合名稱）
        global rag_system
        if target_collection == rag_system.collection_name:
            rag_system.chunks = chunks
            logger.info("已更新全域RAG系統")

        processing_time = time.time() - start_time

        # 清理臨時文件
        try:
            # 清理原始上傳文件
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            # 清理轉換後的PDF（如果不同於原始文件）
            if temp_pdf_path != temp_input_path and os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
            # 清理處理過程中的臨時文件
            if os.path.exists("temp_processed_chunks.jsonl"):
                os.unlink("temp_processed_chunks.jsonl")
        except Exception as e:
            errors.append(f"清理臨時文件失敗: {str(e)}")

        logger.info(f"文件處理完成，共處理 {len(chunks)} 個段落，耗時 {processing_time:.2f} 秒")

        return ProcessPDFResponse(
            success=True,
            message=f"成功處理文件 '{file.filename}' ({file_ext} -> PDF)",
            chunks_processed=len(chunks),
            images_extracted=images_count,
            collection_name=target_collection,
            processing_time=processing_time,
            errors=errors
        )

    except HTTPException:
        # 重新拋出HTTP異常
        raise
    except Exception as e:
        logger.error(f"文件處理過程中發生錯誤: {e}")

        # 清理臨時文件
        try:
            if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            if 'temp_pdf_path' in locals() and os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
            if os.path.exists("temp_processed_chunks.jsonl"):
                os.unlink("temp_processed_chunks.jsonl")
        except:
            pass

        return ProcessPDFResponse(
            success=False,
            message=f"文件處理失敗: {str(e)}",
            chunks_processed=0,
            images_extracted=0,
            collection_name="",
            processing_time=time.time() - start_time,
            errors=[str(e)]
        )


@app.post("/process-pdf", response_model=ProcessPDFResponse)
async def process_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    collection_name: Optional[str] = Query(None, description="自定義集合名稱，如不提供則使用預設"),
    enable_vision: bool = Query(True, description="是否啟用視覺分析"),
    force_recreate: bool = Query(False, description="是否強制重新創建集合")
):
    """
    處理上傳的PDF文件並自動embedding到Qdrant（向後兼容端點）

    - **file**: 要處理的PDF文件
    - **collection_name**: 可選的自定義集合名稱
    - **enable_vision**: 是否啟用GPT-4o視覺分析
    - **force_recreate**: 是否強制重新創建向量集合
    """
    # 檢查文件類型
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支援PDF文件格式")

    # 直接調用新的多格式處理端點
    return await process_file(file, collection_name, enable_vision, force_recreate)


@app.get("/collections", response_model=List[str])
async def list_collections():
    """獲取所有可用的Qdrant集合列表"""
    try:
        if rag_system is None:
            raise HTTPException(status_code=500, detail="RAG系統未初始化")

        collections = rag_system.qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]

        return collection_names

    except Exception as e:
        logger.error(f"獲取集合列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取集合列表失敗: {str(e)}")

@app.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """刪除指定的Qdrant集合"""
    try:
        if rag_system is None:
            raise HTTPException(status_code=500, detail="RAG系統未初始化")

        # 檢查集合是否存在
        collections = rag_system.qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]

        if collection_name not in collection_names:
            raise HTTPException(status_code=404, detail=f"集合 '{collection_name}' 不存在")

        # 刪除集合
        rag_system.qdrant_client.delete_collection(collection_name)

        logger.info(f"已刪除集合: {collection_name}")
        return {"message": f"成功刪除集合 '{collection_name}'"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除集合失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除集合失敗: {str(e)}")


@app.get("/collections/{collection_name}/count", response_model=CollectionCountResponse)
async def check_collection_count(collection_name: str):
    """檢查指定集合的數量資訊"""
    try:
        if rag_system is None:
            raise HTTPException(status_code=500, detail="RAG系統未初始化")

        # 使用集合數量檢查器
        from check_collection_count import CollectionCountChecker
        checker = CollectionCountChecker(qdrant_url=rag_system.qdrant_url)

        result = checker.check_collection_count(collection_name)

        if result["success"]:
            collection_info = CollectionInfo(
                collection_name=result["collection_name"],
                vectors_count=result["vectors_count"],
                points_count=result["points_count"],
                status=result["status"],
                exists=result["exists"]
            )

            return CollectionCountResponse(
                success=True,
                collection_info=collection_info,
                last_activity=result.get("last_activity")
            )
        else:
            return CollectionCountResponse(
                success=False,
                error_message=result.get("error_message", "未知錯誤"),
                last_activity=result.get("last_activity")
            )

    except Exception as e:
        logger.error(f"檢查集合數量失敗: {e}")
        return CollectionCountResponse(
            success=False,
            error_message=f"檢查集合數量失敗: {str(e)}",
            last_activity=time.time()
        )


@app.get("/collections/count/all")
async def check_all_collections_count():
    """檢查所有集合的數量資訊"""
    try:
        if rag_system is None:
            raise HTTPException(status_code=500, detail="RAG系統未初始化")

        # 使用集合數量檢查器
        from check_collection_count import CollectionCountChecker
        checker = CollectionCountChecker(qdrant_url=rag_system.qdrant_url)

        result = checker.check_all_collections()

        return {
            "success": result["success"],
            "total_collections": result.get("total_collections", 0),
            "summary": result.get("summary", {}),
            "collections": result.get("collections", []),
            "error_message": result.get("error_message"),
            "last_activity": result.get("last_activity", time.time())
        }

    except Exception as e:
        logger.error(f"檢查所有集合數量失敗: {e}")
        return {
            "success": False,
            "error_message": f"檢查所有集合數量失敗: {str(e)}",
            "total_collections": 0,
            "collections": [],
            "last_activity": time.time()
        }


@app.get("/collections/{collection_name}/statistics")
async def get_collection_statistics(collection_name: str):
    """獲取指定集合的詳細統計資訊"""
    try:
        if rag_system is None:
            raise HTTPException(status_code=500, detail="RAG系統未初始化")

        # 使用集合數量檢查器
        from check_collection_count import CollectionCountChecker
        checker = CollectionCountChecker(qdrant_url=rag_system.qdrant_url)

        result = checker.get_collection_statistics(collection_name)

        return result

    except Exception as e:
        logger.error(f"獲取集合統計失敗: {e}")
        return {
            "success": False,
            "collection_name": collection_name,
            "error_message": f"獲取集合統計失敗: {str(e)}",
            "last_activity": time.time()
        }

@app.post("/chat", response_model=ChatResponse)
async def chat_with_memory(request: ChatRequest):
    """
    帶有記憶功能的聊天API

    - **message**: 用戶訊息
    - **session_id**: 會話ID，如不提供則自動生成
    - **use_rag**: 是否使用RAG檢索相關內容
    - **top_k**: RAG檢索的文件數量
    """
    if rag_system is None:
        raise HTTPException(status_code=500, detail="RAG系統未初始化")

    try:
        # 生成或使用提供的session_id
        session_id = request.session_id or str(uuid.uuid4())

        # 獲取會話記憶
        messages = memory_manager.get_session(session_id)

        # 添加用戶訊息到記憶
        memory_manager.add_message(session_id, "user", request.message)

        # 準備回應內容
        response_content = ""
        sources = []
        rag_used = False

        # 如果啟用RAG，檢索相關內容
        if request.use_rag and rag_system.has_vector_data():
            try:
                # 檢索相關文件段落
                retrieval_results = rag_system.retrieve_relevant_chunks(
                    query=request.message,
                    top_k=request.top_k
                )

                if retrieval_results:
                    rag_used = True

                    # 準備RAG上下文
                    rag_context = "\n\n".join([
                        f"【{result.chunk.topic} - {result.chunk.sub_topic}】\n{result.chunk.content}"
                        for result in retrieval_results
                    ])

                    # 添加RAG上下文到對話
                    rag_message = f"""基於以下教材內容回答問題：

{rag_context}

用戶問題：{request.message}

請結合教材內容和之前的對話歷史來回答。"""

                    # 暫時添加RAG上下文（不保存到記憶中）
                    temp_messages = messages + [{"role": "user", "content": rag_message}]

                    # 準備來源資訊
                    for result in retrieval_results:
                        chunk = result.chunk
                        source_info = {
                            "page_num": chunk.page_num,
                            "topic": chunk.topic,
                            "sub_topic": chunk.sub_topic,
                            "content": chunk.content,
                            "content_type": chunk.content_type,
                            "keywords": chunk.keywords,
                            "similarity_score": result.similarity_score,
                            "relevance_reason": result.relevance_reason
                        }

                        # 處理圖片資訊
                        if hasattr(chunk, 'has_images') and chunk.has_images:
                            image_url = None
                            if hasattr(chunk, 'image_path') and chunk.image_path:
                                image_url = get_image_url(chunk.image_path)

                            source_info["image_info"] = ImageInfo(
                                has_images=True,
                                image_url=image_url,
                                image_analysis=getattr(chunk, 'image_analysis', ""),
                                technical_symbols=getattr(chunk, 'technical_symbols', [])
                            )
                        else:
                            source_info["image_info"] = ImageInfo(has_images=False)

                        sources.append(SourceInfo(**source_info))

                else:
                    # 沒有找到相關內容，使用普通對話
                    temp_messages = messages

            except Exception as e:
                logger.warning(f"RAG檢索失敗，使用普通對話: {e}")
                temp_messages = messages
        else:
            # 不使用RAG，直接對話
            temp_messages = messages

        # 調用OpenAI API生成回應
        from openai import OpenAI
        client = OpenAI(api_key=Config.OPENAI_API_KEY)

        completion = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=temp_messages,
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE
        )

        response_content = completion.choices[0].message.content

        # 添加助手回應到記憶
        memory_manager.add_message(session_id, "assistant", response_content)

        # 獲取會話統計
        session_summary = memory_manager.get_session_summary(session_id)

        logger.info(f"聊天回應完成 - 會話: {session_id}, RAG: {rag_used}")

        return ChatResponse(
            response=response_content,
            session_id=session_id,
            message_count=session_summary["message_count"],
            total_tokens=session_summary["total_tokens"],
            sources=sources,
            rag_used=rag_used
        )

    except Exception as e:
        logger.error(f"聊天處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"聊天處理失敗: {str(e)}")

@app.get("/sessions", response_model=List[str])
async def list_chat_sessions():
    """獲取所有聊天會話ID列表"""
    try:
        sessions = memory_manager.list_sessions()
        return sessions
    except Exception as e:
        logger.error(f"獲取會話列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取會話列表失敗: {str(e)}")

@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """獲取指定會話的詳細資訊"""
    try:
        summary = memory_manager.get_session_summary(session_id)

        return SessionInfo(
            session_id=session_id,
            exists=summary["exists"],
            message_count=summary.get("message_count", 0),
            total_tokens=summary.get("total_tokens", 0),
            last_activity=summary.get("last_activity")
        )
    except Exception as e:
        logger.error(f"獲取會話資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取會話資訊失敗: {str(e)}")

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """清除指定會話的記憶"""
    try:
        summary = memory_manager.get_session_summary(session_id)
        if not summary["exists"]:
            raise HTTPException(status_code=404, detail=f"會話 '{session_id}' 不存在")

        memory_manager.clear_session(session_id)
        logger.info(f"已清除會話記憶: {session_id}")

        return {"message": f"成功清除會話 '{session_id}' 的記憶"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除會話記憶失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清除會話記憶失敗: {str(e)}")

if __name__ == "__main__":
    # 開發模式運行
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info"
    )
