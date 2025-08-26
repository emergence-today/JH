"""
LangChain Parent-Child RAG系統
使用LangChain的ParentDocumentRetriever實現更優化的檢索
"""

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from langchain.retrievers import ParentDocumentRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.storage import InMemoryStore
from langchain_core.stores import BaseStore
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config.config import Config

logger = logging.getLogger(__name__)

@dataclass
class LangChainRetrievalResult:
    """LangChain檢索結果 - 兼容原有格式"""
    document: Document
    similarity_score: float
    relevance_reason: str
    parent_content: str
    child_content: str

    # 兼容原有格式的屬性
    @property
    def child_chunk(self):
        """兼容原有child_chunk屬性"""
        return type('ChildChunk', (), {
            'content': self.child_content,
            'topic': self.document.metadata.get('topic', ''),
            'sub_topic': self.document.metadata.get('sub_topic', ''),
            'page_num': self.document.metadata.get('page_num', 0),
            'keywords': self.document.metadata.get('keywords', []),
            'has_images': self.document.metadata.get('has_images', False),
            'image_path': self.document.metadata.get('image_path', ''),
            'content_type': self.document.metadata.get('content_type', '未指定'),
            'source_filename': self.document.metadata.get('source_filename', '')
        })()

    @property
    def parent_chunk(self):
        """兼容原有parent_chunk屬性"""
        return type('ParentChunk', (), {
            'content': self.parent_content,
            'topic': self.document.metadata.get('topic', ''),
            'page_range': (self.document.metadata.get('page_num', 0), self.document.metadata.get('page_num', 0)),
            'has_images': self.document.metadata.get('has_images', False),
            'image_paths': [self.document.metadata.get('image_path', '')] if self.document.metadata.get('image_path') else [],
            'content_type': self.document.metadata.get('content_type', '未指定'),
            'source_filename': self.document.metadata.get('source_filename', '')
        })()

class QdrantDocStore(BaseStore[str, str]):
    """Qdrant文檔存儲器，用於存儲父文檔"""
    
    def __init__(self, qdrant_client: QdrantClient, collection_name: str):
        self.qdrant_client = qdrant_client
        self.collection_name = f"{collection_name}_docstore"
        self._ensure_collection()
    
    def _ensure_collection(self):
        """確保集合存在"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                # 創建文檔存儲集合（不需要向量，只存儲文檔）
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1,  # 最小向量維度
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ 創建文檔存儲集合: {self.collection_name}")
        except Exception as e:
            logger.error(f"創建文檔存儲集合失敗: {e}")
    
    def mget(self, keys: List[str]) -> List[Optional[str]]:
        """批量獲取文檔"""
        try:
            results = []
            for key in keys:
                points = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter={
                        "must": [{"key": "doc_id", "match": {"value": key}}]
                    },
                    limit=1,
                    with_payload=True
                )[0]
                
                if points:
                    results.append(points[0].payload.get("content"))
                else:
                    results.append(None)
            return results
        except Exception as e:
            logger.error(f"批量獲取文檔失敗: {e}")
            return [None] * len(keys)
    
    def mset(self, key_value_pairs: List[tuple]) -> None:
        """批量設置文檔"""
        try:
            from qdrant_client.models import PointStruct
            
            points = []
            for i, (key, value) in enumerate(key_value_pairs):
                point = PointStruct(
                    id=hash(key) % (2**63),  # 生成唯一ID
                    vector=[0.0],  # 占位向量
                    payload={
                        "doc_id": key,
                        "content": value
                    }
                )
                points.append(point)
            
            if points:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"✅ 批量存儲 {len(points)} 個文檔")
        except Exception as e:
            logger.error(f"批量設置文檔失敗: {e}")
    
    def mdelete(self, keys: List[str]) -> None:
        """批量刪除文檔"""
        try:
            for key in keys:
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector={
                        "filter": {
                            "must": [{"key": "doc_id", "match": {"value": key}}]
                        }
                    }
                )
            logger.info(f"✅ 批量刪除 {len(keys)} 個文檔")
        except Exception as e:
            logger.error(f"批量刪除文檔失敗: {e}")

    def yield_keys(self, prefix: Optional[str] = None):
        """返回鍵值的迭代器"""
        try:
            if prefix:
                scroll_filter = {
                    "must": [{"key": "doc_id", "match": {"text": f"{prefix}*"}}]
                }
            else:
                scroll_filter = None

            points, _ = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=1000,
                with_payload=True
            )

            for point in points:
                yield point.payload.get("doc_id")
        except Exception as e:
            logger.error(f"獲取鍵值迭代器失敗: {e}")
            return iter([])

class LangChainParentChildRAG:
    """基於LangChain的Parent-Child RAG系統"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.child_collection_name = f"{collection_name}_langchain_children"
        self.parent_collection_name = f"{collection_name}_langchain_parents"
        
        # 初始化Qdrant客戶端
        self.qdrant_client = QdrantClient(url=Config.QDRANT_URL)
        
        # 初始化嵌入模型
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_EMBEDDING_MODEL
        )
        
        # 確保子集合存在
        self._ensure_child_collection()

        # 初始化向量存儲
        self.vectorstore = Qdrant(
            client=self.qdrant_client,
            collection_name=self.child_collection_name,
            embeddings=self.embeddings
        )
        
        # 初始化文檔存儲
        self.docstore = QdrantDocStore(self.qdrant_client, collection_name)
        
        # 初始化文本分割器 - 更保守的參數
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # 降低父段落大小
            chunk_overlap=150,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )
        
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,   # 增加子段落大小
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )
        
        # 初始化檢索器
        self.retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            child_splitter=self.child_splitter,
            parent_splitter=self.parent_splitter,
            search_kwargs={"k": 15}  # 增加檢索數量
        )
        
        logger.info(f"✅ LangChain Parent-Child RAG系統初始化完成")
        logger.info(f"  子段落集合: {self.child_collection_name}")
        logger.info(f"  父段落存儲: {self.parent_collection_name}")

    def _ensure_child_collection(self):
        """確保子集合存在"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.child_collection_name not in collection_names:
                # 獲取嵌入模型的維度
                embedding_dimension = self._get_embedding_dimension()

                # 創建子集合用於向量存儲
                self.qdrant_client.create_collection(
                    collection_name=self.child_collection_name,
                    vectors_config=VectorParams(
                        size=embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ 創建子段落集合: {self.child_collection_name} (維度: {embedding_dimension})")
            else:
                logger.info(f"✅ 子段落集合已存在: {self.child_collection_name}")
        except Exception as e:
            logger.error(f"創建子段落集合失敗: {e}")
            raise

    def _get_embedding_dimension(self) -> int:
        """獲取嵌入模型的維度"""
        model_dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072
        }

        return model_dimensions.get(Config.OPENAI_EMBEDDING_MODEL, 1536)
    
    def add_documents_from_zerox(self, zerox_chunks: List) -> Dict[str, Any]:
        """從Zerox處理結果添加文檔"""
        try:
            # 轉換Zerox chunks為LangChain Documents
            documents = []
            for chunk in zerox_chunks:
                # 組合內容：包含圖片分析和metadata
                content_parts = [chunk.content]
                
                if hasattr(chunk, 'image_analysis') and chunk.image_analysis:
                    content_parts.append(f"\n\n**圖片分析**: {chunk.image_analysis}")
                
                if hasattr(chunk, 'technical_symbols') and chunk.technical_symbols:
                    content_parts.append(f"\n\n**技術符號**: {', '.join(chunk.technical_symbols)}")
                
                full_content = "".join(content_parts)
                
                # 創建LangChain Document
                doc = Document(
                    page_content=full_content,
                    metadata={
                        "page_num": chunk.page_num,
                        "topic": chunk.topic,
                        "sub_topic": chunk.sub_topic,
                        "content_type": chunk.content_type,
                        "keywords": chunk.keywords,
                        "difficulty_level": chunk.difficulty_level,
                        "chunk_id": chunk.chunk_id,
                        "has_images": getattr(chunk, 'has_images', False),
                        "image_path": getattr(chunk, 'image_path', ''),
                        "source_filename": getattr(chunk, 'source_filename', ''),
                        "source": f"page_{chunk.page_num}"
                    }
                )
                documents.append(doc)
            
            # 添加文檔到檢索器
            logger.info(f"🔄 開始處理 {len(documents)} 個文檔...")
            start_time = time.time()
            
            self.retriever.add_documents(documents)
            
            processing_time = time.time() - start_time
            
            # 統計信息
            result = {
                "success": True,
                "original_chunks": len(zerox_chunks),
                "documents_added": len(documents),
                "processing_time": processing_time,
                "child_collection": self.child_collection_name,
                "parent_collection": self.parent_collection_name
            }
            
            logger.info(f"✅ LangChain處理完成:")
            logger.info(f"  原始段落: {result['original_chunks']}")
            logger.info(f"  添加文檔: {result['documents_added']}")
            logger.info(f"  處理時間: {result['processing_time']:.2f}秒")
            
            return result
            
        except Exception as e:
            logger.error(f"添加文檔失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 10) -> List[LangChainRetrievalResult]:
        """檢索相關段落 - 真正的父子關係檢索"""
        try:
            logger.info(f"🔍 LangChain檢索查詢: {query}")

            # 步驟1: 先在子段落中搜索，獲取相關的子段落
            child_docs = self.vectorstore.similarity_search_with_score(query, k=top_k*2)
            logger.info(f"🔍 在子段落中找到 {len(child_docs)} 個相關結果")

            # 步驟2: 根據子段落的ID獲取對應的父段落
            results = []
            processed_parent_ids = set()  # 避免重複的父段落

            for child_doc, score in child_docs:
                try:
                    # 獲取子段落的父文檔ID
                    parent_id = child_doc.metadata.get('doc_id', '')
                    logger.debug(f"子段落metadata: {child_doc.metadata}")
                    logger.debug(f"父文檔ID: {parent_id}")

                    if not parent_id or parent_id in processed_parent_ids:
                        # 如果沒有父ID，直接使用子段落內容作為父內容
                        if not parent_id:
                            logger.debug("沒有找到父文檔ID，使用子段落內容")
                            parent_content = child_doc.page_content
                        else:
                            continue
                    else:
                        processed_parent_ids.add(parent_id)

                        # 從docstore獲取完整的父段落
                        parent_docs = self.docstore.mget([parent_id])
                        logger.debug(f"從docstore獲取的父文檔: {parent_docs}")

                        if parent_docs and parent_docs[0]:
                            parent_content = parent_docs[0]
                            logger.debug(f"父段落長度: {len(parent_content)}")
                        else:
                            logger.debug("docstore返回空，使用子段落內容作為父內容")
                            parent_content = child_doc.page_content

                    # 計算相似度分數（轉換為0-1範圍）
                    similarity_score = max(0.1, min(1.0, 1.0 - score))

                    # 生成相關性解釋
                    relevance_reason = self._explain_relevance(query, child_doc, similarity_score)

                    # 創建結果對象，包含真正的父子關係
                    result = LangChainRetrievalResult(
                        document=child_doc,  # 保留原始子文檔的metadata
                        similarity_score=similarity_score,
                        relevance_reason=relevance_reason,
                        parent_content=parent_content,  # 完整的父段落內容
                        child_content=child_doc.page_content  # 匹配的子段落內容
                    )
                    results.append(result)

                    # 限制結果數量
                    if len(results) >= top_k:
                        break

                except Exception as doc_error:
                    logger.error(f"處理子文檔時出錯: {doc_error}")
                    continue

            # 如果子段落檢索失敗，回退到原始方法
            if not results:
                logger.warning("子段落檢索失敗，回退到ParentDocumentRetriever")
                docs = self.retriever.get_relevant_documents(query)
                docs = docs[:top_k]

                for i, doc in enumerate(docs):
                    similarity_score = max(0.1, 1.0 - (i * 0.1))
                    relevance_reason = self._explain_relevance(query, doc, similarity_score)

                    result = LangChainRetrievalResult(
                        document=doc,
                        similarity_score=similarity_score,
                        relevance_reason=relevance_reason,
                        parent_content=doc.page_content,
                        child_content=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
                    )
                    results.append(result)

            logger.info(f"✅ LangChain父子檢索完成，找到 {len(results)} 個相關結果")
            logger.info(f"   父段落平均長度: {sum(len(r.parent_content) for r in results) // len(results) if results else 0} 字符")
            logger.info(f"   子段落平均長度: {sum(len(r.child_content) for r in results) // len(results) if results else 0} 字符")

            return results

        except Exception as e:
            logger.error(f"LangChain檢索失敗: {e}")
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
            return []
    
    def _explain_relevance(self, query: str, doc: Document, score: float) -> str:
        """生成相關性解釋"""
        reasons = []
        
        if score > 0.7:
            reasons.append("高度相關")
        elif score > 0.4:
            reasons.append("中度相關")
        else:
            reasons.append("低度相關")
        
        # 檢查關鍵字匹配
        query_lower = query.lower()
        content_lower = doc.page_content.lower()
        
        if any(word in content_lower for word in query_lower.split()):
            reasons.append("關鍵字匹配")
        
        # 檢查metadata匹配
        metadata = doc.metadata
        if metadata.get('topic') and any(word in metadata['topic'].lower() for word in query_lower.split()):
            reasons.append("主題匹配")
        
        return "; ".join(reasons)
    
    def has_vector_data(self) -> bool:
        """檢查是否有向量數據"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.child_collection_name in collection_names:
                child_info = self.qdrant_client.get_collection(self.child_collection_name)
                child_count = child_info.vectors_count or child_info.points_count or 0
                return child_count > 0
            
            return False
        except Exception as e:
            logger.warning(f"檢查向量數據時發生錯誤: {e}")
            return False
    
    def generate_answer(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """生成回答 - 兼容原有 API"""
        try:
            # 檢索相關段落
            retrieval_results = self.retrieve_relevant_chunks(query, top_k)

            if not retrieval_results:
                return {
                    "answer": "抱歉，我無法在知識庫中找到相關資訊來回答您的問題。",
                    "sources": [],
                    "query": query
                }

            # 準備上下文
            context_parts = []
            sources = []

            for result in retrieval_results:
                # 使用父段落作為上下文
                context_parts.append(result.parent_content)

                # 構建來源資訊
                source_info = {
                    "has_images": result.document.metadata.get('has_images', False),
                    "image_paths": [result.document.metadata.get('image_path', '')] if result.document.metadata.get('image_path') else [],
                    "page_num": result.document.metadata.get('page_num', 0),
                    "topic": result.document.metadata.get('topic', ''),
                    "content": result.child_content,
                    "similarity_score": result.similarity_score
                }
                sources.append(source_info)

            # 使用 OpenAI 生成回答
            from openai import OpenAI
            client = OpenAI(api_key=Config.OPENAI_API_KEY)

            context = "\n\n".join(context_parts[:5])  # 限制上下文長度

            prompt = f"""基於以下教材內容回答問題：

{context}

問題：{query}

請根據教材內容提供準確、詳細的回答。如果教材中有相關圖片或圖表，請在回答中提及。"""

            completion = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )

            answer = completion.choices[0].message.content

            return {
                "answer": answer,
                "sources": sources,
                "query": query,
                "retrieval_count": len(retrieval_results)
            }

        except Exception as e:
            logger.error(f"生成回答失敗: {e}")
            return {
                "answer": f"抱歉，處理您的問題時發生錯誤：{str(e)}",
                "sources": [],
                "query": query
            }

    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統資訊"""
        return {
            "system_type": "LangChain Parent-Child RAG",
            "collection_name": self.collection_name,
            "child_collection": self.child_collection_name,
            "parent_collection": self.parent_collection_name,
            "embedding_model": Config.OPENAI_EMBEDDING_MODEL,
            "llm_model": Config.OPENAI_MODEL,
            "chunking_strategy": "langchain_parent_child",
            "parent_chunk_size": 1500,
            "child_chunk_size": 400
        }
