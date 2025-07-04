"""
RAG系統 - 基於處理後的PPT內容建立教學型chatbot
使用 Qdrant 向量資料庫和 OpenAI API
"""

import json
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import openai
from openai import OpenAI
from scipy.spatial.distance import cosine
from pdf_processor import DocumentChunk  # 使用統一的 DocumentChunk
from config import Config
import logging
import os
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Filter, FieldCondition
from meteor_utilities import MeteorUtilities

logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """檢索結果"""
    chunk: DocumentChunk
    similarity_score: float
    relevance_reason: str

class TeachingRAGSystem:
    """教學型RAG系統 - 使用 Qdrant 向量資料庫和 OpenAI API"""

    def __init__(self, openai_api_key: str = None, qdrant_url: str = None):
        """初始化RAG系統"""
        # 設置 OpenAI API - 優先使用傳入的 key，否則從配置讀取
        api_key = openai_api_key or Config.OPENAI_API_KEY
        if not api_key:
            raise ValueError("請設定 OPENAI_API_KEY 環境變數或在 .env 文件中配置")

        self.client = OpenAI(api_key=api_key)
        self.chunks: List[DocumentChunk] = []
        self.embedding_model = Config.OPENAI_EMBEDDING_MODEL

        # 設置 Qdrant 客戶端
        self.qdrant_url = qdrant_url or "http://ec2-13-112-118-36.ap-northeast-1.compute.amazonaws.com:6333"
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        self.collection_name = "steven_JH_pro_0704"

        # 初始化 MeteorUtilities
        self.meteor = MeteorUtilities()

        # 教學模式配置
        self.teaching_modes = {
            "qa": "問答模式 - 回答具體問題",
            "quiz": "測驗模式 - 生成測驗題目",
            "guide": "導讀模式 - 章節重點說明",
            "search": "搜尋模式 - 關鍵字查詢",
            "explain": "解釋模式 - 深度說明概念"
        }

    def load_processed_chunks(self, chunks_file: str):
        """載入處理過的文件段落"""
        from pdf_processor import PDFProcessor

        # 使用PDF處理器的載入方法，它能正確處理VisionDocumentChunk
        processor = PDFProcessor()
        self.chunks = processor.load_chunks(chunks_file)

        logger.info(f"載入了 {len(self.chunks)} 個文件段落")

    def should_load_local_chunks(self) -> bool:
        """
        檢查是否需要載入本地 chunks 檔案

        Returns:
            bool: 如果需要載入本地檔案返回 True，否則返回 False
        """
        try:
            # 檢查集合是否存在
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)

            if not collection_exists:
                logger.info(f"集合 {self.collection_name} 不存在，需要載入本地檔案")
                return True

            # 檢查集合是否有資料
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            existing_count = collection_info.vectors_count
            points_count = collection_info.points_count

            # 處理 vectors_count 可能為 None 的情況
            if existing_count is None:
                existing_count = points_count if points_count is not None else 0

            if existing_count > 0:
                logger.info(f"集合 {self.collection_name} 已存在且包含 {existing_count} 個向量，無需載入本地檔案")
                return False
            else:
                logger.info(f"集合 {self.collection_name} 存在但為空，需要載入本地檔案")
                return True

        except Exception as e:
            logger.warning(f"檢查集合狀態時發生錯誤: {e}，預設載入本地檔案")
            return True

    def has_vector_data(self) -> bool:
        """
        檢查 Qdrant 集合是否包含向量資料

        Returns:
            bool: 如果集合存在且包含資料返回 True，否則返回 False
        """
        try:
            # 檢查集合是否存在
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)

            if not collection_exists:
                return False

            # 檢查集合是否有資料
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            existing_count = collection_info.vectors_count
            points_count = collection_info.points_count

            # 處理 vectors_count 可能為 None 的情況
            if existing_count is None:
                existing_count = points_count if points_count is not None else 0

            return existing_count > 0

        except Exception as e:
            logger.warning(f"檢查向量資料時發生錯誤: {e}")
            return False

    def create_embeddings(self):
        """為所有文件段落創建向量嵌入並儲存到 Qdrant"""
        if not self.chunks:
            raise ValueError("請先載入文件段落")

        logger.info("正在檢查 Qdrant 集合...")

        # 檢查集合是否存在，如果不存在則創建
        try:
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)

            if collection_exists:
                # 檢查集合中是否已有向量
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                existing_count = collection_info.vectors_count
                points_count = collection_info.points_count

                # 處理 vectors_count 可能為 None 的情況（某些 Qdrant 版本）
                if existing_count is None:
                    # 使用 points_count 作為替代指標
                    existing_count = points_count if points_count is not None else 0
                    logger.info(f"集合 {self.collection_name} 的 vectors_count 為 None，使用 points_count: {existing_count}")

                if existing_count > 0:
                    logger.info(f"集合 {self.collection_name} 已存在且包含 {existing_count} 個向量")
                    # 檢查是否需要添加新的文件內容
                    if self._should_add_new_content(existing_count):
                        logger.info("檢測到新文件內容，將添加到現有集合中...")
                        self._generate_and_store_embeddings()
                    else:
                        logger.info("集合內容已是最新，跳過向量生成")
                    return  # 提前返回，避免重複執行
                else:
                    logger.info(f"集合 {self.collection_name} 存在但為空，將重新生成向量")
            else:
                logger.info(f"創建新的 Qdrant 集合: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=1536,  # text-embedding-3-small 的維度
                        distance=models.Distance.COSINE
                    )
                )

        except Exception as e:
            logger.error(f"Qdrant 集合操作失敗: {e}")
            raise

        # 如果到這裡，說明是新集合或空集合，需要生成向量
        self._generate_and_store_embeddings()

    def force_recreate_embeddings(self):
        """強制重新創建向量嵌入（清空集合並重新生成）"""
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
                    size=1536,  # text-embedding-3-small 的維度
                    distance=models.Distance.COSINE
                )
            )

            # 強制重新生成向量
            self._generate_and_store_embeddings()

        except Exception as e:
            logger.error(f"強制重新創建向量嵌入失敗: {e}")
            raise

    def _should_add_new_content(self, existing_count: int) -> bool:
        """
        檢查是否需要添加新的文件內容到現有集合

        Args:
            existing_count: 現有集合中的向量數量

        Returns:
            bool: 如果需要添加新內容返回 True，否則返回 False
        """
        try:
            # 檢查當前載入的 chunks 數量
            current_chunks_count = len(self.chunks)

            # 如果當前 chunks 數量大於現有向量數量，說明有新內容
            if current_chunks_count > existing_count:
                logger.info(f"檢測到新內容: 當前 {current_chunks_count} 個段落 > 現有 {existing_count} 個向量")
                return True

            # 如果數量相同，可以進一步檢查內容是否有變化
            # 這裡可以添加更精細的檢查邏輯，比如檢查文件修改時間或內容雜湊值
            if current_chunks_count == existing_count:
                logger.info(f"段落數量相同 ({current_chunks_count})，假設內容未變化")
                return False

            # 如果當前 chunks 數量小於現有向量數量，可能是文件被刪減了
            if current_chunks_count < existing_count:
                logger.info(f"當前段落數量 ({current_chunks_count}) 小於現有向量數量 ({existing_count})，建議重新創建集合")
                return False

            return False

        except Exception as e:
            logger.warning(f"檢查新內容時發生錯誤: {e}，預設添加新內容")
            return True

    def _generate_and_store_embeddings(self):
        """生成並儲存向量嵌入的內部方法"""
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

        try:
            # 獲取現有集合中的最大 ID，避免 ID 衝突
            max_existing_id = 0
            try:
                # 獲取現有點的最大 ID
                existing_points = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    limit=10000,  # 假設不會超過這個數量
                    with_payload=False,
                    with_vectors=False
                )
                if existing_points[0]:
                    existing_ids = [point.id for point in existing_points[0]]
                    max_existing_id = max(existing_ids) if existing_ids else 0
                    logger.info(f"現有集合中最大 ID: {max_existing_id}")
            except Exception as e:
                logger.warning(f"無法獲取現有 ID，將從 0 開始: {e}")
                max_existing_id = 0

            # 批量處理以提高效率
            batch_size = 50
            total_batches = (len(texts) - 1) // batch_size + 1

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_chunks = self.chunks[i:i + batch_size]
                batch_num = i // batch_size + 1

                logger.info(f"處理批次 {batch_num}/{total_batches} (共 {len(batch_texts)} 個文本)")

                # 使用 MeteorUtilities 生成向量
                batch_embeddings = []
                for text in batch_texts:
                    embedding = self.meteor.get_embedding(text)
                    batch_embeddings.append(embedding)

                # 準備 Qdrant 點數據 - 使用階層式 metadata 結構
                for j, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                    # 使用不會衝突的 ID：從最大現有 ID + 1 開始
                    point_id = max_existing_id + 1 + i + j

                    # 創建階層式 metadata 結構
                    hierarchical_payload = {
                        # 基本識別資訊
                        "chunk_uuid": getattr(chunk, 'chunk_uuid', f"chunk_{point_id}"),
                        "file_uuid": getattr(chunk, 'file_uuid', f"file_{chunk.page_num}"),
                        "md_uuid": getattr(chunk, 'md_uuid', f"md_{point_id}"),

                        # 文件結構資訊
                        "document": {
                            "page_num": chunk.page_num,
                            "content_type": chunk.content_type,
                            "difficulty_level": chunk.difficulty_level
                        },

                        # 主題分類階層
                        "taxonomy": {
                            "topic": chunk.topic,
                            "sub_topic": chunk.sub_topic,
                            "keywords": chunk.keywords if isinstance(chunk.keywords, list) else [chunk.keywords] if chunk.keywords else []
                        },

                        # 內容資訊
                        "content": {
                            "text": chunk.content,
                            "combined_text": batch_texts[j],
                            "length": len(chunk.content) if chunk.content else 0
                        },

                        # 位置資訊 (類似您截圖中的 loc 結構)
                        "loc": {
                            "start": {
                                "page": chunk.page_num,
                                "chunk_index": j
                            },
                            "end": {
                                "page": chunk.page_num,
                                "chunk_index": j
                            }
                        },

                        # 處理狀態
                        "status": "processed",
                        "created_date": "20250703",
                        "update_date": "20250703",

                        # 向後相容性 - 保留原有的平面結構
                        "page_num": chunk.page_num,
                        "topic": chunk.topic,
                        "sub_topic": chunk.sub_topic,
                        "content": chunk.content,
                        "content_type": chunk.content_type,
                        "keywords": chunk.keywords,
                        "difficulty_level": chunk.difficulty_level,
                        "chunk_id": chunk.chunk_id,
                        "combined_text": batch_texts[j]
                    }

                    # 如果是視覺增強的段落，添加圖片相關資訊
                    if hasattr(chunk, 'has_images'):
                        hierarchical_payload.update({
                            "has_images": getattr(chunk, 'has_images', False),
                            "image_analysis": getattr(chunk, 'image_analysis', ""),
                            "technical_symbols": getattr(chunk, 'technical_symbols', []),
                            "image_path": getattr(chunk, 'image_path', "")
                        })

                    point = models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=hierarchical_payload
                    )
                    points.append(point)

                logger.info(f"批次 {batch_num} 向量生成完成")

            # 將所有點插入到 Qdrant
            logger.info(f"正在將 {len(points)} 個向量插入到 Qdrant...")
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"向量嵌入完成，共 {len(points)} 個向量已儲存到 Qdrant")

        except Exception as e:
            logger.error(f"向量嵌入處理失敗: {e}")
            raise

    def retrieve_relevant_chunks_hierarchical(self, query: str, top_k: int = 5,
                                            filters: dict = None) -> List[RetrievalResult]:
        """
        檢索相關文件段落 - 使用階層式 metadata 查詢

        Args:
            query: 查詢文本
            top_k: 返回結果數量
            filters: 階層式過濾條件，例如:
                {
                    "taxonomy.topic": "圖面識別",
                    "document.difficulty_level": "初級",
                    "document.page_num": {"gte": 1, "lte": 10},
                    "status": "processed"
                }
        """
        try:
            # 使用 MeteorUtilities 生成查詢向量
            logger.info(f"正在為查詢生成向量: {query[:50]}...")
            query_embedding = self.meteor.get_embedding(query)

            # 準備階層式搜索過濾器
            search_filter = None
            if filters:
                conditions = []

                for key, value in filters.items():
                    if isinstance(value, dict):
                        # 範圍查詢 (例如: {"gte": 1, "lte": 10})
                        if "gte" in value or "lte" in value or "gt" in value or "lt" in value:
                            range_condition = {}
                            if "gte" in value:
                                range_condition["gte"] = value["gte"]
                            if "lte" in value:
                                range_condition["lte"] = value["lte"]
                            if "gt" in value:
                                range_condition["gt"] = value["gt"]
                            if "lt" in value:
                                range_condition["lt"] = value["lt"]

                            conditions.append(
                                FieldCondition(
                                    key=key,
                                    range=models.Range(**range_condition)
                                )
                            )
                    elif isinstance(value, list):
                        # 多值匹配
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=models.MatchAny(any=value)
                            )
                        )
                    else:
                        # 單值匹配
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                        )

                if conditions:
                    search_filter = Filter(must=conditions)

            # 在 Qdrant 中搜索
            logger.info(f"正在 Qdrant 中搜索相關文件段落 (階層式查詢)...")
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )

            # 轉換搜索結果
            results = []
            for result in search_results:
                payload = result.payload

                # 優先使用階層式結構，如果不存在則使用平面結構
                content_text = payload.get("content", {}).get("text") if isinstance(payload.get("content"), dict) else payload.get("content", "")
                page_num = payload.get("document", {}).get("page_num") if isinstance(payload.get("document"), dict) else payload.get("page_num", 0)
                topic = payload.get("taxonomy", {}).get("topic") if isinstance(payload.get("taxonomy"), dict) else payload.get("topic", "")
                sub_topic = payload.get("taxonomy", {}).get("sub_topic") if isinstance(payload.get("taxonomy"), dict) else payload.get("sub_topic", "")

                # 檢查是否有圖片資訊
                has_images = payload.get("has_images", False)

                if has_images:
                    # 使用 VisionDocumentChunk 來處理包含圖片的段落
                    from pdf_processor import VisionDocumentChunk
                    chunk = VisionDocumentChunk(
                        page_num=page_num,
                        topic=topic,
                        sub_topic=sub_topic,
                        content=content_text,
                        content_type=payload.get("document", {}).get("content_type") if isinstance(payload.get("document"), dict) else payload.get("content_type", ""),
                        keywords=payload.get("taxonomy", {}).get("keywords") if isinstance(payload.get("taxonomy"), dict) else payload.get("keywords", ""),
                        difficulty_level=payload.get("document", {}).get("difficulty_level") if isinstance(payload.get("document"), dict) else payload.get("difficulty_level", ""),
                        chunk_id=payload.get("chunk_uuid", payload.get("chunk_id", "")),
                        has_images=True,
                        image_analysis=payload.get("image_analysis", ""),
                        technical_symbols=payload.get("technical_symbols", []),
                        image_path=payload.get("image_path", "")
                    )
                else:
                    chunk = DocumentChunk(
                        page_num=page_num,
                        topic=topic,
                        sub_topic=sub_topic,
                        content=content_text,
                        content_type=payload.get("document", {}).get("content_type") if isinstance(payload.get("document"), dict) else payload.get("content_type", ""),
                        keywords=payload.get("taxonomy", {}).get("keywords") if isinstance(payload.get("taxonomy"), dict) else payload.get("keywords", ""),
                        difficulty_level=payload.get("document", {}).get("difficulty_level") if isinstance(payload.get("document"), dict) else payload.get("difficulty_level", ""),
                        chunk_id=payload.get("chunk_uuid", payload.get("chunk_id", ""))
                    )

                results.append(RetrievalResult(
                    chunk=chunk,
                    score=result.score,
                    metadata=payload  # 包含完整的階層式 metadata
                ))

            logger.info(f"檢索完成，找到 {len(results)} 個相關段落")
            return results

        except Exception as e:
            logger.error(f"檢索失敗: {e}")
            return []

    def retrieve_relevant_chunks(self, query: str, top_k: int = 5,
                                topic_filter: str = None) -> List[RetrievalResult]:
        """檢索相關文件段落 - 使用 Qdrant 向量搜索"""

        try:
            # 使用 MeteorUtilities 生成查詢向量
            logger.info(f"正在為查詢生成向量: {query[:50]}...")
            query_embedding = self.meteor.get_embedding(query)

            # 準備搜索過濾器
            search_filter = None
            if topic_filter:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="topic",
                            match=models.MatchValue(value=topic_filter)
                        )
                    ]
                )

            # 在 Qdrant 中搜索
            logger.info(f"正在 Qdrant 中搜索相關文件段落...")
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )

            # 轉換搜索結果
            results = []
            for result in search_results:
                # 從 payload 重建 DocumentChunk
                payload = result.payload

                # 檢查是否有圖片資訊
                has_images = payload.get("has_images", False)

                if has_images:
                    # 使用 VisionDocumentChunk 來處理包含圖片的段落
                    from pdf_processor import VisionDocumentChunk
                    chunk = VisionDocumentChunk(
                        page_num=payload["page_num"],
                        topic=payload["topic"],
                        sub_topic=payload["sub_topic"],
                        content=payload["content"],
                        content_type=payload["content_type"],
                        keywords=payload["keywords"],
                        difficulty_level=payload["difficulty_level"],
                        chunk_id=payload["chunk_id"],
                        has_images=True,
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

                # 解釋相關性
                relevance_reason = self._explain_relevance(query, chunk, result.score)

                retrieval_result = RetrievalResult(
                    chunk=chunk,
                    similarity_score=float(result.score),
                    relevance_reason=relevance_reason
                )
                results.append(retrieval_result)

            logger.info(f"找到 {len(results)} 個相關文件段落")
            return results

        except Exception as e:
            logger.error(f"Qdrant 搜索失敗: {e}")
            # 如果 Qdrant 搜索失敗，使用關鍵字匹配作為後備方案
            logger.info("使用關鍵字搜索作為後備方案")
            return self._fallback_keyword_search(query, top_k, topic_filter)

    def _fallback_keyword_search(self, query: str, top_k: int = 5,
                                topic_filter: str = None) -> List[RetrievalResult]:
        """後備關鍵字搜尋方法"""
        logger.info("使用關鍵字搜尋作為後備方案")

        query_lower = query.lower()
        results = []

        for chunk in self.chunks:
            if topic_filter and chunk.topic != topic_filter:
                continue

            score = 0.0
            reasons = []

            # 檢查標題匹配
            if query_lower in chunk.sub_topic.lower():
                score += 0.8
                reasons.append("標題匹配")

            # 檢查內容匹配
            if query_lower in chunk.content.lower():
                score += 0.6
                reasons.append("內容匹配")

            # 檢查關鍵字匹配
            if any(keyword.lower() in query_lower for keyword in chunk.keywords):
                score += 0.7
                reasons.append("關鍵字匹配")

            # 檢查主題匹配
            if query_lower in chunk.topic.lower():
                score += 0.5
                reasons.append("主題匹配")

            if score > 0:
                results.append(RetrievalResult(
                    chunk=chunk,
                    similarity_score=score,
                    relevance_reason="; ".join(reasons)
                ))

        # 按分數排序
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]

    def _explain_relevance(self, query: str, chunk: DocumentChunk, score: float) -> str:
        """解釋為什麼這個段落相關"""
        reasons = []
        
        query_lower = query.lower()
        content_lower = chunk.content.lower()

        # 檢查關鍵字匹配
        if any(keyword.lower() in query_lower for keyword in chunk.keywords):
            reasons.append("關鍵字匹配")
        
        # 檢查主題相關性
        if chunk.topic.lower() in query_lower:
            reasons.append("主題相關")
        
        # 檢查相似度分數
        if score > 0.8:
            reasons.append("高度相似")
        elif score > 0.6:
            reasons.append("中度相似")
        else:
            reasons.append("低度相似")
        
        return ", ".join(reasons) if reasons else "語意相關"

    def generate_teaching_response(self, query: str, mode: str = "qa", 
                                 topic_filter: str = None) -> Dict[str, Any]:
        """生成教學型回答"""
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
            response = self._generate_qa_response(query, relevant_chunks)
        elif mode == "quiz":
            response = self._generate_quiz_response(relevant_chunks)
        elif mode == "guide":
            response = self._generate_guide_response(relevant_chunks)
        elif mode == "explain":
            response = self._generate_explanation_response(query, relevant_chunks)
        else:
            response = self._generate_qa_response(query, relevant_chunks)
        
        # 添加來源資訊
        sources = []
        for result in relevant_chunks:
            source_info = {
                "page_num": result.chunk.page_num,
                "topic": result.chunk.topic,
                "sub_topic": result.chunk.sub_topic,
                "content_type": result.chunk.content_type,
                "keywords": result.chunk.keywords,
                "relevance": result.relevance_reason,
                "similarity_score": result.similarity_score
            }

            # 如果是視覺增強的段落，添加圖片相關資訊
            if hasattr(result.chunk, 'has_images') and result.chunk.has_images:
                source_info.update({
                    "has_images": True,
                    "technical_symbols": getattr(result.chunk, 'technical_symbols', []),
                    "image_analysis": getattr(result.chunk, 'image_analysis', ""),
                    "image_path": getattr(result.chunk, 'image_path', "")
                })
            else:
                source_info["has_images"] = False

            sources.append(source_info)
        
        response["sources"] = sources
        response["mode"] = mode
        
        return response

    def _generate_qa_response(self, query: str, chunks: List[RetrievalResult]) -> Dict[str, Any]:
        """生成問答模式回答"""
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

        return {
            "answer": self._call_llm(prompt),
            "context_used": context
        }

    def _generate_quiz_response(self, chunks: List[RetrievalResult]) -> Dict[str, Any]:
        """生成測驗模式內容"""
        # 選擇最相關的段落
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

        return {
            "answer": self._call_llm(prompt),
            "quiz_topic": main_chunk.topic,
            "quiz_subtopic": main_chunk.sub_topic
        }

    def _generate_guide_response(self, chunks: List[RetrievalResult]) -> Dict[str, Any]:
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

    def _generate_explanation_response(self, query: str, chunks: List[RetrievalResult]) -> Dict[str, Any]:
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

        return {
            "answer": self._call_llm(prompt),
            "explanation_depth": "detailed"
        }

    def _call_llm(self, prompt: str) -> str:
        """調用 OpenAI API 生成回答"""
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一位專業的品管教育訓練講師，請用繁體中文回答問題。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API 調用失敗: {e}")
            return f"抱歉，生成回答時發生錯誤。請檢查 OpenAI API 設定。錯誤: {str(e)}"

    def get_collection_info(self):
        """獲取 Qdrant 集合資訊"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            vectors_count = collection_info.vectors_count
            points_count = collection_info.points_count

            # 處理 vectors_count 可能為 None 的情況（某些 Qdrant 版本）
            if vectors_count is None:
                vectors_count = points_count if points_count is not None else 0

            return {
                "collection_name": self.collection_name,
                "vectors_count": vectors_count,
                "points_count": points_count,
                "status": collection_info.status,
                "config": collection_info.config
            }
        except Exception as e:
            logger.error(f"獲取集合資訊失敗: {e}")
            return None

if __name__ == "__main__":
    # 使用範例
    rag_system = TeachingRAGSystem()
    
    # 載入處理過的文件段落
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
