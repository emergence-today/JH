# 今皓專家 RAG 智能問答系統

## 📖 專案概述

這是一個專為製造業品管教育訓練設計的智能問答系統，整合了 **Zerox 視覺處理** 和 **LangChain Parent-Child RAG** 技術，能夠處理包含技術圖面的PDF教材，並提供基於RAG (Retrieval-Augmented Generation) 的智能問答服務。系統支援多模態分析，能夠理解和解釋技術圖面中的符號、標記和內容。

## 🚀 主要功能

- **📄 Zerox PDF處理**: 使用 py-zerox 進行高品質PDF視覺分析和文字提取
- **🔍 多模態視覺分析**: 支援 Claude 和 GPT-4o 分析技術圖面和符號
- **🏗️ Parent-Child RAG**: 使用 LangChain 實現階層式文檔檢索，提升檢索精度
- **🧠 智能分類**: 自動識別主題、內容類型和難度等級
- **🔎 向量檢索**: 基於Qdrant向量資料庫的語義搜尋
- **💬 技藝聊天**: 專業的製造業技術問答，結合文字和圖片的智能回答
- **🧠 記憶功能**: 支援多會話記憶管理和上下文對話
- **🌐 API服務**: 提供完整的RESTful API
- **📊 RAG測試模組**: 完整的測試框架，支援圖片測試和品質評估

## 🏗️ 系統架構

```
PDF文件 → Zerox處理器 → Parent-Child分割 → 向量嵌入 → Qdrant資料庫 → API服務 → 智能問答
    ↓         ↓            ↓            ↓          ↓         ↓
  圖片提取  Claude/GPT視覺  階層式段落   1536維向量  語義搜尋  多模態回應
```

## 📊 完整資料流程圖

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF文件上傳    │───▶│   Zerox處理器    │───▶│   視覺分析       │
│  /process-pdf   │    │  py-zerox       │    │  Claude/GPT-4o  │
└─────────────────┘    │  頁面圖片生成    │    │  技術符號識別   │
                       │  空白頁檢測     │    │  內容結構化     │
                       └─────────────────┘    └─────────────────┘
                                ↓                       ↓
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   專家知識庫     │    │ Parent-Child分割 │    │  ZeroxChunk     │
│  專家/圖紙認識   │    │  LangChain      │    │  結構化物件     │
│  專家/材料認識   │    │  階層式檢索     │    │  JSONL格式      │
│  專家/製程學習   │    │  父子段落關係   │    │  圖片路徑       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ↓                       ↓
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API服務       │◀───│   Qdrant向量庫   │◀───│   向量儲存       │
│  FastAPI        │    │  Parent集合     │    │  1536維向量     │
│  Port 8006      │    │  Child集合      │    │  階層Metadata   │
└─────────────────┘    │  語義搜尋       │    │  圖片關聯       │
         ↓              └─────────────────┘    └─────────────────┘
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用戶查詢       │    │   記憶管理       │    │   智能回應       │
│  /query         │    │  會話記憶       │    │  RAG生成        │
│  /chat          │    │  上下文追蹤     │    │  圖片URL        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ↓
┌─────────────────┐
│   RAG測試模組    │
│  圖片測試       │
│  品質評估       │
│  HTML報告       │
└─────────────────┘
```

## 📊 資料流程

### 1. Zerox PDF處理階段
- **視覺分析**: 使用 `py-zerox` 整合 Claude 或 GPT-4o 進行頁面視覺分析
- **圖片生成**: 自動生成每頁PNG圖片，儲存至 `outputs/images/zerox_output/`
- **空白頁檢測**: 智能檢測並跳過空白頁面，節省處理成本
- **多模型支援**: 支援 AWS Bedrock Claude 和 OpenAI GPT-4o
- **成本追蹤**: 詳細的 token 使用量和成本統計
- **文件上傳**: 支援透過API上傳PDF文件進行即時處理

### 2. Parent-Child 分割階段
- **LangChain整合**: 使用 LangChain 的 ParentDocumentRetriever
- **階層式分割**: 父段落(1500字元) + 子段落(400字元)
- **智能重疊**: 父段落150字元重疊，子段落50字元重疊
- **雙向檢索**: 子段落檢索 → 父段落內容回傳
- **文檔存儲**: QdrantDocStore 管理父子段落關係

### 3. 內容分析階段
- **主題識別**: 零件圖、成品圖、圖面符號、線位圖、圖面有效性、公差標準
- **內容分類**: 定義、程序、符號、範例、表格
- **關鍵字提取**: 技術術語、符號、縮寫
- **難度判斷**: 基礎、中級、進階
- **技術符號**: 自動識別 Φ、公差、尺寸等技術符號
- **結構化儲存**: 生成ZeroxDocumentChunk物件並儲存為JSONL格式

### 4. 向量化階段
- **嵌入模型**: `text-embedding-3-small` (1536維)
- **向量資料庫**: Qdrant (Cosine相似度)
- **雙集合架構**: Parent集合 + Child集合
- **階層式metadata**: 文件結構、主題分類、內容特徵、圖片資訊
- **集合管理**: 支援多個向量集合的建立和管理

### 5. API服務階段
- **FastAPI伺服器**: 提供完整的RESTful API (Port 8006)
- **技藝聊天**: 專業的製造業技術問答服務
- **記憶管理**: 多會話記憶功能，支援上下文對話
- **圖片服務**: 本地圖片服務，支援 `/images/{filename}` 端點
- **健康檢查**: 系統狀態監控和診斷

### 6. RAG測試階段
- **圖片測試**: 支援資料夾和Excel兩種測試模式
- **品質評估**: Claude評估答案品質，生成詳細評分
- **HTML報告**: 生成包含圖片的測試報告
- **成本追蹤**: 自動計算Claude和OpenAI API使用成本

## 🛠️ 技術棧

### 核心技術
- **Python 3.10+**: 主要開發語言
- **FastAPI**: Web API框架
- **Qdrant**: 向量資料庫
- **py-zerox**: PDF視覺處理引擎
- **LangChain**: Parent-Child RAG實現
- **AWS Bedrock Claude**: 視覺分析和回答生成
- **OpenAI GPT-4o**: 視覺分析和回答生成
- **OpenAI Embeddings**: 文字向量化

### 主要依賴
```
fastapi>=0.104.1
qdrant-client>=1.6.4
openai>=1.3.0
langchain>=0.1.0
langchain-community>=0.0.20
langchain-openai>=0.0.6
py-zerox>=0.0.10
boto3>=1.34.0
pdfplumber>=0.9.0
PyMuPDF>=1.23.0
numpy>=1.24.0
scipy>=1.11.0
python-dotenv>=1.0.0
uvicorn>=0.24.0
pillow>=10.0.0
```

## 📁 專案結構

```
今皓專家RAG系統/
├── main.py                          # FastAPI主應用程式
├── requirements.txt                 # 依賴套件
├── README.md                       # 專案說明文件
├── config/                         # 系統配置
│   ├── config.py                   # 主要配置文件
│   └── .env                        # 環境變數配置
├── src/                            # 核心源碼
│   ├── core/                       # 核心模組
│   │   └── langchain_rag_system.py # LangChain Parent-Child RAG
│   └── processors/                 # 處理器模組
│       ├── pdf_processor.py        # PDF處理器
│       ├── zerox_pdf_processor.py  # Zerox PDF處理器
│       └── file_converter.py       # 文件轉換器
├── scripts/                        # 腳本工具
│   └── process_single_folder_langchain.py # 批量處理腳本
├── outputs/                        # 輸出目錄
│   ├── images/                     # 圖片輸出
│   │   └── zerox_output/           # Zerox處理的圖片
│   ├── embeddings/                 # 嵌入向量
│   ├── metadata_cache/             # 元數據快取
│   └── reports/                    # 處理報告
├── 專家/                           # 專家知識庫
│   ├── 圖紙認識/                   # 圖紙識別教材
│   ├── 材料認識/                   # 材料認識教材
│   ├── 製程學習/                   # 製程學習教材
│   └── 體系訓練/                   # 體系訓練教材
└── RAG_test_module/                # RAG測試模組
    ├── run_test.py                 # 測試啟動腳本
    ├── smart_tester.py             # 智能測試器
    ├── interactive_smart_tester.py # 互動式測試器
    ├── config/                     # 測試配置
    ├── core/                       # 測試核心
    ├── utils/                      # 測試工具
    └── results/                    # 測試結果
```

## ⚙️ 安裝與設定

### 1. 環境準備
```bash
# 克隆專案
git clone <repository-url>
cd 今皓專家RAG(鑑識圖片PPT)

# 安裝依賴
pip install -r requirements.txt
```

### 2. 環境變數設定
創建 `.env` 文件：
```env
# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Qdrant設定
QDRANT_URL=http://ec2-13-112-118-36.ap-northeast-1.compute.amazonaws.com:6333
QDRANT_COLLECTION_NAME=your_collection_name_here

# API設定
MAX_TOKENS=1000
TEMPERATURE=0.7
TOP_K_RETRIEVAL=3
```

### 3. 資料準備
```bash
# 注意：本專案使用手動匯入的 Qdrant 知識庫
# 確保您的 Qdrant 集合中已有資料

# 啟動API服務
uv run main.py
```

## 🚀 使用方式

### 1. 啟動服務
```bash
uv run main.py
```
服務將在 `http://localhost:8006` 啟動

### 2. API端點總覽

| 端點 | 方法 | 功能 | 說明 |
|------|------|------|------|
| `/` | GET | 根路徑 | API基本資訊 |
| `/health` | GET | 健康檢查 | 系統狀態監控 |
| `/query` | POST | 技藝問答 | 專業製造業技術問答API |
| `/query-with-memory` | POST | 記憶問答 | 支援會話記憶的技術問答API |
| `/chat` | POST | 技藝聊天 | 支援會話記憶的技術聊天API |
| `/process-pdf` | POST | PDF處理 | 上傳並處理PDF文件 |
| `/collections` | GET | 列出集合 | 獲取所有Qdrant集合 |
| `/collections/{name}` | DELETE | 刪除集合 | 刪除指定的向量集合 |
| `/sessions` | GET | 列出會話 | 獲取所有聊天會話ID |
| `/sessions/{id}` | GET | 會話資訊 | 獲取指定會話的詳細資訊 |
| `/sessions/{id}` | DELETE | 清除會話 | 清除指定會話的記憶 |
| `/images/{filename}` | GET | 靜態圖片 | 提供本地圖片檔案 |

### 3. 詳細API說明

#### 🏠 根路徑
```bash
GET /
```
**回應**: API基本資訊和導航連結

#### 🔍 健康檢查
```bash
GET /health
```
**回應**: 系統狀態、Qdrant連線、文件段落數、圖片數量

#### 🤖 技藝問答
```bash
POST /query
Content-Type: application/json

{
    "question": "Φ符號代表什麼意思？",
    "chatId": "chat_123"
}
```
**功能**: 專業製造業技術問答，支援圖片URL回傳（無會話記憶）

#### 🧠 記憶問答
```bash
POST /query-with-memory
Content-Type: application/json

{
    "question": "你還記得我剛才問的問題嗎？",
    "chatId": "chat_123"
}
```
**功能**: 支援會話記憶的技術問答功能，chatId會作為session_id使用

#### 💬 技藝聊天
```bash
POST /chat
Content-Type: application/json

{
    "message": "你好，我想學習圖面識別",
    "session_id": "optional_session_id",
    "use_rag": true,
    "top_k": 3
}
```
**功能**: 支援會話記憶的製造業技術聊天，可選擇是否使用RAG檢索

#### 📄 PDF文件處理
```bash
POST /process-pdf
Content-Type: multipart/form-data

Parameters:
- file: PDF文件 (必填)
- collection_name: 自定義集合名稱 (可選)
- enable_vision: 是否啟用視覺分析 (預設: true)
- force_recreate: 是否強制重新創建集合 (預設: false)
```
**功能**: 上傳PDF文件並自動處理、向量化、儲存到Qdrant

#### 🗂️ 集合管理
```bash
# 獲取所有集合
GET /collections

# 刪除指定集合
DELETE /collections/{collection_name}
```
**功能**: 管理Qdrant向量資料庫中的集合

#### 🧠 會話記憶管理
```bash
# 獲取所有會話
GET /sessions

# 獲取會話資訊
GET /sessions/{session_id}

# 清除會話記憶
DELETE /sessions/{session_id}
```
**功能**: 管理聊天會話的記憶和上下文

### 4. 使用範例

#### 🔍 健康檢查範例
```bash
curl -X GET "http://localhost:8006/health"
```

#### 🤖 技藝問答範例
```bash
curl -X POST "http://localhost:8006/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什麼是有效圖面？",
    "chatId": "chat_123"
  }'
```

#### 🧠 記憶問答範例
```bash
# 第一次對話
curl -X POST "http://localhost:8006/query-with-memory" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你好，我想學習圖面識別",
    "chatId": "chat_123"
  }'

# 第二次對話（會記住之前的內容）
curl -X POST "http://localhost:8006/query-with-memory" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你還記得我想學什麼嗎？",
    "chatId": "chat_123"
  }'
```

#### 💬 技藝聊天範例
```bash
curl -X POST "http://localhost:8006/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想學習製程技術",
    "use_rag": true,
    "top_k": 3
  }'
```

#### 📄 PDF文件處理範例
```bash
# 使用curl上傳PDF文件
curl -X POST "http://localhost:8006/process-pdf" \
  -F "file=@your_document.pdf" \
  -F "collection_name=my_custom_collection" \
  -F "enable_vision=true" \
  -F "force_recreate=false"
```

#### 🗂️ 集合管理範例
```bash
# 獲取所有集合
curl -X GET "http://localhost:8006/collections"

# 刪除集合
curl -X DELETE "http://localhost:8006/collections/my_collection"
```

#### 🧠 會話管理範例
```bash
# 獲取所有會話
curl -X GET "http://localhost:8006/sessions"

# 獲取會話資訊
curl -X GET "http://localhost:8006/sessions/session_123"

# 清除會話記憶
curl -X DELETE "http://localhost:8006/sessions/session_123"
```

#### 🐍 Python SDK範例
```python
import requests

class RAGClient:
    def __init__(self, base_url="http://localhost:8006"):
        self.base_url = base_url

    def health_check(self):
        """健康檢查"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

    def query_technical(self, question, chat_id):
        """技藝問答（無記憶）"""
        data = {"question": question, "chatId": chat_id}
        response = requests.post(f"{self.base_url}/query", json=data)
        return response.json()

    def query_with_memory(self, question, chat_id):
        """記憶問答"""
        data = {"question": question, "chatId": chat_id}
        response = requests.post(f"{self.base_url}/query-with-memory", json=data)
        return response.json()

    def technical_chat(self, message, session_id=None, use_rag=True, top_k=3):
        """技藝聊天"""
        data = {
            "message": message,
            "session_id": session_id,
            "use_rag": use_rag,
            "top_k": top_k
        }
        response = requests.post(f"{self.base_url}/chat", json=data)
        return response.json()

    def process_pdf(self, file_path, collection_name=None, enable_vision=True):
        """處理PDF文件"""
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {
                "collection_name": collection_name,
                "enable_vision": enable_vision,
                "force_recreate": False
            }
            response = requests.post(
                f"{self.base_url}/process-pdf",
                files=files,
                data=data
            )
            return response.json()

# 使用範例
client = RAGClient()

# 健康檢查
health = client.health_check()
print(f"系統狀態: {health['status']}")

# 技藝問答對話
chat_id = "user_123"
result1 = client.query_with_memory("你好，我想學習圖面識別", chat_id)
print(f"AI回應: {result1['text']}")

result2 = client.query_with_memory("你還記得我想學什麼嗎？", chat_id)
print(f"AI回應: {result2['text']}")

# 或使用技藝聊天格式
session_id = None
result3 = client.technical_chat("你好，我想學習製程技術")
session_id = result3["session_id"]

result4 = client.technical_chat("你還記得我想學什麼嗎？", session_id)
print(f"AI回應: {result4['response']}")
```

### 5. API回應格式

#### 🏠 根路徑回應
```json
{
    "message": "圖面識別教學 RAG API",
    "version": "1.0.0",
    "docs": "/docs",
    "health": "/health"
}
```

#### 🔍 健康檢查回應
```json
{
    "status": "healthy",
    "qdrant_connected": true,
    "chunks_loaded": 15,
    "images_available": 3
}
```

#### 🤖 技藝問答回應
```json
{
    "text": "有效圖面是指經工程部正式發行的零件圖，須蓋有檢驗章、檢驗工具章、公差章、工程部主管審核章及發行版本、工程部發行章。\n\n📷 相關圖片：\n1. http://localhost:8006/images/圖面識別教材_PDF_page_1.png",
    "question": "什麼是有效圖面？",
    "chatId": "chat_123",
    "sessionId": "session_chat_123_1720012345",
    "chatMessageId": "uuid-generated-id"
}
```

#### 💬 技藝聊天回應
```json
{
    "response": "你好！很高興認識你。我是專業的製造業技術講師助手，可以幫你學習圖面識別、材料認識、製程技術等相關知識。",
    "session_id": "abc123-def456-ghi789",
    "message_count": 2,
    "total_tokens": 156,
    "sources": [],
    "rag_used": false
}
```

#### 📄 PDF處理回應
```json
{
    "success": true,
    "message": "成功處理PDF文件 'technical_manual.pdf'",
    "chunks_processed": 25,
    "images_extracted": 8,
    "collection_name": "my_custom_collection",
    "processing_time": 45.67,
    "errors": []
}
```

#### 🗂️ 集合列表回應
```json
[
    "steven_test_0703",
    "my_custom_collection",
    "another_collection"
]
```

#### 🧠 會話資訊回應
```json
{
    "session_id": "abc123-def456-ghi789",
    "exists": true,
    "message_count": 5,
    "total_tokens": 1250,
    "last_activity": 1720012345.67
}
```

## 📈 系統特色

### 1. 多模態處理
- **文字理解**: 精確提取和分析技術文件內容
- **圖片分析**: GPT-4o視覺分析技術圖面
- **符號識別**: 自動識別Φ、公差、尺寸等技術符號

### 2. 智能分類
- **主題分類**: 6大主題自動分類
- **內容類型**: 5種內容類型識別
- **難度等級**: 3級難度自動判斷

### 3. 高效檢索
- **語義搜尋**: 基於向量相似度的精確檢索
- **階層式metadata**: 豐富的結構化資訊
- **相關性解釋**: 自動解釋檢索結果的相關性

### 4. 企業級部署
- **雲端整合**: AWS S3圖片服務
- **API標準**: RESTful API設計
- **監控功能**: 健康檢查和系統統計
- **擴展性**: 支援Flowise等第三方平台

## 🔧 配置說明

### 主題分類配置
```python
TOPIC_CATEGORIES = {
    "零件圖": ["零件圖", "零件", "供應商", "IQC"],
    "成品圖": ["成品圖", "成品", "組裝", "BOM"],
    "圖面符號": ["符號", "Φ", "直徑", "厚度", "公差", "單位"],
    "線位圖": ["線位圖", "PIN", "連接器", "電路"],
    "圖面有效性": ["有效圖面", "檢驗章", "審核章", "發行版本"],
    "公差標準": ["公差", "Max", "Min", "標準", "規格"]
}
```

### 教學模式配置
- **qa**: 問答模式 - 回答具體問題
- **quiz**: 測驗模式 - 生成測驗題目  
- **guide**: 導讀模式 - 章節重點說明
- **search**: 搜尋模式 - 關鍵字查詢
- **explain**: 解釋模式 - 深度說明概念

## 📊 系統統計

目前系統包含：
- **15個文件段落**: 來自PDF的結構化內容
- **3張圖片**: 提取的技術圖面
- **6個主題分類**: 涵蓋品管教學重點
- **1536維向量**: 高精度語義表示

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件

## 📞 聯絡資訊

- **專案維護者**: 今皓專家團隊
- **技術支援**: [技術支援信箱]
- **專案網址**: [專案GitHub連結]

## 📋 API功能總結

### 🎯 核心功能
1. **PDF文件處理** (`/process-pdf`)
   - 支援PDF文件上傳和即時處理
   - Zerox視覺分析技術圖面
   - Parent-Child階層式分割
   - 自動向量化並儲存到Qdrant

2. **技藝問答** (`/query`, `/chat`)
   - 專業製造業技術問答API
   - 支援會話記憶的聊天功能
   - RAG檢索增強生成
   - 多模態回應（文字+圖片URL）

3. **記憶管理** (`/sessions/*`)
   - 多會話記憶追蹤
   - 上下文對話支援
   - Token使用量統計
   - 會話生命週期管理

4. **集合管理** (`/collections/*`)
   - 多個Qdrant集合支援
   - 動態集合建立和刪除
   - 集合狀態查詢

5. **系統監控** (`/health`, `/`)
   - 即時健康檢查
   - 系統狀態診斷
   - 資源使用統計

### 🔧 技術特色
- **Parent-Child RAG**: LangChain階層式檢索，提升檢索精度
- **Zerox視覺處理**: 高品質PDF視覺分析和文字提取
- **多模態處理**: 文字+圖片的綜合分析
- **記憶功能**: 智能會話記憶管理
- **企業級**: RESTful API設計，專注製造業技術問答

### 🌐 部署資訊
- **服務端口**: 8006
- **API根路徑**: `/api/v1/JH`
- **文檔地址**: `/docs` (Swagger UI)
- **健康檢查**: `/health`

---

---

## 🚀 快速開始

### 1. 環境設置
```bash
# 克隆專案
git clone <repository-url>
cd JH

# 安裝依賴
uv install

# 設置環境變數
cp config/.env.template .env
# 編輯 .env 文件，填入必要的 API 金鑰
```

### 2. 處理專家知識庫
```bash
# 處理圖紙認識教材
uv run scripts/process_single_folder_langchain.py

# 或批量處理
uv run embedding2qdrant/batch_process_files.py "專家/圖紙認識" --collection-name "JH-圖紙認識-langchain"
```

### 3. 啟動服務
```bash
uv run main.py
```

### 4. 測試RAG系統
```bash
cd RAG_test_module
python3 run_test.py
```

---

*最後更新: 2025-01-15*