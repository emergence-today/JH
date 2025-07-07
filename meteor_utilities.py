"""
MeteorUtilities - OpenAI 向量化實現
使用 OpenAI API 進行文本向量化
"""

import logging
from typing import List, Optional
from openai import OpenAI
from config import Config
import time

logger = logging.getLogger(__name__)

class MeteorUtilities:
    """使用 OpenAI API 的向量化工具"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 MeteorUtilities

        Args:
            api_key: OpenAI API 金鑰，如果不提供則從配置讀取
        """
        # 優先使用傳入的 API 金鑰，否則從配置讀取
        self.api_key = api_key or Config.OPENAI_API_KEY

        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError("請設定有效的 OPENAI_API_KEY")

        self.client = OpenAI(api_key=self.api_key)
        self.embedding_model = Config.OPENAI_EMBEDDING_MODEL

        # 根據模型設定向量維度
        self.embedding_dimension = self._get_embedding_dimension()

        logger.info(f"MeteorUtilities 初始化完成 - 模型: {self.embedding_model}, 維度: {self.embedding_dimension}")

    def _get_embedding_dimension(self) -> int:
        """根據模型名稱返回向量維度"""
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return model_dimensions.get(self.embedding_model, 1536)

    def get_embedding(self, text: str, retry_count: int = 3) -> List[float]:
        """
        獲取單個文本的向量嵌入

        Args:
            text: 要向量化的文本
            retry_count: 重試次數

        Returns:
            向量嵌入列表
        """
        if not text or not text.strip():
            logger.warning("輸入文本為空，返回零向量")
            return [0.0] * self.embedding_dimension

        for attempt in range(retry_count):
            try:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=[text.strip()],
                    timeout=30
                )
                embedding = response.data[0].embedding
                logger.debug(f"成功生成向量嵌入，維度: {len(embedding)}")
                return embedding

            except Exception as e:
                logger.warning(f"向量嵌入生成失敗 (嘗試 {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    # 指數退避重試
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"向量嵌入生成最終失敗: {e}")
                    # 返回零向量作為後備
                    return [0.0] * self.embedding_dimension

    def get_embeddings_batch(self, texts: List[str], batch_size: int = 50, retry_count: int = 3) -> List[List[float]]:
        """
        批量獲取文本的向量嵌入

        Args:
            texts: 要向量化的文本列表
            batch_size: 批次大小
            retry_count: 重試次數

        Returns:
            向量嵌入列表的列表
        """
        if not texts:
            logger.warning("輸入文本列表為空")
            return []

        # 過濾空文本
        processed_texts = [text.strip() if text else "" for text in texts]
        all_embeddings = []

        total_batches = (len(processed_texts) - 1) // batch_size + 1

        for i in range(0, len(processed_texts), batch_size):
            batch = processed_texts[i:i + batch_size]
            batch_num = i // batch_size + 1

            logger.info(f"處理批次 {batch_num}/{total_batches} (共 {len(batch)} 個文本)")

            # 為每個批次重試
            batch_success = False
            for attempt in range(retry_count):
                try:
                    response = self.client.embeddings.create(
                        model=self.embedding_model,
                        input=batch,
                        timeout=60
                    )
                    batch_embeddings = [data.embedding for data in response.data]
                    all_embeddings.extend(batch_embeddings)
                    logger.info(f"批次 {batch_num} 完成，處理了 {len(batch)} 個文本")
                    batch_success = True
                    break

                except Exception as e:
                    logger.warning(f"批次 {batch_num} 失敗 (嘗試 {attempt + 1}/{retry_count}): {e}")
                    if attempt < retry_count - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"等待 {wait_time} 秒後重試批次 {batch_num}...")
                        time.sleep(wait_time)

            if not batch_success:
                logger.error(f"批次 {batch_num} 最終失敗，使用零向量")
                # 添加零向量作為後備
                all_embeddings.extend([[0.0] * self.embedding_dimension for _ in batch])

        logger.info(f"批量向量化完成，共生成 {len(all_embeddings)} 個向量")
        return all_embeddings

    def test_connection(self) -> bool:
        """
        測試 OpenAI API 連接

        Returns:
            連接是否成功
        """
        try:
            test_embedding = self.get_embedding("測試連接")
            return len(test_embedding) == self.embedding_dimension
        except Exception as e:
            logger.error(f"連接測試失敗: {e}")
            return False
