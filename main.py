"""
FastAPI 服務器 - 提供 RAG 查詢 API
支援 Qdrant 知識庫檢索和圖片 URL 回傳
"""

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
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
import pandas as pd
import zipfile
import io


from src.core.langchain_rag_system import LangChainParentChildRAG
from config.config import Config
from src.processors.pdf_processor import PDFProcessor
from src.processors.file_converter import FileConverter

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全域變數
rag_system = None
memory_manager = None

# 圖片目錄路徑
IMAGES_DIR = "outputs/images/zerox_output"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時初始化
    global rag_system, memory_manager
    try:
        logger.info("正在初始化 LangChain Parent-Child RAG 系統...")
        rag_system = LangChainParentChildRAG(Config.QDRANT_COLLECTION_NAME)

        logger.info("LANGCHAIN RAG 系統初始化完成")
        logger.info(f"  系統類型: {rag_system.get_system_info()['system_type']}")
        if hasattr(rag_system, 'child_collection_name'):
            logger.info(f"  子段落集合: {rag_system.child_collection_name}")
            logger.info(f"  父段落集合: {rag_system.parent_collection_name}")

        # 初始化記憶管理器
        memory_manager = MemoryManager()
        logger.info("記憶管理器初始化完成")

        # 檢查圖片目錄
        if os.path.exists(IMAGES_DIR):
            logger.info(f"圖片目錄存在: {IMAGES_DIR}/ - 將通過 /images/{{filename}} 端點提供")
        else:
            logger.warning(f"{IMAGES_DIR} 目錄不存在")

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

class TestFolderRequest(BaseModel):
    """資料夾測試請求模型"""
    folder_name: str
    num_images_per_category: int = 1

class TestResult(BaseModel):
    """測試結果模型"""
    image_name: str
    category: str
    question: str
    rag_answer: str
    evaluation: Dict[str, Any]
    cost_info: Dict[str, float]

class TestResponse(BaseModel):
    """測試回應模型"""
    test_id: str
    total_tests: int
    results: List[TestResult]
    summary: Dict[str, Any]
    html_report_url: str

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

    # 從配置文件讀取 API 基礎 URL
    api_base_url = f"{Config.API_BASE_URL}/api/v1/JH"

    # 檔案名稱需要 URL 編碼（因為包含中文）
    from urllib.parse import quote
    encoded_filename = quote(filename)

    # 生成後端 API URL
    image_url = f"{api_base_url}/images/{encoded_filename}"

    return image_url

def format_answer_with_images(answer: str) -> str:
    """將回答中的圖片 URL 轉換為實際的圖片顯示"""
    import re

    # 先處理 "📷 相關圖片：" 部分的編號URL
    if "📷 相關圖片" in answer:
        # 收集編號的圖片URL
        numbered_url_pattern = r'\d+\.\s*(https?://[^\s]+\.(?:png|jpg|jpeg|gif|bmp))'
        urls = re.findall(numbered_url_pattern, answer)

        if urls:
            # 移除整個編號URL行
            answer = re.sub(r'\d+\.\s*https?://[^\s]+\.(?:png|jpg|jpeg|gif|bmp)', '', answer)

            # 創建並排的圖片容器 - 適中大小，確保完整顯示
            images_html = '<div style="display: flex; flex-direction: row; flex-wrap: wrap; gap: 20px; margin: 20px 0; justify-content: center; align-items: flex-start;">'
            for url in urls:
                images_html += f'''
                <div style="flex: 1; max-width: 400px; min-width: 300px; text-align: center;">
                    <img src="{url}" alt="相關圖片"
                         style="width: 100%; max-width: 400px; height: auto; border: 2px solid #2c3e50; border-radius: 8px;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; transition: transform 0.2s;
                                object-fit: contain;"
                         onclick="window.open('{url}', '_blank')"
                         onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 6px 20px rgba(52, 152, 219, 0.3)'"
                         onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)'">
                </div>'''
            images_html += '</div>'

            # 替換到原位置
            answer = answer.replace('📷 相關圖片：', f'📷 相關圖片：{images_html}')

            # 直接返回，不再處理其他URL（避免重複處理）
            return answer

    # 處理其他單獨的圖片URL（只有在沒有相關圖片區塊時才執行）
    url_pattern = r'https?://[^\s]+\.(?:png|jpg|jpeg|gif|bmp)'
    def replace_url_with_img(match):
        url = match.group(0)
        return f'<br><img src="{url}" alt="相關圖片" style="width: 100%; max-width: 600px; height: auto; margin: 15px 0; border: 2px solid #2c3e50; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; object-fit: contain;" onclick="window.open(\'{url}\', \'_blank\')">'

    # 替換剩餘的 URL 為圖片標籤
    formatted_answer = re.sub(url_pattern, replace_url_with_img, answer)

    return formatted_answer

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
        rag_message = None

        # 檢索相關內容 (預設啟用RAG)
        # 檢查 Qdrant 集合是否有資料，而不是檢查本地 chunks
        if rag_system.has_vector_data():
            try:
                # 檢索相關文件段落 - 增加檢索數量以確保有足夠圖片
                retrieval_results = rag_system.retrieve_relevant_chunks(
                    query=request.user_query,
                    top_k=10  # 增加檢索數量以確保有足夠圖片
                )

                if retrieval_results:
                    rag_used = True

                    # 準備RAG上下文
                    rag_context_parts = []
                    for result in retrieval_results:
                        context_part = f"【{result.parent_chunk.topic}】\n{result.parent_chunk.content}"

                        # 添加相關圖片
                        if result.parent_chunk.has_images and result.parent_chunk.image_paths:
                            current_image_urls = []
                            for image_path in result.parent_chunk.image_paths:
                                # 使用統一的 URL 生成函數
                                image_url = get_image_url(image_path)
                                if image_url:
                                    current_image_urls.append(image_url)
                                    # 添加到全局圖片URL列表（最多3張）
                                    if image_url not in image_urls and len(image_urls) < 3:
                                        image_urls.append(image_url)

                            if current_image_urls:
                                context_part += f"\n\n相關圖片：\n" + "\n".join(current_image_urls)

                        rag_context_parts.append(context_part)

                    rag_context = "\n\n".join(rag_context_parts)

                    # 添加RAG上下文到對話
                    rag_message = f"""基於以下教材內容回答問題：

{rag_context}

用戶問題：{request.user_query}

請結合教材內容和對話歷史，用清楚友善的方式回答問題。如果教材中有相關圖片，請在回答中提及。"""

                    # 收集圖片 URL (已在上面的循環中處理)

            except Exception as e:
                logger.error(f"RAG檢索失敗: {e}")
                rag_used = False

        # 準備對話訊息
        temp_messages = messages.copy()
        if rag_used and rag_message:
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
@app.options("/images/{filename}")
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
        file_path = os.path.join(IMAGES_DIR, clean_filename)

        logger.info(f"清理後的檔案名稱: {clean_filename}")
        logger.info(f"完整檔案路徑: {file_path}")

        # 檢查檔案是否存在
        if not os.path.exists(file_path):
            # 列出IMAGES_DIR目錄中的相似檔案
            similar_files = []
            if os.path.exists(IMAGES_DIR):
                for f in os.listdir(IMAGES_DIR):
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

        # 創建FileResponse並添加CORS標頭
        response = FileResponse(
            file_path,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "public, max-age=3600"
            }
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提供圖片檔案時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")

@app.get("/debug/images")
async def debug_images():
    """調試圖片檔案端點"""
    try:
        if not os.path.exists(IMAGES_DIR):
            return {"error": f"{IMAGES_DIR}目錄不存在"}

        # 列出所有圖片檔案
        image_files = []
        for file in os.listdir(IMAGES_DIR):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(IMAGES_DIR, file)
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
        if os.path.exists(IMAGES_DIR):
            images_count = len([f for f in os.listdir(IMAGES_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))])

        # 檢查向量資料庫中的資料量
        chunks_loaded = 0
        if qdrant_connected and rag_system.has_vector_data():
            try:
                # 獲取子段落集合的資料量
                child_info = rag_system.qdrant_client.get_collection(rag_system.child_collection_name)
                chunks_loaded = child_info.vectors_count or child_info.points_count or 0
            except Exception as e:
                logger.warning(f"無法獲取向量資料量: {e}")
                chunks_loaded = 0

        return HealthResponse(
            status="healthy" if qdrant_connected else "degraded",
            qdrant_connected=qdrant_connected,
            chunks_loaded=chunks_loaded,
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

        # 使用 Parent-Child RAG 系統生成回答
        response = rag_system.generate_answer(
            query=request.question,
            top_k=10  # 增加檢索數量以確保有足夠圖片
        )

        # 收集最多三張圖片 URL
        image_urls = []
        seen_urls = set()
        for source in response.get("sources", []):
            if source.get("has_images", False) and source.get("image_paths"):
                for image_path in source["image_paths"]:
                    image_url = get_image_url(image_path)
                    if image_url and image_url not in seen_urls:
                        image_urls.append(image_url)
                        seen_urls.add(image_url)
                        if len(image_urls) >= 3:  # 最多收集3張圖片
                            break
            if len(image_urls) >= 3:  # 如果已經收集到3張圖片，停止搜索
                break

        # 準備回應，將圖片 URL 作為單獨字段返回
        answer = response["answer"]

        # 可選：仍然在文本中添加圖片 URL 以保持向後兼容
        if image_urls:
            answer += "\n\n📷 相關圖片："
            for i, url in enumerate(image_urls, 1):
                answer += f"\n{i}. {url}"

        # 生成唯一的 sessionId 和 chatMessageId
        session_id = f"session_{request.chatId}_{int(time.time())}"
        chat_message_id = str(uuid.uuid4())

        return FlowiseResponse(
            text=answer,  # 只返回純文字，不進行HTML轉換
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
        image_urls = []

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
                    rag_context_parts = []
                    for result in retrieval_results:
                        context_part = f"【{result.parent_chunk.topic}】\n{result.parent_chunk.content}"

                        # 添加相關圖片
                        if result.parent_chunk.has_images and result.parent_chunk.image_paths:
                            current_image_urls = []
                            for image_path in result.parent_chunk.image_paths:
                                # 使用統一的 URL 生成函數
                                image_url = get_image_url(image_path)
                                if image_url:
                                    current_image_urls.append(image_url)
                                    # 添加到全局圖片URL列表（最多3張）
                                    if image_url not in image_urls and len(image_urls) < 3:
                                        image_urls.append(image_url)

                            if current_image_urls:
                                context_part += f"\n\n相關圖片：\n" + "\n".join(current_image_urls)

                        rag_context_parts.append(context_part)

                    rag_context = "\n\n".join(rag_context_parts)

                    # 添加RAG上下文到對話
                    rag_message = f"""基於以下教材內容回答問題：

{rag_context}

用戶問題：{request.user_query}

請結合教材內容和對話歷史，用清楚友善的方式回答問題。如果教材中有相關圖片，請在回答中提及。"""

                    # 準備來源資訊
                    for result in retrieval_results:
                        # 使用父段落作為主要內容來源
                        parent_chunk = result.parent_chunk
                        child_chunk = result.child_chunk

                        # 安全地存取視覺相關屬性（從父段落）
                        has_images = hasattr(parent_chunk, 'has_images') and getattr(parent_chunk, 'has_images', False)
                        image_paths = getattr(parent_chunk, 'image_paths', []) if has_images else []
                        image_analyses = getattr(parent_chunk, 'image_analyses', []) if has_images else []

                        # 從子段落獲取技術符號（如果有的話）
                        technical_symbols = getattr(child_chunk, 'technical_symbols', []) if hasattr(child_chunk, 'technical_symbols') else []

                        # 調試日誌
                        logger.info(f"檢索結果調試 - 頁面範圍: {parent_chunk.page_range}, has_images: {has_images}, image_paths: {image_paths}")

                        # 處理圖片資訊
                        image_url = None
                        image_analysis = ""
                        if has_images and image_paths:
                            # 使用第一個圖片路徑
                            first_image_path = image_paths[0]
                            image_url = get_image_url(first_image_path) if first_image_path else None
                            # 使用第一個圖片分析
                            image_analysis = image_analyses[0] if image_analyses else ""

                        image_info = ImageInfo(
                            has_images=has_images,
                            image_url=image_url,
                            image_analysis=image_analysis,
                            technical_symbols=technical_symbols
                        )

                        sources.append(SourceInfo(
                            page_num=child_chunk.page_num,
                            topic=parent_chunk.topic,
                            sub_topic=child_chunk.sub_topic,
                            content=child_chunk.content[:200] + "..." if len(child_chunk.content) > 200 else child_chunk.content,
                            content_type=child_chunk.content_type,
                            keywords=child_chunk.keywords or [],
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

        # 注意：image_urls 已經在上面的檢索過程中收集了，這裡不需要重新定義
        # 如果上面沒有收集到圖片，再從 sources 中收集
        if not image_urls:
            for source in sources:
                if source.image_info.has_images and source.image_info.image_url:
                    if source.image_info.image_url not in image_urls and len(image_urls) < 3:
                        image_urls.append(source.image_info.image_url)

        # 在回答後面添加圖片 URL (保持與原始 /query 端點一致的格式)
        if image_urls:
            response_content += "\n\n📷 相關圖片："
            for i, url in enumerate(image_urls, 1):
                response_content += f"\n{i}. {url}"

        # 添加助手回應到記憶（保存原始文本）
        memory_manager.add_message(session_id, "assistant", response_content)

        # 生成回應ID
        message_id = str(uuid.uuid4())

        # 獲取會話統計
        session_summary = memory_manager.get_session_summary(session_id)

        logger.info(f"記憶對話完成 - 會話: {session_id}, RAG: {rag_used}, 訊息數: {session_summary['message_count']}")

        # 對於非串流模式，回傳簡化的 JSON 格式（只返回純文字，不進行HTML轉換）
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

        # 初始化 RAG 系統
        target_collection = collection_name or f"pdf_{int(time.time())}"
        rag_system_temp = LangChainParentChildRAG(target_collection)
        logger.info("使用 LangChain Parent-Child 策略處理段落...")
        result = rag_system_temp.add_documents_from_zerox(chunks)

        if not result["success"]:
            raise HTTPException(status_code=500, detail="Parent-Child 處理失敗")

        # 更新全域RAG系統（如果使用預設集合名稱）
        global rag_system
        if target_collection == rag_system.collection_name:
            # 重新初始化全域 RAG 系統以載入新數據
            rag_system = LangChainParentChildRAG(target_collection)
            logger.info("已更新全域 LangChain RAG 系統")

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

        logger.info(f"文件處理完成，原始段落: {len(chunks)}，父段落: {result['parent_chunks']}，子段落: {result['child_chunks']}，耗時 {processing_time:.2f} 秒")

        return ProcessPDFResponse(
            success=True,
            message=f"成功處理文件 '{file.filename}' ({file_ext} -> PDF) - Parent-Child策略",
            chunks_processed=result['child_chunks'],  # 報告子段落數量
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
        image_urls = []

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
                    rag_context_parts = []
                    for result in retrieval_results:
                        context_part = f"【{result.parent_chunk.topic}】\n{result.parent_chunk.content}"

                        # 添加相關圖片
                        if result.parent_chunk.has_images and result.parent_chunk.image_paths:
                            current_image_urls = []
                            for image_path in result.parent_chunk.image_paths:
                                # 使用統一的 URL 生成函數
                                image_url = get_image_url(image_path)
                                if image_url:
                                    current_image_urls.append(image_url)
                                    # 添加到全局圖片URL列表（最多3張）
                                    if image_url not in image_urls and len(image_urls) < 3:
                                        image_urls.append(image_url)

                            if current_image_urls:
                                context_part += f"\n\n相關圖片：\n" + "\n".join(current_image_urls)

                        rag_context_parts.append(context_part)

                    rag_context = "\n\n".join(rag_context_parts)

                    # 添加RAG上下文到對話
                    rag_message = f"""基於以下教材內容回答問題：

{rag_context}

用戶問題：{request.message}

請結合教材內容和之前的對話歷史來回答。"""

                    # 暫時添加RAG上下文（不保存到記憶中）
                    temp_messages = messages + [{"role": "user", "content": rag_message}]

                    # 準備來源資訊
                    for result in retrieval_results:
                        parent_chunk = result.parent_chunk
                        child_chunk = result.child_chunk

                        source_info = {
                            "page_num": child_chunk.page_num,
                            "page_range": parent_chunk.page_range,
                            "topic": parent_chunk.topic,
                            "sub_topic": child_chunk.sub_topic,
                            "content": child_chunk.content,
                            "content_type": child_chunk.content_type,
                            "keywords": child_chunk.keywords,
                            "similarity_score": result.similarity_score,
                            "relevance_reason": result.relevance_reason
                        }

                        # 處理圖片資訊（從父段落）
                        if hasattr(parent_chunk, 'has_images') and parent_chunk.has_images:
                            image_url = None
                            image_paths = getattr(parent_chunk, 'image_paths', [])
                            if image_paths:
                                # 使用第一個圖片路徑
                                image_url = get_image_url(image_paths[0])

                            image_analyses = getattr(parent_chunk, 'image_analyses', [])
                            image_analysis = image_analyses[0] if image_analyses else ""

                            source_info["image_info"] = ImageInfo(
                                has_images=True,
                                image_url=image_url,
                                image_analysis=image_analysis,
                                technical_symbols=getattr(child_chunk, 'technical_symbols', [])
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

# ==================== 測試處理函數 ====================

async def handle_excel_mode(tester, excel_file: UploadFile):
    """處理 Excel 模式：無圖片純問題測試"""
    try:
        # 讀取 Excel 文件
        excel_content = await excel_file.read()
        df = pd.read_excel(io.BytesIO(excel_content))

        # 檢查 Excel 格式
        if 'question' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Excel 文件必須包含 'question' 欄位"
            )

        results = []
        for _, row in df.iterrows():
            question = row['question']

            # 執行純問題測試（無圖片）
            result = await tester.run_question_only_test(question)
            results.append(result)

        return results

    except Exception as e:
        logger.error(f"Excel 模式處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Excel 處理失敗: {str(e)}")

async def handle_folder_mode(tester, folder_path: str, num_images_per_category: int):
    """處理資料夾模式：有圖片測試"""
    try:
        # 檢查資料夾是否存在
        folder_full_path = Path(folder_path)
        if not folder_full_path.exists():
            raise HTTPException(status_code=404, detail=f"資料夾不存在: {folder_path}")

        # 獲取圖片類別
        categories = tester.rag_test.get_image_categories(str(folder_full_path))
        if not categories:
            raise HTTPException(status_code=400, detail="資料夾中沒有找到圖片")

        # 構建選擇字典
        selection = {}
        for category in categories.keys():
            selection[category] = min(num_images_per_category, len(categories[category]))

        # 執行測試
        results = tester.run_selected_tests(categories, selection)
        return results

    except Exception as e:
        logger.error(f"資料夾模式處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"資料夾處理失敗: {str(e)}")

# ==================== 統一測試 API 端點 ====================

@app.post("/api/test", response_model=TestResponse)
async def unified_test(
    excel_file: Optional[UploadFile] = File(None),
    folder_path: Optional[str] = Form(None),
    num_images_per_category: int = Form(1)
):
    """
    統一測試 API - 自動判斷模式
    - 上傳 Excel: 無圖片模式（純問題測試）
    - 指定資料夾: 有圖片模式（圖片+問題生成+測試）
    """
    try:
        # 導入測試系統
        import sys
        sys.path.append('./test_RAG')
        from interactive_rag_test import InteractiveRAGTester

        # 初始化測試器
        tester = InteractiveRAGTester()

        # 判斷測試模式
        if excel_file:
            # Excel 模式：無圖片測試（純問題）
            logger.info("🔍 檢測到 Excel 文件，使用無圖片模式")
            results = await handle_excel_mode(tester, excel_file)
            test_mode = "excel_questions"

        elif folder_path:
            # 資料夾模式：有圖片測試
            logger.info("🔍 檢測到資料夾路徑，使用有圖片模式")
            results = await handle_folder_mode(tester, folder_path, num_images_per_category)
            test_mode = "folder_images"

        else:
            raise HTTPException(
                status_code=400,
                detail="請提供 Excel 文件或資料夾路徑"
            )

        # 生成測試 ID 和時間戳
        test_id = f"{test_mode}_test_{int(time.time())}"
        timestamp = time.strftime('%Y%m%d_%H%M%S')

        # 生成 HTML 報告
        html_content = tester.generate_html_report_with_images(results, timestamp)
        html_filename = f"results/api_test_{timestamp}.html"

        # 確保 results 目錄存在
        Path("results").mkdir(exist_ok=True)

        # 保存 HTML 報告
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 計算統計資訊
        total_tests = len(results)

        # 安全地計算平均分數
        valid_scores = [r.get('overall_score', 0.0) for r in results if isinstance(r.get('overall_score'), (int, float))]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        # 安全地計算總成本
        total_cost = 0.0
        for r in results:
            cost_info = r.get('cost_info', {})
            if isinstance(cost_info, dict):
                total_cost += cost_info.get('total_cost', 0.0)

        # 轉換結果格式
        test_results = []
        for result in results:
            # 安全地獲取結果字段，提供預設值
            test_results.append(TestResult(
                image_name=result.get('image_name', 'unknown'),
                category=result.get('category', 'unknown'),
                question=result.get('question', ''),
                rag_answer=result.get('rag_answer', ''),
                evaluation={
                    'technical_accuracy': result.get('technical_accuracy', 0.0),
                    'completeness': result.get('completeness', 0.0),
                    'clarity': result.get('clarity', 0.0),
                    'image_reference': result.get('image_reference', 0.0),
                    'overall_score': result.get('overall_score', 0.0)
                },
                cost_info=result.get('cost_info', {})
            ))

        return TestResponse(
            test_id=test_id,
            total_tests=total_tests,
            results=test_results,
            summary={
                'average_score': avg_score,
                'total_cost': total_cost,
                'categories_tested': list(selection.keys()),
                'images_per_category': selection
            },
            html_report_url=f"/api/v1/JH/{html_filename}"
        )

    except Exception as e:
        logger.error(f"測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"測試失敗: {str(e)}")

if __name__ == "__main__":
    # 開發模式運行
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info"
    )
