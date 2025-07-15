"""
配置文件 - 系統設定和參數
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

# 載入 .env 文件
load_dotenv()

class Config:
    """系統配置類"""

    # Qdrant 設定
    QDRANT_URL = os.getenv("QDRANT_URL", "http://ec2-13-112-118-36.ap-northeast-1.compute.amazonaws.com:6333")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "steven_JH")

    # OpenAI API 設定 - 從 .env 讀取
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

    # Zerox 視覺處理模型
    ZEROX_MODEL = os.getenv("ZEROX_MODEL", "gpt-4o")

    # AWS Bedrock 設定 - 從 .env 讀取
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "us.anthropic.claude-sonnet-4-20250514-v1:0")

    # RAG檢索參數 - 從 .env 讀取，如果沒有則使用預設值
    DEFAULT_TOP_K = int(os.getenv("TOP_K_RETRIEVAL", "3"))

    # 語言模型參數 - 從 .env 讀取
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

    # LangChain 設定
    LANGCHAIN_VERBOSE = os.getenv("LANGCHAIN_VERBOSE", "false").lower() == "true"
    LANGCHAIN_CACHE = os.getenv("LANGCHAIN_CACHE", "true").lower() == "true"

    # 記憶管理設定
    MEMORY_MAX_TOKENS = int(os.getenv("MEMORY_MAX_TOKENS", "8000"))
    MEMORY_WINDOW_SIZE = int(os.getenv("MEMORY_WINDOW_SIZE", "10"))  # 保留最近N輪對話

    # 向量檢索設定
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "3072"))  # text-embedding-3-large

    # Chain 設定
    CHAIN_TYPE = os.getenv("CHAIN_TYPE", "stuff")  # stuff, map_reduce, refine, map_rerank
    RETURN_SOURCE_DOCUMENTS = os.getenv("RETURN_SOURCE_DOCUMENTS", "true").lower() == "true"

    # RAG系統類型 - 固定使用 LangChain
    RAG_SYSTEM_TYPE = "langchain"

    # API 基礎 URL 設定
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8006")

# 環境變數檢查
def check_environment():
    """檢查環境變數和依賴"""
    issues = []
    
    # 檢查OpenAI API Key
    if not Config.OPENAI_API_KEY:
        issues.append("未設定 OPENAI_API_KEY 環境變數")

    return issues

if __name__ == "__main__":
    # 測試配置
    issues = check_environment()
    if issues:
        print("⚠️ 環境檢查發現問題:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ 環境檢查通過")

    print(f"\n📋 配置摘要:")
    print(f"  向量模型: {Config.OPENAI_EMBEDDING_MODEL}")
    print(f"  Qdrant URL: {Config.QDRANT_URL}")
    print(f"  集合名稱: {Config.QDRANT_COLLECTION_NAME}")
