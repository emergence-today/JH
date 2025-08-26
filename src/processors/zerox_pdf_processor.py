"""
基於 Zerox 的PDF文件處理器 - 支援視覺AI分析和成本計算
專為教學型RAG chatbot設計，提供精確的成本報告
"""

import json
import re
import os
import uuid
import time
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from dotenv import load_dotenv

# 載入環境變量
load_dotenv()

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ZeroxDocumentChunk:
    """Zerox處理的文檔段落"""
    page_num: int
    topic: str
    sub_topic: str
    content: str
    content_type: str
    keywords: List[str]
    difficulty_level: str
    chunk_id: str
    
    # Zerox特有的字段
    has_images: bool = True  # Zerox處理的都包含圖片
    image_path: str = ""  # 頁面圖片路徑
    image_analysis: str = ""  # AI圖片分析結果
    technical_symbols: List[str] = None
    
    # 成本追蹤字段
    input_tokens: int = 0
    output_tokens: int = 0
    processing_cost: float = 0.0
    model_used: str = ""

    def __post_init__(self):
        if self.technical_symbols is None:
            self.technical_symbols = []

@dataclass
class ProcessingCostReport:
    """處理成本報告"""
    total_pages: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    model_used: str
    processing_time: float
    cost_per_page: float
    estimated_full_document_cost: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ZeroxPDFProcessor:
    """基於 Zerox 的PDF處理器"""
    
    # 定價表 (USD per 1M tokens)
    MODEL_PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00}
    }
    
    # 主題分類模式
    topic_patterns = {
        "成品圖": ["成品", "產品", "完成品", "最終", "結果"],
        "圖面符號": ["符號", "標記", "記號", "圖例", "legend"],
        "線位圖": ["線位", "位置", "配置", "佈局", "layout"],
        "製程流程": ["流程", "步驟", "程序", "工序", "製程"],
        "品質標準": ["品質", "標準", "規格", "要求", "quality"],
        "檢驗方法": ["檢驗", "測試", "檢查", "驗證", "inspection"],
        "其他": []
    }
    
    # 內容類型模式
    content_type_patterns = {
        "procedure": ["步驟", "程序", "流程", "方法", "操作"],
        "definition": ["定義", "說明", "解釋", "概念", "意思"],
        "table": ["表格", "列表", "清單", "項目", "規格"],
        "diagram": ["圖表", "圖形", "示意圖", "流程圖", "架構圖"],
        "image": ["圖片", "照片", "影像", "截圖", "畫面"]
    }

    def __init__(self, model: str = None, max_pages: Optional[int] = None):
        """
        初始化 Zerox PDF 處理器

        Args:
            model: 使用的AI模型 (None時使用Config.OPENAI_MODEL)
            max_pages: 最大處理頁數（用於成本控制）
        """
        from config.config import Config
        self.model = model or Config.ZEROX_MODEL
        self.max_pages = max_pages
        
        # 生成唯一的處理會話 ID
        self.session_id = str(uuid.uuid4())[:8]
        self.timestamp = str(int(time.time()))[-6:]
        
        # 檢查API Key - 支援 Bedrock Claude 和 OpenAI
        if 'bedrock' in self.model.lower():
            # 使用 Bedrock Claude，檢查 AWS 憑證
            from config.config import Config
            self.aws_access_key = Config.AWS_ACCESS_KEY_ID
            self.aws_secret_key = Config.AWS_SECRET_ACCESS_KEY
            self.aws_region = Config.AWS_REGION
            if not self.aws_access_key or not self.aws_secret_key:
                raise ValueError("使用 Bedrock Claude 請在 .env 文件中設置 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY")
            logger.info(f"使用 Bedrock Claude 模型: {self.model}")
            logger.info(f"AWS 區域: {self.aws_region}")
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError("請設置 OPENAI_API_KEY 環境變量")
        
        # 成本追蹤
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.processing_start_time = None
        
        logger.info(f"ZeroxPDFProcessor 初始化完成 - 模型: {model}")
        if max_pages:
            logger.info(f"設置最大處理頁數: {max_pages}")

    def is_blank_page(self, pdf_path: str, page_num: int, threshold: float = 0.95) -> bool:
        """
        檢測PDF頁面是否為空白頁

        Args:
            pdf_path: PDF文件路徑
            page_num: 頁面編號 (1-based)
            threshold: 空白像素比例閾值 (0.95 = 95%空白認為是空白頁)

        Returns:
            bool: True表示是空白頁
        """
        try:
            import fitz  # PyMuPDF
            import numpy as np
            from PIL import Image
            import io

            doc = fitz.open(pdf_path)
            if page_num > len(doc):
                doc.close()
                return True

            page = doc[page_num - 1]  # PyMuPDF uses 0-based indexing

            # 方法1: 檢查文字內容
            text_content = page.get_text().strip()
            if len(text_content) > 10:  # 如果有超過10個字符，不是空白頁
                doc.close()
                return False

            # 方法2: 檢查圖像內容
            pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0))  # 低解析度快速檢測
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # 轉換為灰度圖像
            gray_img = img.convert('L')
            img_array = np.array(gray_img)

            # 計算空白像素比例 (接近白色的像素)
            white_pixels = np.sum(img_array > 240)  # 240以上認為是白色
            total_pixels = img_array.size
            white_ratio = white_pixels / total_pixels

            doc.close()

            is_blank = white_ratio > threshold
            if is_blank:
                logger.info(f"檢測到空白頁 {page_num}: 空白比例 {white_ratio:.2%}")

            return is_blank

        except ImportError:
            logger.warning("PyMuPDF 或 PIL 未安裝，無法檢測空白頁")
            return False
        except Exception as e:
            logger.warning(f"檢測空白頁失敗: {e}")
            return False

    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """計算API調用成本"""
        if model not in self.MODEL_PRICING:
            logger.warning(f"未知模型 {model}，使用 gpt-4o 定價")
            model = "gpt-4o"
        
        pricing = self.MODEL_PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost

    async def process_pdf_with_zerox(self, pdf_path: str, output_dir: str = "outputs/images/zerox_output") -> Dict[str, Any]:
        """使用 Zerox 處理PDF文件"""
        try:
            from pyzerox import zerox

            logger.info(f"開始使用 Zerox 處理PDF: {pdf_path}")
            self.processing_start_time = time.time()

            # 確保輸出目錄存在
            os.makedirs(output_dir, exist_ok=True)

            # 檢查是否已有對應的 markdown 文件
            pdf_name = Path(pdf_path).stem
            expected_md_file = os.path.join(output_dir, f"{pdf_name}.md")

            if os.path.exists(expected_md_file):
                logger.info(f"發現已存在的 markdown 文件，跳過 Zerox 處理: {expected_md_file}")

                # 讀取現有的 markdown 文件並構造結果
                with open(expected_md_file, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                # 構造模擬的 Zerox 結果結構
                from types import SimpleNamespace

                # 分析 markdown 內容來估算頁數和 token 數
                estimated_pages = max(1, markdown_content.count('\n\n') // 10)  # 粗略估算頁數
                estimated_input_tokens = len(markdown_content.split()) * 1.3  # 粗略估算
                estimated_output_tokens = len(markdown_content.split())

                # 創建模擬的頁面結構
                pages = []
                page_sections = markdown_content.split('\n\n')
                current_page = 1

                for i in range(0, len(page_sections), max(1, len(page_sections) // estimated_pages)):
                    page_content = '\n\n'.join(page_sections[i:i + max(1, len(page_sections) // estimated_pages)])
                    if page_content.strip():
                        page = SimpleNamespace()
                        page.page = current_page
                        page.content = page_content.strip()
                        pages.append(page)
                        current_page += 1

                # 構造結果對象
                result = SimpleNamespace()
                result.pages = pages
                result.input_tokens = int(estimated_input_tokens)
                result.output_tokens = int(estimated_output_tokens)

                logger.info(f"從現有 markdown 文件載入: {len(pages)} 頁")
                return result

            # 設置處理頁數並過濾空白頁
            select_pages = None
            if self.max_pages:
                all_pages = list(range(1, self.max_pages + 1))
            else:
                # 獲取PDF總頁數
                try:
                    import fitz
                    doc = fitz.open(pdf_path)
                    total_pages = len(doc)
                    doc.close()
                    all_pages = list(range(1, total_pages + 1))
                except:
                    all_pages = None

            # 過濾空白頁
            if all_pages:
                non_blank_pages = []
                blank_pages = []

                logger.info(f"開始檢測空白頁，總頁數: {len(all_pages)}")

                for page_num in all_pages:
                    if self.is_blank_page(pdf_path, page_num):
                        blank_pages.append(page_num)
                    else:
                        non_blank_pages.append(page_num)

                if blank_pages:
                    logger.info(f"發現 {len(blank_pages)} 個空白頁，將跳過: {blank_pages}")

                select_pages = non_blank_pages if non_blank_pages else None
                logger.info(f"實際處理頁數: {len(non_blank_pages) if non_blank_pages else 0}")

            if not select_pages:
                logger.warning("沒有找到非空白頁面，跳過處理")
                return None

            # 使用 Zerox 處理PDF (只處理非空白頁)
            if 'bedrock' in self.model.lower():
                # 使用 Bedrock Claude - 按照 LiteLLM 格式
                # 設置 AWS 環境變量供 LiteLLM 使用
                os.environ['AWS_ACCESS_KEY_ID'] = self.aws_access_key
                os.environ['AWS_SECRET_ACCESS_KEY'] = self.aws_secret_key
                os.environ['AWS_REGION'] = self.aws_region

                logger.info(f"使用 Bedrock Claude 模型: {self.model}")

                result = await zerox(
                    file_path=pdf_path,
                    model=self.model,  # 使用 LiteLLM 格式
                    output_dir=output_dir,
                    select_pages=select_pages,
                    concurrency=2,  # 控制並發數以避免API限制
                    cleanup=False,  # 保留臨時文件
                    maintain_format=False  # 避免與 select_pages 衝突
                    # 使用 Zerox 預設系統提示詞，不指定 custom_system_prompt
                )
            else:
                # 使用 OpenAI
                result = await zerox(
                    file_path=pdf_path,
                    model=self.model,
                    output_dir=output_dir,
                    select_pages=select_pages,
                    concurrency=2,  # 控制並發數以避免API限制
                    cleanup=False,  # 保留臨時文件
                    maintain_format=False  # 避免與 select_pages 衝突
                )
            
            if not result:
                raise Exception("Zerox 處理失敗，未返回結果")
            
            # 更新成本統計
            self.total_input_tokens += result.input_tokens
            self.total_output_tokens += result.output_tokens
            self.total_cost += self.calculate_cost(
                result.input_tokens, 
                result.output_tokens, 
                self.model
            )
            
            logger.info(f"Zerox 處理完成:")
            logger.info(f"  - 處理頁數: {len(result.pages)}")
            logger.info(f"  - 輸入tokens: {result.input_tokens:,}")
            logger.info(f"  - 輸出tokens: {result.output_tokens:,}")
            logger.info(f"  - 成本: ${self.total_cost:.4f} USD")
            
            # 手動生成PDF頁面圖片
            await self.generate_pdf_images(pdf_path, output_dir, select_pages)

            return result

        except ImportError:
            raise Exception("請先安裝 py-zerox: pip install py-zerox")
        except Exception as e:
            logger.error(f"Zerox 處理失敗: {e}")
            raise

    async def generate_pdf_images(self, pdf_path: str, output_dir: str, select_pages: List[int] = None):
        """手動生成PDF頁面圖片 - 避免重複生成"""
        try:
            import fitz  # PyMuPDF

            pdf_name = Path(pdf_path).stem
            doc = fitz.open(pdf_path)

            pages_to_process = select_pages if select_pages else range(1, len(doc) + 1)
            generated_count = 0
            skipped_count = 0

            for page_num in pages_to_process:
                if page_num <= len(doc):
                    # 檢查圖片是否已存在
                    image_filename = f"{pdf_name}_page_{page_num}.png"
                    image_path = os.path.join(output_dir, image_filename)

                    if os.path.exists(image_path):
                        logger.info(f"頁面圖片已存在，跳過: {image_path}")
                        skipped_count += 1
                        continue

                    page = doc[page_num - 1]  # PyMuPDF uses 0-based indexing

                    # 生成高解析度圖片
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)

                    # 保存圖片
                    pix.save(image_path)
                    generated_count += 1

                    logger.info(f"生成頁面圖片: {image_path}")

            doc.close()
            logger.info(f"完成PDF圖片生成，共 {len(pages_to_process)} 頁 (新生成: {generated_count}, 跳過: {skipped_count})")

        except ImportError:
            logger.warning("PyMuPDF 未安裝，無法生成PDF圖片。請安裝: pip install PyMuPDF")
        except Exception as e:
            logger.error(f"生成PDF圖片失敗: {e}")

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
        if "|" in text or "---" in text:
            return "table"
        
        for content_type, patterns in self.content_type_patterns.items():
            if any(pattern in text for pattern in patterns):
                return content_type
        
        return "definition"

    def extract_keywords(self, text: str) -> List[str]:
        """提取關鍵字"""
        # 移除標點符號並分割
        cleaned_text = re.sub(r'[^\w\s]', ' ', text)
        words = cleaned_text.split()
        
        # 過濾長度和常見詞
        keywords = []
        common_words = {'的', '是', '在', '有', '和', '與', '或', '但', '如果', '因為', '所以'}
        
        for word in words:
            if len(word) >= 2 and word not in common_words:
                keywords.append(word)
        
        # 返回前10個關鍵字
        return list(set(keywords))[:10]

    def determine_difficulty_level(self, text: str) -> str:
        """判斷難度等級"""
        # 基於文字複雜度和技術術語密度
        technical_terms = ['製程', '品質', '檢驗', '標準', '規格', '流程', '工序']
        
        tech_count = sum(1 for term in technical_terms if term in text)
        text_length = len(text)
        
        if tech_count >= 3 or text_length > 500:
            return "advanced"
        elif tech_count >= 1 or text_length > 200:
            return "intermediate"
        else:
            return "basic"

    async def convert_zerox_to_chunks(self, zerox_result, pdf_path: str, output_dir: str = "zerox_output") -> List[ZeroxDocumentChunk]:
        """將 Zerox 結果轉換為文檔段落 - 一頁一個chunk"""
        chunks = []
        
        pdf_name = Path(pdf_path).stem

        for page in zerox_result.pages:
            # 使用整頁內容作為一個chunk（一頁一個chunk）
            page_content = page.content.strip()

            if len(page_content) < 10:  # 跳過內容太少的頁面
                continue

            # 生成唯一ID - 一頁一個chunk
            chunk_id = f"{self.session_id}_{self.timestamp}_page_{page.page}"

            # 使用GPT生成豐富的metadata - 支援緩存
            metadata = await self.generate_enhanced_metadata(page_content, page.page, pdf_path)

            topic = metadata.get('topic', self.identify_topic(page_content))
            content_type = metadata.get('content_type', self.identify_content_type(page_content))
            keywords = metadata.get('keywords', self.extract_keywords(page_content))
            difficulty = metadata.get('difficulty_level', self.determine_difficulty_level(page_content))
            sub_topic = metadata.get('sub_topic', self.generate_sub_topic(page_content, topic))

            # 計算該頁面的成本分攤
            page_cost = self.calculate_cost(
                zerox_result.input_tokens // len(zerox_result.pages),
                zerox_result.output_tokens // len(zerox_result.pages),
                self.model
            )

            # 構建圖片路徑 - 使用相對路徑便於Web訪問
            image_filename = f"{pdf_name}_page_{page.page}.png"
            image_path = f"{output_dir}/{image_filename}"  # 相對路徑，便於Web服務訪問

            chunk = ZeroxDocumentChunk(
                page_num=page.page,
                topic=topic,
                sub_topic=sub_topic,
                content=page_content,  # 使用整頁內容
                content_type=content_type,
                keywords=keywords,
                difficulty_level=difficulty,
                chunk_id=chunk_id,
                has_images=True,
                image_path=image_path,  # 完整的圖片路徑
                image_analysis=page_content,  # Zerox的分析結果就是頁面內容
                technical_symbols=metadata.get('technical_symbols', self.extract_technical_symbols(page_content)),
                input_tokens=zerox_result.input_tokens // len(zerox_result.pages),
                output_tokens=zerox_result.output_tokens // len(zerox_result.pages),
                processing_cost=page_cost,
                model_used=self.model
            )
            
            # 添加檔案名稱資訊
            chunk.source_filename = pdf_name

            # 添加額外的metadata到chunk
            if hasattr(chunk, 'metadata'):
                chunk.metadata = metadata
            else:
                # 如果chunk沒有metadata屬性，我們將其添加為動態屬性
                for key, value in metadata.items():
                    if not hasattr(chunk, key):
                        setattr(chunk, f"meta_{key}", value)

            chunks.append(chunk)
        
        return chunks

    def generate_sub_topic(self, content: str, topic: str) -> str:
        """生成子主題"""
        # 提取內容的前50個字符作為子主題
        sub_topic = content[:50].replace('\n', ' ').strip()
        if len(sub_topic) < len(content):
            sub_topic += "..."
        return sub_topic

    def extract_technical_symbols(self, text: str) -> List[str]:
        """提取技術符號"""
        # 查找常見的技術符號和縮寫
        symbols = []
        
        # 查找大寫字母組合（可能是縮寫）
        abbreviations = re.findall(r'\b[A-Z]{2,}\b', text)
        symbols.extend(abbreviations)
        
        # 查找數字+單位的組合
        units = re.findall(r'\d+(?:\.\d+)?[a-zA-Z]+', text)
        symbols.extend(units)
        
        return list(set(symbols))[:5]  # 返回前5個

    def generate_cost_report(self, total_pages_in_pdf: int, processing_time: float) -> ProcessingCostReport:
        """生成詳細的成本報告"""
        pages_processed = len([chunk for chunk in getattr(self, 'chunks', [])]) // 3  # 估算
        
        cost_per_page = self.total_cost / pages_processed if pages_processed > 0 else 0
        
        # 估算處理整個文檔的成本
        estimated_full_cost = cost_per_page * total_pages_in_pdf
        
        return ProcessingCostReport(
            total_pages=pages_processed,
            total_input_tokens=self.total_input_tokens,
            total_output_tokens=self.total_output_tokens,
            total_cost_usd=self.total_cost,
            model_used=self.model,
            processing_time=processing_time,
            cost_per_page=cost_per_page,
            estimated_full_document_cost=estimated_full_cost
        )

    def save_chunks(self, chunks: List[ZeroxDocumentChunk], output_path: str):
        """保存處理結果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(asdict(chunk), ensure_ascii=False) + '\n')
        
        logger.info(f"文件段落已保存至: {output_path}")

    async def process_pdf(self, pdf_path: str, output_path: str = "outputs/embeddings/zerox_processed_chunks.jsonl") -> List[ZeroxDocumentChunk]:
        """完整處理PDF文件"""
        logger.info(f"開始使用 Zerox 處理PDF文件: {pdf_path}")

        # 檢查文件是否存在
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        try:
            # 設置輸出目錄 - 直接使用 outputs 結構
            output_dir = "outputs/images/zerox_output"

            # 使用 Zerox 處理PDF
            zerox_result = await self.process_pdf_with_zerox(pdf_path, output_dir)

            # 轉換為文檔段落 - 傳入output_dir以正確設置圖片路徑
            chunks = await self.convert_zerox_to_chunks(zerox_result, pdf_path, output_dir)
            
            # 保存結果
            self.save_chunks(chunks, output_path)
            
            # 計算處理時間
            processing_time = time.time() - self.processing_start_time
            
            # 生成成本報告
            cost_report = self.generate_cost_report(75, processing_time)  # 假設75頁
            
            # 保存成本報告
            cost_report_path = output_path.replace('.jsonl', '_cost_report.json')
            with open(cost_report_path, 'w', encoding='utf-8') as f:
                json.dump(cost_report.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"處理完成，共生成 {len(chunks)} 個文件段落")
            logger.info(f"成本報告已保存至: {cost_report_path}")
            
            # 存儲chunks供其他方法使用
            self.chunks = chunks
            
            return chunks

        except Exception as e:
            logger.error(f"PDF處理失敗: {e}")
            raise

    async def generate_enhanced_metadata(self, content: str, page_num: int, pdf_path: str = None) -> dict:
        """使用GPT生成增強的metadata - 支援緩存檢查"""
        try:
            # 檢查是否有緩存的 metadata
            if pdf_path:
                pdf_name = Path(pdf_path).stem
                metadata_cache_dir = "outputs/metadata_cache"
                os.makedirs(metadata_cache_dir, exist_ok=True)

                cache_file = os.path.join(metadata_cache_dir, f"{pdf_name}_page_{page_num}_metadata.json")

                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cached_metadata = json.load(f)
                        logger.info(f"載入頁面 {page_num} 的緩存metadata")
                        return cached_metadata
                    except Exception as e:
                        logger.warning(f"載入緩存metadata失敗: {e}")

            prompt = f"""
請分析以下技術文件內容，並生成結構化的metadata。這是第{page_num}頁的內容：

內容：
{content[:2000]}  # 限制長度避免token過多

請以JSON格式返回以下metadata：
{{
    "topic": "主要主題（如：線束設計、材料規格、製程工藝等）",
    "sub_topic": "具體子主題",
    "content_type": "內容類型（如：specification, procedure, diagram, table, introduction等）",
    "keywords": ["關鍵詞1", "關鍵詞2", "關鍵詞3"],
    "difficulty_level": "難度等級（basic/intermediate/advanced）",
    "technical_symbols": ["技術符號1", "技術符號2"],
    "document_section": "文件章節（如：第一章、附錄A等）",
    "equipment_mentioned": ["提到的設備名稱"],
    "materials_mentioned": ["提到的材料名稱"],
    "processes_mentioned": ["提到的工藝流程"],
    "standards_mentioned": ["提到的標準規範"],
    "measurements_units": ["提到的測量單位"],
    "safety_requirements": ["安全要求"],
    "quality_criteria": ["品質標準"],
    "application_area": "應用領域（如：汽車、電子、工業等）",
    "target_audience": "目標讀者（如：工程師、技術員、管理人員等）",
    "action_items": ["需要執行的動作項目"],
    "related_documents": ["相關文件"],
    "revision_info": "版本信息",
    "importance_level": "重要程度（high/medium/low）"
}}

請確保返回有效的JSON格式。
"""

            # 根據模型類型選擇API
            if 'bedrock' in self.model.lower() or 'claude' in self.model.lower():
                # 使用 Bedrock Claude
                import boto3
                from config.config import Config

                bedrock_runtime = boto3.client(
                    'bedrock-runtime',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region
                )

                # Bedrock Claude 請求格式
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"你是一個專業的技術文件分析專家，擅長從工程和製造文件中提取結構化metadata。\n\n{prompt}"
                        }
                    ]
                }

                response = bedrock_runtime.invoke_model(
                    modelId=Config.BEDROCK_MODEL,
                    body=json.dumps(body)
                )

                response_body = json.loads(response['body'].read())
                metadata_text = response_body['content'][0]['text']

            else:
                # 使用 OpenAI API
                import openai
                from config.config import Config

                client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一個專業的技術文件分析專家，擅長從工程和製造文件中提取結構化metadata。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )

                metadata_text = response.choices[0].message.content

            # 解析JSON回應

            # 嘗試提取JSON部分
            start_idx = metadata_text.find('{')
            end_idx = metadata_text.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_text = metadata_text[start_idx:end_idx]
                metadata = json.loads(json_text)

                # 保存到緩存
                if pdf_path:
                    try:
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)
                        logger.info(f"成功生成並緩存頁面 {page_num} 的增強metadata")
                    except Exception as e:
                        logger.warning(f"保存metadata緩存失敗: {e}")
                        logger.info(f"成功生成頁面 {page_num} 的增強metadata")
                else:
                    logger.info(f"成功生成頁面 {page_num} 的增強metadata")

                return metadata
            else:
                logger.warning(f"無法解析頁面 {page_num} 的metadata JSON")
                return {}

        except Exception as e:
            logger.error(f"生成增強metadata失敗: {e}")
            return {}
