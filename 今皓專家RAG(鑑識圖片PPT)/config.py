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

    # 文件路徑 - 從 .env 讀取，如果沒有則使用預設值
    PDF_FILE_PATH = os.getenv("PDF_FILE_PATH", "圖面識別教材_PDF.pdf")
    CHUNKS_FILE_PATH = os.getenv("CHUNKS_FILE_PATH", "processed_chunks.jsonl")

    # Qdrant 設定
    QDRANT_URL = os.getenv("QDRANT_URL", "http://ec2-13-112-118-36.ap-northeast-1.compute.amazonaws.com:6333")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "steven_JH_pro_0704")

    # OpenAI API 設定 - 從 .env 讀取
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # RAG檢索參數 - 從 .env 讀取，如果沒有則使用預設值
    DEFAULT_TOP_K = int(os.getenv("TOP_K_RETRIEVAL", "3"))
    MAX_TOP_K = 10
    SIMILARITY_THRESHOLD = 0.3

    # 語言模型參數 - 從 .env 讀取
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

    # Streamlit 設定
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # 教學模式配置
    TEACHING_MODES = {
        "qa": {
            "name": "問答模式",
            "description": "回答具體問題",
            "icon": "🤔",
            "prompt_template": """你是一位專業的品管教育訓練講師，請根據以下教材內容回答學員問題。

教材內容：
{context}

學員問題：{query}

請用清楚、條理分明的方式回答，包括：
1. 直接回答問題
2. 相關的重要概念說明
3. 如果有範例或圖面說明，請一併提供

回答："""
        },
        "quiz": {
            "name": "測驗模式",
            "description": "生成測驗題目",
            "icon": "📝",
            "prompt_template": """基於以下教材內容，請生成3道測驗題目：

教材內容：
{context}

請生成：
1. 1道選擇題（4個選項）
2. 1道是非題
3. 1道簡答題

每題都要包含正確答案和簡要解釋。

測驗題目："""
        },
        "guide": {
            "name": "導讀模式", 
            "description": "章節重點說明",
            "icon": "📖",
            "prompt_template": """請為以下教材內容提供學習導讀：

教材內容：
{context}

請提供：
1. 本章節的學習重點
2. 關鍵概念解釋
3. 學習建議和注意事項
4. 與其他章節的關聯

導讀內容："""
        },
        "explain": {
            "name": "解釋模式",
            "description": "深度概念解釋", 
            "icon": "💡",
            "prompt_template": """請對以下概念進行深度解釋：

相關教材內容：
{context}

要解釋的概念：{query}

請提供：
1. 清楚的定義
2. 實際應用場景
3. 常見錯誤或注意事項
4. 相關概念的關聯性

詳細解釋："""
        },
        "search": {
            "name": "搜尋模式",
            "description": "關鍵字查詢",
            "icon": "🔍",
            "prompt_template": """基於搜尋結果，請整理相關資訊：

搜尋關鍵字：{query}

相關內容：
{context}

請整理：
1. 關鍵字的定義和含義
2. 在教材中的出現位置和用法
3. 相關的重要資訊

搜尋結果整理："""
        }
    }
    
    # 主題分類配置
    TOPIC_CATEGORIES = {
        "零件圖": {
            "keywords": ["零件圖", "零件", "供應商", "IQC"],
            "color": "#FF6B6B",
            "description": "零件圖相關內容，包括來源、有效性判斷等"
        },
        "成品圖": {
            "keywords": ["成品圖", "成品", "組裝", "BOM"],
            "color": "#4ECDC4", 
            "description": "成品圖相關內容，包括組裝圖面、BOM等"
        },
        "圖面符號": {
            "keywords": ["符號", "Φ", "直徑", "厚度", "公差", "單位"],
            "color": "#45B7D1",
            "description": "圖面符號解釋，包括各種標記和符號含義"
        },
        "線位圖": {
            "keywords": ["線位圖", "PIN", "連接器", "電路"],
            "color": "#96CEB4",
            "description": "線位圖說明，包括PIN腳定義、連接器資訊"
        },
        "圖面有效性": {
            "keywords": ["有效圖面", "檢驗章", "審核章", "發行版本"],
            "color": "#FFEAA7",
            "description": "圖面有效性判斷標準和要求"
        },
        "公差標準": {
            "keywords": ["公差", "Max", "Min", "標準", "規格"],
            "color": "#DDA0DD",
            "description": "公差標準和規格要求"
        }
    }
    
    # 內容類型配置
    CONTENT_TYPES = {
        "definition": "定義說明",
        "procedure": "操作程序", 
        "symbol": "符號解釋",
        "example": "範例說明",
        "table": "表格資料"
    }
    
    # 難度等級配置
    DIFFICULTY_LEVELS = {
        "basic": {
            "name": "基礎",
            "color": "#90EE90",
            "description": "基本概念和定義"
        },
        "intermediate": {
            "name": "中級", 
            "color": "#FFD700",
            "description": "需要一定理解的概念"
        },
        "advanced": {
            "name": "進階",
            "color": "#FF6347", 
            "description": "複雜概念和專業知識"
        }
    }
    
    # Streamlit界面配置
    STREAMLIT_CONFIG = {
        "page_title": "圖面識別教學助手",
        "page_icon": "📚",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    
    # 快速問題模板
    QUICK_QUESTIONS = [
        "什麼是有效圖面？",
        "Φ符號代表什麼意思？",
        "零件圖和成品圖的差異？", 
        "如何判斷圖面有效性？",
        "線位圖包含哪些資訊？",
        "公差標準怎麼看？",
        "IQC檢驗需要注意什麼？",
        "圖面上的檢驗章有哪些？",
        "PIN腳定義怎麼看？",
        "圖面符號有哪些類型？"
    ]
    
    # 日誌配置
    LOGGING_CONFIG = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "teaching_chatbot.log"
    }

# 環境變數檢查
def check_environment():
    """檢查環境變數和依賴"""
    issues = []
    
    # 檢查OpenAI API Key
    if not Config.OPENAI_API_KEY:
        issues.append("未設定 OPENAI_API_KEY 環境變數")
    
    # 檢查必要文件
    if not os.path.exists(Config.PDF_FILE_PATH):
        issues.append(f"找不到PDF文件: {Config.PDF_FILE_PATH}")

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
    print(f"  PDF文件: {Config.PDF_FILE_PATH}")
    print(f"  向量模型: {Config.OPENAI_EMBEDDING_MODEL}")
    print(f"  支援模式: {len(Config.TEACHING_MODES)} 種")
    print(f"  主題分類: {len(Config.TOPIC_CATEGORIES)} 類")
