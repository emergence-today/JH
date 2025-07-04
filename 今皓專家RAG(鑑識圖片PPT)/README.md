# 圖面識別教學 RAG 系統

## 📖 專案概述

這是一個專為品管教育訓練設計的智能問答系統，能夠處理包含技術圖面的PDF教材，並提供基於RAG (Retrieval-Augmented Generation) 的智能問答服務。系統支援視覺分析，能夠理解和解釋技術圖面中的符號、標記和內容。

## 🚀 主要功能

- **📄 PDF智能處理**: 自動提取文字內容和圖片，支援上傳處理
- **🔍 視覺分析**: 使用GPT-4o分析技術圖面和符號
- **🧠 智能分類**: 自動識別主題、內容類型和難度等級
- **🔎 向量檢索**: 基於Qdrant向量資料庫的語義搜尋
- **💬 多模態問答**: 結合文字和圖片的智能回答
- **🧠 記憶功能**: 支援多會話記憶管理和上下文對話
- **🌐 API服務**: 提供完整的RESTful API
- **🔗 Flowise整合**: 專為Flowise聊天機器人平台設計的API

## 🏗️ 系統架構

```
PDF文件 → PDF處理器 → 內容分析 → 向量嵌入 → Qdrant資料庫 → API服務 → 智能問答
    ↓         ↓         ↓         ↓          ↓         ↓
  圖片提取  視覺分析  結構化段落  1536維向量  語義搜尋  多模態回應
```

## � 完整資料流程圖

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF文件上傳    │───▶│   PDF處理器      │───▶│   內容分析       │
│  /process-pdf   │    │  pdfplumber     │    │  主題分類       │
└─────────────────┘    │  PyMuPDF        │    │  關鍵字提取     │
                       │  GPT-4o視覺     │    │  難度判斷       │
                       └─────────────────┘    └─────────────────┘
                                ↓                       ↓
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   圖片儲存       │    │   向量化處理     │    │  DocumentChunk  │
│  AWS S3雲端     │    │  OpenAI         │    │  結構化物件     │
│  本地images/    │    │  Embeddings     │    │  JSONL格式      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ↓                       ↓
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API服務       │◀───│   Qdrant向量庫   │◀───│   向量儲存       │
│  FastAPI        │    │  語義搜尋       │    │  1536維向量     │
│  Port 8006      │    │  相似度計算     │    │  Metadata       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ↓
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用戶查詢       │    │   記憶管理       │    │   智能回應       │
│  /query         │    │  會話記憶       │    │  RAG生成        │
│  /chat          │    │  上下文追蹤     │    │  圖片URL        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## �📊 資料流程

### 1. PDF處理階段
- **文字提取**: 使用 `pdfplumber` 提取每頁文字內容
- **圖片檢測**: 使用 `PyMuPDF` 檢測並提取頁面圖片
- **視覺分析**: 使用 `GPT-4o` 分析技術圖面和符號
- **文件上傳**: 支援透過API上傳PDF文件進行即時處理

### 2. 內容分析階段
- **主題識別**: 零件圖、成品圖、圖面符號、線位圖、圖面有效性、公差標準
- **內容分類**: 定義、程序、符號、範例、表格
- **關鍵字提取**: 技術術語、符號、縮寫
- **難度判斷**: 基礎、中級、進階
- **結構化儲存**: 生成DocumentChunk物件並儲存為JSONL格式

### 3. 向量化階段
- **嵌入模型**: `text-embedding-3-small` (1536維)
- **向量資料庫**: Qdrant (Cosine相似度)
- **階層式metadata**: 文件結構、主題分類、內容特徵、圖片資訊
- **集合管理**: 支援多個向量集合的建立和管理

### 4. API服務階段
- **FastAPI伺服器**: 提供完整的RESTful API (Port 8006)
- **Flowise整合**: 專用的/query端點支援聊天機器人平台
- **記憶管理**: 多會話記憶功能，支援上下文對話
- **圖片服務**: AWS S3雲端圖片URL生成
- **健康檢查**: 系統狀態監控和診斷

## 🛠️ 技術棧

### 核心技術
- **Python 3.8+**: 主要開發語言
- **FastAPI**: Web API框架
- **Qdrant**: 向量資料庫
- **OpenAI GPT-4o**: 視覺分析和回答生成
- **OpenAI Embeddings**: 文字向量化

### 主要依賴
```
fastapi>=0.104.1
qdrant-client>=1.6.4
openai>=1.3.0
pdfplumber>=0.9.0
PyMuPDF>=1.23.0
PyPDF2>=3.0.1
numpy>=1.24.0
scipy>=1.11.0
python-dotenv>=1.0.0
uvicorn>=0.24.0
```

## 📁 專案結構

```
今皓專家RAG(鑑識圖片PPT)/
├── main.py                 # FastAPI主應用程式
├── pdf_processor.py        # PDF處理器
├── rag_system.py          # RAG系統核心
├── config.py              # 系統配置
├── meteor_utilities.py    # 向量化工具
├── requirements.txt       # 依賴套件
├── processed_chunks.jsonl # 處理後的文件段落
├── images/                # 提取的圖片目錄
│   ├── 圖面識別教材_PDF_page_1.png
│   ├── 圖面識別教材_PDF_page_11.png
│   └── 圖面識別教材_PDF_page_13.png
└── README.md             # 專案說明文件
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
QDRANT_COLLECTION_NAME=steven_test_0703

# 文件路徑
PDF_FILE_PATH=圖面識別教材_PDF.pdf
CHUNKS_FILE_PATH=processed_chunks.jsonl

# API設定
MAX_TOKENS=1000
TEMPERATURE=0.7
TOP_K_RETRIEVAL=3
```

### 3. 資料準備
```bash
# 處理PDF文件 (如果需要重新處理)
python pdf_processor.py

# 啟動API服務
python main.py
```

## 🚀 使用方式

### 1. 啟動服務
```bash
python main.py
```
服務將在 `http://localhost:8006` 啟動

### 2. API端點總覽

| 端點 | 方法 | 功能 | 說明 |
|------|------|------|------|
| `/` | GET | 根路徑 | API基本資訊 |
| `/health` | GET | 健康檢查 | 系統狀態監控 |
| `/query` | POST | Flowise查詢 | 專為Flowise設計的問答API（無記憶） |
| `/query-with-memory` | POST | Flowise記憶查詢 | Flowise格式但支援會話記憶的API |
| `/chat` | POST | 記憶聊天 | 支援會話記憶的聊天API |
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

#### 🤖 Flowise整合查詢
```bash
POST /query
Content-Type: application/json

{
    "question": "Φ符號代表什麼意思？",
    "chatId": "chat_123"
}
```
**功能**: 專為Flowise聊天機器人平台設計，支援圖片URL回傳（無會話記憶）

#### 🧠 Flowise記憶查詢
```bash
POST /query-with-memory
Content-Type: application/json

{
    "question": "你還記得我剛才問的問題嗎？",
    "chatId": "chat_123"
}
```
**功能**: 使用Flowise格式但支援會話記憶功能，chatId會作為session_id使用

#### 💬 記憶聊天
```bash
POST /chat
Content-Type: application/json

{
    "message": "你好，我是小明",
    "session_id": "optional_session_id",
    "use_rag": true,
    "top_k": 3
}
```
**功能**: 支援會話記憶的智能聊天，可選擇是否使用RAG檢索

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

#### 🤖 Flowise查詢範例
```bash
curl -X POST "http://localhost:8006/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什麼是有效圖面？",
    "chatId": "chat_123"
  }'
```

#### 🧠 Flowise記憶查詢範例
```bash
# 第一次對話
curl -X POST "http://localhost:8006/query-with-memory" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你好，我是小明",
    "chatId": "chat_123"
  }'

# 第二次對話（會記住之前的內容）
curl -X POST "http://localhost:8006/query-with-memory" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你還記得我的名字嗎？",
    "chatId": "chat_123"
  }'
```

#### 💬 記憶聊天範例
```bash
curl -X POST "http://localhost:8006/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我是小明",
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

    def query_flowise(self, question, chat_id):
        """Flowise查詢（無記憶）"""
        data = {"question": question, "chatId": chat_id}
        response = requests.post(f"{self.base_url}/query", json=data)
        return response.json()

    def query_flowise_with_memory(self, question, chat_id):
        """Flowise格式的記憶查詢"""
        data = {"question": question, "chatId": chat_id}
        response = requests.post(f"{self.base_url}/query-with-memory", json=data)
        return response.json()

    def chat_with_memory(self, message, session_id=None, use_rag=True, top_k=3):
        """記憶聊天"""
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

# 使用Flowise格式的記憶對話
chat_id = "user_123"
result1 = client.query_flowise_with_memory("你好，我是小明", chat_id)
print(f"AI回應: {result1['text']}")

result2 = client.query_flowise_with_memory("你還記得我的名字嗎？", chat_id)
print(f"AI回應: {result2['text']}")

# 或使用原始的記憶聊天格式
session_id = None
result3 = client.chat_with_memory("你好，我是小王")
session_id = result3["session_id"]

result4 = client.chat_with_memory("你還記得我的名字嗎？", session_id)
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

#### 🤖 Flowise查詢回應
```json
{
    "text": "有效圖面是指經工程部正式發行的零件圖，須蓋有檢驗章、檢驗工具章、公差章、工程部主管審核章及發行版本、工程部發行章。\n\n📷 相關圖片：\n1. https://jh-expert-agent.s3.ap-northeast-1.amazonaws.com/圖面識別教材_PDF_page_1.png",
    "question": "什麼是有效圖面？",
    "chatId": "chat_123",
    "sessionId": "session_chat_123_1720012345",
    "chatMessageId": "uuid-generated-id"
}
```

#### 💬 記憶聊天回應
```json
{
    "response": "你好小明！很高興認識你。我是專業的品管教育訓練講師助手，可以幫你學習圖面識別相關知識。",
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
   - 自動提取文字和圖片
   - GPT-4o視覺分析技術圖面
   - 自動向量化並儲存到Qdrant

2. **智能問答** (`/query`, `/chat`)
   - Flowise整合的專用查詢API
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
- **高效向量檢索**: 基於Qdrant的語義搜尋
- **多模態處理**: 文字+圖片的綜合分析
- **雲端整合**: AWS S3圖片儲存服務
- **記憶功能**: 智能會話記憶管理
- **企業級**: RESTful API設計，支援第三方整合

### 🌐 部署資訊
- **服務端口**: 8006
- **API根路徑**: `/api/v1/JH`
- **文檔地址**: `/docs` (Swagger UI)
- **健康檢查**: `/health`

---

*最後更新: 2025-07-04*
