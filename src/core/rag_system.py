"""
RAG系統 - 使用 LangChain 框架重構
基於處理後的PPT內容建立教學型chatbot
使用 Qdrant 向量資料庫和 OpenAI API
"""

import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import logging
import os

# LangChain imports
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.schema import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

# Qdrant imports
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Filter, FieldCondition

# Local imports
from src.processors.pdf_processor import DocumentChunk
from config.config import Config
from src.core.meteor_utilities import MeteorUtilities

logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """檢索結果 - 保持與原系統相容"""
    chunk: DocumentChunk
    similarity_score: float
    relevance_reason: str

class QdrantRetriever(BaseRetriever):
    """自定義 Qdrant 檢索器，保持與原系統的相容性"""

    # 明確聲明 Pydantic 欄位
    qdrant_client: QdrantClient
    collection_name: str
    embeddings: OpenAIEmbeddings
    chunks: List[DocumentChunk]
    meteor: MeteorUtilities

    def __init__(self, qdrant_client: QdrantClient, collection_name: str,
                 embeddings: OpenAIEmbeddings, chunks: List[DocumentChunk]):
        super().__init__(
            qdrant_client=qdrant_client,
            collection_name=collection_name,
            embeddings=embeddings,
            chunks=chunks,
            meteor=MeteorUtilities()
        )
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """檢索相關文件"""
        try:
            # 使用 MeteorUtilities 生成查詢向量
            query_embedding = self.meteor.get_embedding(query)
            
            # 在 Qdrant 中搜索
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=Config.DEFAULT_TOP_K,
                with_payload=True,
                with_vectors=False
            )
            
            documents = []
            for result in search_results:
                payload = result.payload
                
                # 重建 DocumentChunk - 根據是否有圖片使用不同的類別
                if payload.get("has_images", False):
                    from src.processors.pdf_processor import VisionDocumentChunk
                    chunk = VisionDocumentChunk(
                        page_num=payload["page_num"],
                        topic=payload["topic"],
                        sub_topic=payload["sub_topic"],
                        content=payload["content"],
                        content_type=payload["content_type"],
                        keywords=payload["keywords"],
                        difficulty_level=payload["difficulty_level"],
                        chunk_id=payload["chunk_id"],
                        has_images=payload["has_images"],
                        image_analysis=payload.get("image_analysis", ""),
                        technical_symbols=payload.get("technical_symbols", []),
                        image_path=payload.get("image_path", "")
                    )
                else:
                    chunk = DocumentChunk(
                        page_num=payload["page_num"],
                        topic=payload["topic"],
                        sub_topic=payload["sub_topic"],
                        content=payload["content"],
                        content_type=payload["content_type"],
                        keywords=payload["keywords"],
                        difficulty_level=payload["difficulty_level"],
                        chunk_id=payload["chunk_id"]
                    )
                
                # 創建 LangChain Document
                doc = Document(
                    page_content=f"{chunk.topic} - {chunk.sub_topic}\n{chunk.content}",
                    metadata={
                        "chunk": chunk,
                        "similarity_score": float(result.score),
                        "page_num": chunk.page_num,
                        "topic": chunk.topic,
                        "sub_topic": chunk.sub_topic,
                        "content_type": chunk.content_type,
                        "difficulty_level": chunk.difficulty_level,
                        "has_images": getattr(chunk, 'has_images', False),
                        "image_path": getattr(chunk, 'image_path', ''),
                        "image_description": getattr(chunk, 'image_description', '')
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"檢索失敗: {e}")
            return []

class TeachingRAGSystemLangChain:
    """教學型RAG系統 - 使用 LangChain 框架"""

    def __init__(self, openai_api_key: str = None, qdrant_url: str = None):
        """初始化RAG系統"""
        # 設置 OpenAI API
        api_key = openai_api_key or Config.OPENAI_API_KEY
        if not api_key:
            raise ValueError("請設定 OPENAI_API_KEY 環境變數或在 .env 文件中配置")

        # 初始化 LangChain 組件
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=Config.OPENAI_MODEL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
            verbose=Config.LANGCHAIN_VERBOSE
        )
        
        self.embeddings = OpenAIEmbeddings(
            api_key=api_key,
            model=Config.OPENAI_EMBEDDING_MODEL
        )
        
        # 設置 Qdrant 客戶端
        self.qdrant_url = qdrant_url or Config.QDRANT_URL
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        self.collection_name = Config.QDRANT_COLLECTION_NAME
        
        # 初始化其他組件
        self.chunks: List[DocumentChunk] = []
        self.meteor = MeteorUtilities()
        self.retriever = None
        self.qa_chain = None
        self.memory = ConversationBufferWindowMemory(
            k=Config.MEMORY_WINDOW_SIZE,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # 教學模式配置
        self.teaching_modes = {
            "qa": "問答模式 - 回答具體問題",
            "quiz": "測驗模式 - 生成測驗題目", 
            "guide": "導讀模式 - 章節重點說明",
            "search": "搜尋模式 - 關鍵字查詢",
            "explain": "解釋模式 - 深度說明概念"
        }
        
        logger.info("LangChain RAG 系統初始化完成")

    def load_processed_chunks(self, file_path: str):
        """載入處理過的文件段落"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    chunk_data = json.loads(line.strip())
                    
                    # 檢查是否有圖片資訊
                    if chunk_data.get("has_images", False):
                        chunk = DocumentChunk(
                            page_num=chunk_data["page_num"],
                            topic=chunk_data["topic"],
                            sub_topic=chunk_data["sub_topic"],
                            content=chunk_data["content"],
                            content_type=chunk_data["content_type"],
                            keywords=chunk_data["keywords"],
                            difficulty_level=chunk_data["difficulty_level"],
                            chunk_id=chunk_data["chunk_id"],
                            has_images=chunk_data["has_images"],
                            image_path=chunk_data.get("image_path", ""),
                            image_description=chunk_data.get("image_description", "")
                        )
                    else:
                        chunk = DocumentChunk(
                            page_num=chunk_data["page_num"],
                            topic=chunk_data["topic"],
                            sub_topic=chunk_data["sub_topic"],
                            content=chunk_data["content"],
                            content_type=chunk_data["content_type"],
                            keywords=chunk_data["keywords"],
                            difficulty_level=chunk_data["difficulty_level"],
                            chunk_id=chunk_data["chunk_id"]
                        )
                    
                    self.chunks.append(chunk)
            
            logger.info(f"成功載入 {len(self.chunks)} 個文件段落")
            
        except Exception as e:
            logger.error(f"載入文件段落失敗: {e}")
            raise

    def has_vector_data(self) -> bool:
        """檢查 Qdrant 集合是否包含向量資料"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)
            
            if not collection_exists:
                return False
            
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            existing_count = collection_info.vectors_count
            points_count = collection_info.points_count
            
            if existing_count is None:
                existing_count = points_count if points_count is not None else 0
            
            return existing_count > 0
            
        except Exception as e:
            logger.warning(f"檢查向量資料時發生錯誤: {e}")
            return False

    def should_load_local_chunks(self) -> bool:
        """判斷是否需要載入本地文件段落"""
        return not self.has_vector_data()

    def setup_retriever(self):
        """設置檢索器和QA鏈"""
        # 如果沒有本地 chunks，嘗試從 Qdrant 載入一些樣本來初始化檢索器
        if not self.chunks:
            logger.info("沒有本地文件段落，嘗試從 Qdrant 載入樣本數據...")
            self._load_sample_chunks_from_qdrant()

        # 創建自定義檢索器
        self.retriever = QdrantRetriever(
            qdrant_client=self.qdrant_client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
            chunks=self.chunks
        )
        
        # 設置提示詞模板
        qa_prompt = PromptTemplate(
            template="""你是一位專業的品管教育訓練講師，請根據以下教材內容回答學員問題。

教材內容：
{context}

學員問題：{question}

請用清楚、自然的方式回答問題，提供相關的重要概念說明，如果有範例或圖面說明也請一併提供。

回答：""",
            input_variables=["context", "question"]
        )
        
        # 創建QA鏈
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type=Config.CHAIN_TYPE,
            retriever=self.retriever,
            return_source_documents=Config.RETURN_SOURCE_DOCUMENTS,
            chain_type_kwargs={"prompt": qa_prompt},
            verbose=Config.LANGCHAIN_VERBOSE
        )
        
        logger.info("檢索器和QA鏈設置完成")

    def _load_sample_chunks_from_qdrant(self):
        """從 Qdrant 載入樣本數據來初始化檢索器"""
        try:
            # 檢查集合是否存在
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)

            if not collection_exists:
                logger.warning(f"Qdrant 集合 {self.collection_name} 不存在")
                return

            # 獲取一些樣本點來了解數據結構
            points = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10,  # 載入10個樣本就足夠了
                with_payload=True,
                with_vectors=False
            )

            sample_chunks = []
            for point in points[0]:
                payload = point.payload

                # 重建 DocumentChunk - 根據是否有圖片使用不同的類別
                if payload.get("has_images", False):
                    from src.processors.pdf_processor import VisionDocumentChunk
                    chunk = VisionDocumentChunk(
                        page_num=payload.get("page_num", 0),
                        topic=payload.get("topic", ""),
                        sub_topic=payload.get("sub_topic", ""),
                        content=payload.get("content", ""),
                        content_type=payload.get("content_type", ""),
                        keywords=payload.get("keywords", []),
                        difficulty_level=payload.get("difficulty_level", ""),
                        chunk_id=payload.get("chunk_id", ""),
                        has_images=payload.get("has_images", False),
                        image_analysis=payload.get("image_analysis", ""),
                        technical_symbols=payload.get("technical_symbols", []),
                        image_path=payload.get("image_path", "")
                    )
                else:
                    chunk = DocumentChunk(
                        page_num=payload.get("page_num", 0),
                        topic=payload.get("topic", ""),
                        sub_topic=payload.get("sub_topic", ""),
                        content=payload.get("content", ""),
                        content_type=payload.get("content_type", ""),
                        keywords=payload.get("keywords", []),
                        difficulty_level=payload.get("difficulty_level", ""),
                        chunk_id=payload.get("chunk_id", "")
                    )

                sample_chunks.append(chunk)

            self.chunks = sample_chunks
            logger.info(f"從 Qdrant 載入了 {len(sample_chunks)} 個樣本文件段落")

        except Exception as e:
            logger.error(f"從 Qdrant 載入樣本數據失敗: {e}")
            # 創建一個空的 chunk 作為後備
            self.chunks = []

    def create_embeddings(self):
        """創建向量嵌入 - 保持與原系統相容的接口"""
        if not self.has_vector_data():
            logger.info("Qdrant 集合為空或不存在，需要生成向量嵌入")
            self._generate_and_store_embeddings()
        else:
            logger.info("Qdrant 集合已存在且包含資料，跳過向量生成")

        # 設置檢索器
        self.setup_retriever()

    def _generate_and_store_embeddings(self):
        """生成並儲存向量嵌入"""
        if not self.chunks:
            raise ValueError("請先載入文件段落")

        try:
            # 檢查集合是否存在，不存在則創建
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)

            if not collection_exists:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=Config.EMBEDDING_DIMENSION,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"創建新集合: {self.collection_name}")

            # 準備文字內容進行向量化
            texts = []
            points = []

            for i, chunk in enumerate(self.chunks):
                # 組合多個欄位以提高檢索效果
                combined_text = f"{chunk.topic} {chunk.sub_topic} {chunk.content}"
                if chunk.keywords:
                    combined_text += f" 關鍵字: {' '.join(chunk.keywords)}"
                texts.append(combined_text)

            # 使用 MeteorUtilities 生成嵌入向量
            logger.info("正在使用 MeteorUtilities 生成向量嵌入...")
            embeddings_list = []

            for i, text in enumerate(texts):
                embedding = self.meteor.get_embedding(text)
                embeddings_list.append(embedding)

                if (i + 1) % 10 == 0:
                    logger.info(f"已生成 {i + 1}/{len(texts)} 個向量")

            # 準備 Qdrant points
            for i, (chunk, embedding) in enumerate(zip(self.chunks, embeddings_list)):
                payload = {
                    "page_num": chunk.page_num,
                    "topic": chunk.topic,
                    "sub_topic": chunk.sub_topic,
                    "content": chunk.content,
                    "content_type": chunk.content_type,
                    "keywords": chunk.keywords,
                    "difficulty_level": chunk.difficulty_level,
                    "chunk_id": chunk.chunk_id
                }

                # 添加圖片資訊（如果有）
                if hasattr(chunk, 'has_images') and chunk.has_images:
                    payload.update({
                        "has_images": chunk.has_images,
                        "image_path": getattr(chunk, 'image_path', ''),
                        "image_description": getattr(chunk, 'image_description', '')
                    })
                else:
                    payload["has_images"] = False

                point = models.PointStruct(
                    id=i,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)

            # 批量上傳到 Qdrant
            logger.info(f"正在上傳 {len(points)} 個向量到 Qdrant...")
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"向量嵌入生成完成，共 {len(points)} 個向量")

        except Exception as e:
            logger.error(f"生成向量嵌入失敗: {e}")
            raise

    def retrieve_relevant_chunks(self, query: str, top_k: int = 5,
                                topic_filter: str = None) -> List[RetrievalResult]:
        """檢索相關文件段落 - 保持與原系統相容的接口"""
        try:
            if not self.retriever:
                self.setup_retriever()

            # 使用 LangChain 檢索器
            documents = self.retriever.get_relevant_documents(query)

            # 轉換為原系統的 RetrievalResult 格式
            results = []
            for doc in documents[:top_k]:
                chunk = doc.metadata["chunk"]
                similarity_score = doc.metadata["similarity_score"]

                # 生成相關性解釋
                relevance_reason = self._explain_relevance(query, chunk, similarity_score)

                result = RetrievalResult(
                    chunk=chunk,
                    similarity_score=similarity_score,
                    relevance_reason=relevance_reason
                )
                results.append(result)

            # 應用主題過濾器（如果有）
            if topic_filter:
                results = [r for r in results if r.chunk.topic == topic_filter]

            logger.info(f"找到 {len(results)} 個相關文件段落")
            return results

        except Exception as e:
            logger.error(f"檢索失敗: {e}")
            return self._fallback_keyword_search(query, top_k, topic_filter)

    def _explain_relevance(self, query: str, chunk: DocumentChunk, score: float) -> str:
        """解釋相關性原因"""
        reasons = []
        query_lower = query.lower()

        if query_lower in chunk.sub_topic.lower():
            reasons.append("標題匹配")
        if query_lower in chunk.content.lower():
            reasons.append("內容匹配")
        if any(keyword.lower() in query_lower for keyword in chunk.keywords):
            reasons.append("關鍵字匹配")
        if query_lower in chunk.topic.lower():
            reasons.append("主題匹配")

        if not reasons:
            reasons.append(f"語義相似度: {score:.3f}")

        return "; ".join(reasons)

    def _fallback_keyword_search(self, query: str, top_k: int, topic_filter: str = None) -> List[RetrievalResult]:
        """關鍵字搜索作為後備方案"""
        logger.info("使用關鍵字搜索作為後備方案")
        results = []
        query_lower = query.lower()

        for chunk in self.chunks:
            if topic_filter and chunk.topic != topic_filter:
                continue

            score = 0.0
            reasons = []

            if query_lower in chunk.sub_topic.lower():
                score += 0.8
                reasons.append("標題匹配")

            if query_lower in chunk.content.lower():
                score += 0.6
                reasons.append("內容匹配")

            if any(keyword.lower() in query_lower for keyword in chunk.keywords):
                score += 0.7
                reasons.append("關鍵字匹配")

            if query_lower in chunk.topic.lower():
                score += 0.5
                reasons.append("主題匹配")

            if score > 0:
                results.append(RetrievalResult(
                    chunk=chunk,
                    similarity_score=score,
                    relevance_reason="; ".join(reasons)
                ))

        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]

    def generate_teaching_response(self, query: str, mode: str = "qa",
                                 topic_filter: str = None) -> Dict[str, Any]:
        """生成教學型回答 - 保持與原系統相容的接口"""
        # 檢索相關內容
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k=3, topic_filter=topic_filter)

        if not relevant_chunks:
            return {
                "answer": "抱歉，我在教材中找不到相關內容。請嘗試其他問題或關鍵字。",
                "mode": mode,
                "sources": []
            }

        # 根據模式生成不同類型的回答
        if mode == "qa":
            response = self._generate_qa_response_langchain(query, relevant_chunks)
        elif mode == "quiz":
            response = self._generate_quiz_response_langchain(relevant_chunks)
        elif mode == "guide":
            response = self._generate_guide_response_langchain(relevant_chunks)
        elif mode == "explain":
            response = self._generate_explanation_response_langchain(query, relevant_chunks)
        else:
            response = self._generate_qa_response_langchain(query, relevant_chunks)

        # 準備來源資訊並收集圖片 URL
        sources = []
        image_urls = []

        for result in relevant_chunks:
            chunk = result.chunk
            source_info = {
                "page_num": chunk.page_num,
                "topic": chunk.topic,
                "sub_topic": chunk.sub_topic,
                "content_type": chunk.content_type,
                "difficulty_level": chunk.difficulty_level,
                "similarity_score": result.similarity_score,
                "relevance_reason": result.relevance_reason,
                "has_images": getattr(chunk, 'has_images', False),
                "image_path": getattr(chunk, 'image_path', ''),
                "image_analysis": getattr(chunk, 'image_analysis', '')
            }
            sources.append(source_info)

            # 收集圖片 URL
            if source_info["has_images"] and source_info["image_path"]:
                image_url = self._get_image_url(source_info["image_path"])
                if image_url and image_url not in image_urls:
                    image_urls.append(image_url)

        # 在回答後面添加圖片 URL
        if image_urls:
            response["answer"] += "\n\n📷 相關圖片："
            for i, url in enumerate(image_urls, 1):
                response["answer"] += f"\n{i}. {url}"

        response["sources"] = sources
        response["mode"] = mode

        return response

    def _get_image_url(self, image_path: str) -> str:
        """生成圖片的完整 URL - 使用後端API路徑"""
        if not image_path:
            return None

        import os
        from urllib.parse import quote

        # 提取檔案名稱，處理可能的路徑分隔符問題
        filename = os.path.basename(image_path.replace('\\', '/'))

        # 後端 API 基礎 URL
        api_base_url = "https://uat.heph-ai.net/api/v1/JH"

        # 檔案名稱需要 URL 編碼（因為包含中文）
        encoded_filename = quote(filename)

        # 生成後端 API URL
        image_url = f"{api_base_url}/images/{encoded_filename}"

        return image_url

    def _generate_qa_response_langchain(self, query: str, chunks: List[RetrievalResult]) -> Dict[str, Any]:
        """使用 LangChain 生成問答模式回答"""
        try:
            if not self.qa_chain:
                self.setup_retriever()

            # 使用 LangChain QA 鏈
            result = self.qa_chain({"query": query})

            return {
                "answer": result["result"],
                "context_used": result.get("source_documents", [])
            }

        except Exception as e:
            logger.error(f"LangChain QA 生成失敗: {e}")
            # 降級到原始方法
            return self._generate_qa_response_fallback(query, chunks)

    def _generate_qa_response_fallback(self, query: str, chunks: List[RetrievalResult]) -> Dict[str, Any]:
        """降級的問答回答生成"""
        # 組合相關內容
        context_parts = []
        for result in chunks:
            chunk = result.chunk
            context_parts.append(f"【{chunk.topic} - {chunk.sub_topic}】\n{chunk.content}")

        context = "\n\n".join(context_parts)

        # 構建提示詞
        prompt = f"""你是一位專業的品管教育訓練講師，請根據以下教材內容回答學員問題。

教材內容：
{context}

學員問題：{query}

請用清楚、自然的方式回答問題，提供相關的重要概念說明，如果有範例或圖面說明也請一併提供。

回答："""

        # 直接調用 LLM
        response = self.llm.invoke(prompt)

        return {
            "answer": response.content,
            "context_used": context
        }

    def _generate_quiz_response_langchain(self, chunks: List[RetrievalResult]) -> Dict[str, Any]:
        """生成測驗模式內容"""
        main_chunk = chunks[0].chunk

        prompt = f"""基於以下教材內容，請生成3道測驗題目：

教材內容：
【{main_chunk.topic} - {main_chunk.sub_topic}】
{main_chunk.content}

請生成：
1. 1道選擇題（4個選項）
2. 1道是非題
3. 1道簡答題

每題都要包含正確答案和簡要解釋。

測驗題目："""

        response = self.llm.invoke(prompt)

        return {
            "answer": response.content,
            "quiz_topic": main_chunk.topic,
            "quiz_subtopic": main_chunk.sub_topic
        }

    def _generate_guide_response_langchain(self, chunks: List[RetrievalResult]) -> Dict[str, Any]:
        """生成導讀模式內容"""
        # 按主題組織內容
        topics = {}
        for result in chunks:
            topic = result.chunk.topic
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(result.chunk)

        guide_content = []
        for topic, topic_chunks in topics.items():
            guide_content.append(f"## {topic}")
            for chunk in topic_chunks:
                guide_content.append(f"### {chunk.sub_topic}")
                guide_content.append(chunk.content)
                if chunk.keywords:
                    guide_content.append(f"**關鍵字：** {', '.join(chunk.keywords)}")
                guide_content.append("")

        return {
            "answer": "\n".join(guide_content),
            "topics_covered": list(topics.keys())
        }

    def _generate_explanation_response_langchain(self, query: str, chunks: List[RetrievalResult]) -> Dict[str, Any]:
        """生成深度解釋模式內容"""
        context = "\n\n".join([f"【{r.chunk.topic}】{r.chunk.content}" for r in chunks])

        prompt = f"""請對以下概念進行深度解釋，包括定義、用途、注意事項等：

相關教材內容：
{context}

要解釋的概念：{query}

請提供：
1. 清楚的定義
2. 實際應用場景
3. 常見錯誤或注意事項
4. 相關概念的關聯性

詳細解釋："""

        response = self.llm.invoke(prompt)

        return {
            "answer": response.content,
            "explanation_depth": "detailed"
        }

    def chat_with_memory(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        """帶記憶的聊天功能"""
        try:
            # 檢索相關內容
            relevant_chunks = self.retrieve_relevant_chunks(query, top_k=3)

            if relevant_chunks:
                # 準備上下文
                context = "\n\n".join([
                    f"【{result.chunk.topic} - {result.chunk.sub_topic}】\n{result.chunk.content}"
                    for result in relevant_chunks
                ])

                # 創建帶記憶的對話鏈
                if not hasattr(self, 'conversation_chain') or self.conversation_chain is None:
                    self.conversation_chain = ConversationalRetrievalChain.from_llm(
                        llm=self.llm,
                        retriever=self.retriever,
                        memory=self.memory,
                        return_source_documents=True,
                        verbose=Config.LANGCHAIN_VERBOSE
                    )

                # 生成回答
                result = self.conversation_chain({"question": query})

                return {
                    "answer": result["answer"],
                    "sources": [doc.metadata for doc in result.get("source_documents", [])],
                    "session_id": session_id
                }
            else:
                # 沒有相關內容時的純對話
                response = self.llm.invoke(f"""你是一位專業的品管教育訓練講師助手。

用戶問題：{query}

請用友善、專業的方式回答。如果問題與品管教育訓練無關，請引導用戶提問相關問題。

回答：""")

                return {
                    "answer": response.content,
                    "sources": [],
                    "session_id": session_id
                }

        except Exception as e:
            logger.error(f"記憶聊天失敗: {e}")
            return {
                "answer": f"抱歉，處理您的問題時發生錯誤：{str(e)}",
                "sources": [],
                "session_id": session_id
            }

    def clear_memory(self):
        """清除記憶"""
        self.memory.clear()
        logger.info("記憶已清除")

    def get_memory_summary(self) -> Dict[str, Any]:
        """獲取記憶摘要"""
        try:
            messages = self.memory.chat_memory.messages
            return {
                "message_count": len(messages),
                "memory_buffer": str(self.memory.buffer) if hasattr(self.memory, 'buffer') else "",
                "last_messages": [msg.content for msg in messages[-4:]] if messages else []
            }
        except Exception as e:
            logger.error(f"獲取記憶摘要失敗: {e}")
            return {"message_count": 0, "memory_buffer": "", "last_messages": []}

    def force_recreate_embeddings(self):
        """強制重新創建向量嵌入"""
        if not self.chunks:
            raise ValueError("請先載入文件段落")

        logger.info(f"強制重新創建集合 {self.collection_name} 的向量嵌入...")

        try:
            # 刪除現有集合（如果存在）
            try:
                self.qdrant_client.delete_collection(self.collection_name)
                logger.info(f"已刪除現有集合: {self.collection_name}")
            except Exception:
                logger.info(f"集合 {self.collection_name} 不存在，將創建新集合")

            # 創建新集合
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=Config.EMBEDDING_DIMENSION,
                    distance=models.Distance.COSINE
                )
            )

            # 強制重新生成向量
            self._generate_and_store_embeddings()

            # 重新設置檢索器
            self.setup_retriever()

        except Exception as e:
            logger.error(f"強制重新創建向量嵌入失敗: {e}")
            raise

    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統資訊"""
        return {
            "framework": "LangChain",
            "llm_model": Config.OPENAI_MODEL,
            "embedding_model": Config.OPENAI_EMBEDDING_MODEL,
            "vector_store": "Qdrant",
            "collection_name": self.collection_name,
            "chunks_loaded": len(self.chunks),
            "has_vector_data": self.has_vector_data(),
            "memory_type": type(self.memory).__name__,
            "memory_window_size": Config.MEMORY_WINDOW_SIZE,
            "teaching_modes": list(self.teaching_modes.keys())
        }


# 為了保持向後相容性，創建一個別名
TeachingRAGSystem = TeachingRAGSystemLangChain


if __name__ == "__main__":
    # 使用範例
    rag_system = TeachingRAGSystemLangChain()

    # 載入處理過的文件段落
    if os.path.exists("processed_chunks.jsonl"):
        rag_system.load_processed_chunks("processed_chunks.jsonl")

        # 建立向量索引
        rag_system.create_embeddings()

        # 測試不同模式的查詢
        test_queries = [
            ("什麼是有效圖面？", "qa"),
            ("Φ符號代表什麼？", "explain"),
            ("零件圖", "guide"),
            ("測試我對圖面符號的理解", "quiz")
        ]

        for query, mode in test_queries:
            print(f"\n=== 查詢: {query} (模式: {mode}) ===")
            response = rag_system.generate_teaching_response(query, mode)
            print(f"回答: {response['answer'][:200]}...")
            print(f"來源數量: {len(response['sources'])}")

        # 測試記憶聊天
        print(f"\n=== 記憶聊天測試 ===")
        chat_response = rag_system.chat_with_memory("你好，我想學習圖面識別")
        print(f"聊天回答: {chat_response['answer'][:200]}...")

        # 系統資訊
        print(f"\n=== 系統資訊 ===")
        info = rag_system.get_system_info()
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        print("未找到 processed_chunks.jsonl 檔案")
