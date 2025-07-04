"""
PDF文件處理器 - 將PDF拆解成結構化段落並添加metadata
專為教學型RAG chatbot設計，支援圖片視覺分析
"""

import json
import re
import base64
import io
import os
import uuid
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import pdfplumber
import PyPDF2
from pathlib import Path
import logging
from openai import OpenAI
from config import Config
import fitz  # PyMuPDF for image extraction

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """文件段落數據結構"""
    page_num: int
    topic: str
    sub_topic: str
    content: str
    content_type: str  # 'definition', 'procedure', 'symbol', 'example', 'table'
    keywords: List[str]
    difficulty_level: str  # 'basic', 'intermediate', 'advanced'
    chunk_id: str

@dataclass
class VisionDocumentChunk(DocumentChunk):
    """包含視覺分析的文件段落數據結構"""
    has_images: bool = False
    image_analysis: str = ""
    technical_symbols: List[str] = None
    image_path: str = ""  # 圖片檔案路徑

    def __post_init__(self):
        if self.technical_symbols is None:
            self.technical_symbols = []
    
class PDFProcessor:
    """PDF處理器 - 專為教學內容優化，支援圖片視覺分析"""

    def __init__(self, enable_vision_analysis: bool = True):
        self.enable_vision_analysis = enable_vision_analysis

        # 生成唯一的處理會話 ID，避免 chunk_id 重複
        self.session_id = str(uuid.uuid4())[:8]  # 使用前8位作為簡短標識
        self.timestamp = str(int(time.time()))[-6:]  # 使用時間戳後6位

        # 初始化 OpenAI 客戶端（用於圖片分析）
        if self.enable_vision_analysis:
            api_key = Config.OPENAI_API_KEY
            if api_key and api_key != "your_openai_api_key_here":
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("已啟用 GPT-4o 視覺分析功能")
            else:
                self.enable_vision_analysis = False
                logger.warning("未設定 OpenAI API Key，停用視覺分析功能")

        # 定義主題分類規則
        self.topic_patterns = {
            "零件圖": ["零件圖", "零件", "供應商", "IQC"],
            "成品圖": ["成品圖", "成品", "組裝", "BOM"],
            "圖面符號": ["符號", "Φ", "直徑", "厚度", "公差", "單位"],
            "線位圖": ["線位圖", "PIN", "連接器", "電路"],
            "圖面有效性": ["有效圖面", "檢驗章", "審核章", "發行版本"],
            "公差標準": ["公差", "Max", "Min", "標準", "規格"]
        }
        
        # 內容類型識別規則
        self.content_type_patterns = {
            "definition": ["是什麼", "定義", "意思", "含義"],
            "procedure": ["步驟", "流程", "如何", "方法", "程序"],
            "symbol": ["符號", "代表", "表示", "標記"],
            "example": ["例如", "範例", "舉例", "如下"],
            "table": ["表格", "列表", "清單", "對照"]
        }
        
        # 關鍵字提取規則
        self.keyword_patterns = [
            r"[A-Z]{2,}",  # 大寫縮寫 (如 IQC, BOM, PIN)
            r"Φ\d*",       # 直徑符號
            r"[A-Z]+\d+",  # 字母+數字組合
            r"[\u4e00-\u9fff]{2,4}圖",  # 中文+圖
        ]

    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict]:
        """從PDF提取文字內容"""
        try:
            # 檢查文件是否存在
            if not Path(pdf_path).exists():
                logger.error(f"PDF文件不存在: {pdf_path}")
                return []
            
            logger.info(f"正在讀取PDF文件: {pdf_path}")
            pages_data = []
            
            # 使用 pdfplumber 提取文字（更好的文字提取效果）
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    # 提取文字
                    text = page.extract_text()
                    
                    if text and text.strip():
                        # 按行分割文字
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        
                        pages_data.append({
                            "page_num": i + 1,
                            "raw_text": text,
                            "text_blocks": lines
                        })
                    else:
                        logger.warning(f"第 {i+1} 頁沒有提取到文字內容")
                
            logger.info(f"成功提取 {len(pages_data)} 頁的文字內容")
            return pages_data
            
        except Exception as e:
            logger.error(f"PDF文字提取失敗: {e}")
            logger.error(f"文件路徑: {pdf_path}")
            logger.error(f"文件存在: {Path(pdf_path).exists()}")
            return []

    def identify_topic(self, text: str) -> str:
        """識別文字內容的主題分類"""
        text_lower = text.lower()
        
        for topic, keywords in self.topic_patterns.items():
            if any(keyword in text for keyword in keywords):
                return topic
        
        return "其他"

    def identify_content_type(self, text: str) -> str:
        """識別內容類型"""
        text_lower = text.lower()
        
        # 檢查是否包含表格結構
        if ":" in text and len(text.split(":")) > 2:
            return "table"
        
        for content_type, patterns in self.content_type_patterns.items():
            if any(pattern in text for pattern in patterns):
                return content_type
        
        return "definition"

    def extract_keywords(self, text: str) -> List[str]:
        """提取關鍵字"""
        keywords = []
        
        for pattern in self.keyword_patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)
        
        # 移除重複並過濾
        keywords = list(set(keywords))
        keywords = [kw for kw in keywords if len(kw) > 1]
        
        return keywords

    def has_images_on_page(self, pdf_path: str, page_num: int) -> bool:
        """檢查指定頁面是否包含圖片"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]  # fitz 使用 0-based 索引
            image_list = page.get_images()
            doc.close()
            return len(image_list) > 0
        except Exception as e:
            logger.warning(f"檢查頁面 {page_num} 圖片時發生錯誤: {e}")
            return False

    def extract_and_save_page_image(self, pdf_path: str, page_num: int, output_dir: str = "images") -> Optional[str]:
        """提取頁面圖片並儲存到本地檔案"""
        try:
            # 確保輸出目錄存在
            os.makedirs(output_dir, exist_ok=True)

            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]

            # 將頁面渲染為圖片
            mat = fitz.Matrix(2.0, 2.0)  # 2x 縮放以提高品質
            pix = page.get_pixmap(matrix=mat)

            # 生成檔案名稱
            pdf_name = Path(pdf_path).stem
            image_filename = f"{pdf_name}_page_{page_num}.png"
            image_path = os.path.join(output_dir, image_filename)

            # 儲存圖片到檔案
            pix.save(image_path)

            doc.close()
            logger.info(f"頁面 {page_num} 圖片已儲存至: {image_path}")
            return image_path

        except Exception as e:
            logger.error(f"提取並儲存頁面 {page_num} 圖片時發生錯誤: {e}")
            return None

    def extract_page_image_base64(self, pdf_path: str, page_num: int) -> Optional[str]:
        """提取頁面圖片並轉換為 base64 編碼（用於即時顯示）"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]

            # 將頁面渲染為圖片
            mat = fitz.Matrix(2.0, 2.0)  # 2x 縮放以提高品質
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")

            # 轉換為 base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')

            doc.close()
            return img_base64

        except Exception as e:
            logger.error(f"提取頁面 {page_num} 圖片時發生錯誤: {e}")
            return None

    def analyze_page_with_vision(self, pdf_path: str, page_num: int, text_content: str) -> Dict[str, Any]:
        """使用 GPT-4o 分析包含圖片的頁面"""
        if not self.enable_vision_analysis:
            return {"has_images": False, "image_analysis": "", "technical_symbols": []}

        # 檢查是否有圖片
        if not self.has_images_on_page(pdf_path, page_num):
            return {"has_images": False, "image_analysis": "", "technical_symbols": []}

        # 提取頁面圖片
        img_base64 = self.extract_page_image_base64(pdf_path, page_num)
        if not img_base64:
            return {"has_images": True, "image_analysis": "圖片提取失敗", "technical_symbols": []}

        try:
            # 使用 GPT-4o 分析圖片
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""請分析這個技術圖面頁面，這是品管教育訓練教材的一部分。

頁面文字內容：
{text_content}

請提供：
1. 圖面中的技術符號和標記（如 Φ、尺寸標註、公差符號等）
2. 圖面類型（零件圖、成品圖、線位圖等）
3. 重要的視覺元素描述
4. 與文字內容的關聯性

請用繁體中文回答，重點關注技術圖面的教學要點。"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            analysis = response.choices[0].message.content

            # 提取技術符號
            technical_symbols = self._extract_technical_symbols_from_analysis(analysis)

            logger.info(f"頁面 {page_num} 視覺分析完成")
            return {
                "has_images": True,
                "image_analysis": analysis,
                "technical_symbols": technical_symbols
            }

        except Exception as e:
            logger.error(f"頁面 {page_num} 視覺分析失敗: {e}")
            return {
                "has_images": True,
                "image_analysis": f"視覺分析失敗: {str(e)}",
                "technical_symbols": []
            }

    def _extract_technical_symbols_from_analysis(self, analysis: str) -> List[str]:
        """從分析結果中提取技術符號"""
        symbols = []

        # 常見的技術符號模式
        symbol_patterns = [
            r"Φ\d*",  # 直徑符號
            r"[A-Z]+\d+",  # 字母+數字
            r"±\d*\.?\d*",  # 公差符號
            r"MAX|MIN|max|min",  # 最大最小值
            r"[A-Z]{2,}",  # 大寫縮寫
        ]

        for pattern in symbol_patterns:
            matches = re.findall(pattern, analysis)
            symbols.extend(matches)

        # 移除重複並過濾
        symbols = list(set(symbols))
        symbols = [s for s in symbols if len(s) > 1]

        return symbols

    def determine_difficulty(self, text: str, keywords: List[str]) -> str:
        """判斷難度等級"""
        # 基於關鍵字數量和內容複雜度判斷
        if len(keywords) > 5 or "公差" in text or "規格" in text:
            return "advanced"
        elif len(keywords) > 2 or "符號" in text:
            return "intermediate"
        else:
            return "basic"

    def split_content_into_chunks(self, page_data: Dict, pdf_path: str = None) -> List[DocumentChunk]:
        """將頁面內容拆分成結構化段落，支援視覺分析"""
        chunks = []
        page_num = page_data["page_num"]
        text_blocks = page_data["text_blocks"]
        raw_text = page_data.get("raw_text", "")

        # 檢查是否需要進行視覺分析
        vision_analysis = {"has_images": False, "image_analysis": "", "technical_symbols": []}
        if pdf_path and self.enable_vision_analysis:
            vision_analysis = self.analyze_page_with_vision(pdf_path, page_num, raw_text)

        # 合併相關的文字塊
        merged_blocks = self._merge_related_blocks(text_blocks)

        for i, block in enumerate(merged_blocks):
            if len(block.strip()) < 10:  # 跳過太短的內容
                continue

            # 識別主題和子主題
            topic = self.identify_topic(block)

            # 嘗試從文字中提取子主題
            lines = block.split('\n')
            sub_topic = lines[0] if lines else f"段落{i+1}"
            content = block

            # 如果第一行看起來像標題，分離標題和內容
            if len(lines) > 1 and len(lines[0]) < 30:
                sub_topic = lines[0]
                content = '\n'.join(lines[1:])

            # 如果有視覺分析結果，整合到內容中
            if vision_analysis["has_images"] and vision_analysis["image_analysis"]:
                content += f"\n\n【圖面分析】\n{vision_analysis['image_analysis']}"

            # 提取metadata
            content_type = self.identify_content_type(content)
            keywords = self.extract_keywords(content)

            # 整合視覺分析中的技術符號
            if vision_analysis["technical_symbols"]:
                keywords.extend(vision_analysis["technical_symbols"])
                keywords = list(set(keywords))  # 移除重複

            difficulty = self.determine_difficulty(content, keywords)

            # 根據是否有圖片選擇適當的數據結構
            if vision_analysis["has_images"]:
                # 儲存頁面圖片到檔案
                image_path = ""
                if pdf_path:
                    image_path = self.extract_and_save_page_image(pdf_path, page_num) or ""

                chunk = VisionDocumentChunk(
                    page_num=page_num,
                    topic=topic,
                    sub_topic=sub_topic.strip(),
                    content=content.strip(),
                    content_type=content_type,
                    keywords=keywords,
                    difficulty_level=difficulty,
                    chunk_id=f"{self.session_id}_{self.timestamp}_page_{page_num}_chunk_{i+1}",
                    has_images=True,
                    image_analysis=vision_analysis["image_analysis"],
                    technical_symbols=vision_analysis["technical_symbols"],
                    image_path=image_path
                )
            else:
                chunk = DocumentChunk(
                    page_num=page_num,
                    topic=topic,
                    sub_topic=sub_topic.strip(),
                    content=content.strip(),
                    content_type=content_type,
                    keywords=keywords,
                    difficulty_level=difficulty,
                    chunk_id=f"{self.session_id}_{self.timestamp}_page_{page_num}_chunk_{i+1}"
                )

            chunks.append(chunk)

        return chunks

    def _merge_related_blocks(self, text_blocks: List[str]) -> List[str]:
        """合併相關的文字塊"""
        if not text_blocks:
            return []
        
        merged = []
        current_block = text_blocks[0]
        
        for i in range(1, len(text_blocks)):
            next_block = text_blocks[i]
            
            # 如果下一個塊很短，或者看起來是當前塊的延續，就合併
            if (len(next_block) < 50 or 
                not next_block[0].isupper() or
                current_block.endswith(('，', '、', '：', '；'))):
                current_block += '\n' + next_block
            else:
                merged.append(current_block)
                current_block = next_block
        
        merged.append(current_block)
        return merged

    def process_pdf(self, pdf_path: str, output_path: str = "processed_chunks.jsonl") -> List[DocumentChunk]:
        """完整處理PDF文件，包含視覺分析"""
        logger.info(f"開始處理PDF文件: {pdf_path}")

        if self.enable_vision_analysis:
            logger.info("已啟用視覺分析功能，將分析包含圖片的頁面")

        # 提取文字
        pages_data = self.extract_text_from_pdf(pdf_path)
        if not pages_data:
            return []

        # 拆分成段落（傳遞 PDF 路徑以支援視覺分析）
        all_chunks = []
        for page_data in pages_data:
            chunks = self.split_content_into_chunks(page_data, pdf_path)
            all_chunks.extend(chunks)

        # 保存結果
        self.save_chunks(all_chunks, output_path)

        # 統計視覺分析結果
        vision_chunks = [c for c in all_chunks if hasattr(c, 'has_images') and c.has_images]
        logger.info(f"處理完成，共生成 {len(all_chunks)} 個文件段落")
        if vision_chunks:
            logger.info(f"其中 {len(vision_chunks)} 個段落包含圖片分析")

        return all_chunks

    def save_chunks(self, chunks: List[DocumentChunk], output_path: str):
        """保存處理結果為JSONL格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                json.dump(asdict(chunk), f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"文件段落已保存至: {output_path}")

    def load_chunks(self, file_path: str) -> List[DocumentChunk]:
        """從JSONL文件載入段落數據"""
        chunks = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())

                # 檢查是否包含圖片資訊
                if 'has_images' in data and data['has_images']:
                    # 創建 VisionDocumentChunk
                    chunk = VisionDocumentChunk(**data)
                else:
                    # 創建普通的 DocumentChunk，移除可能存在的視覺相關欄位
                    chunk_data = {k: v for k, v in data.items()
                                 if k not in ['has_images', 'image_analysis', 'technical_symbols', 'image_path']}
                    chunk = DocumentChunk(**chunk_data)

                chunks.append(chunk)
        return chunks

if __name__ == "__main__":
    # 使用範例
    processor = PDFProcessor()
    
    # 處理PDF文件
    pdf_path = "圖面識別教材.pdf"  # 假設已轉換為PDF
    chunks = processor.process_pdf(pdf_path)
    
    # 顯示處理結果統計
    if chunks:
        topics = {}
        for chunk in chunks:
            topics[chunk.topic] = topics.get(chunk.topic, 0) + 1
        
        print("\n=== 處理結果統計 ===")
        print(f"總段落數: {len(chunks)}")
        print("主題分布:")
        for topic, count in topics.items():
            print(f"  {topic}: {count} 段")
        
        print("\n=== 前3個段落範例 ===")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n段落 {i+1}:")
            print(f"  頁面: {chunk.page_num}")
            print(f"  主題: {chunk.topic}")
            print(f"  子主題: {chunk.sub_topic}")
            print(f"  內容類型: {chunk.content_type}")
            print(f"  關鍵字: {chunk.keywords}")
            print(f"  內容: {chunk.content[:100]}...")
