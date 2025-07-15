"""
PDF 處理器 - 基礎版本
用於 main.py 的文件上傳 API
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """文檔段落數據結構"""
    content: str
    page_number: int
    chunk_index: int
    metadata: Dict[str, Any]
    file_path: str
    chunk_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return asdict(self)

@dataclass
class VisionDocumentChunk(DocumentChunk):
    """包含視覺分析的文檔段落"""
    image_description: str = ""
    visual_elements: List[str] = None
    
    def __post_init__(self):
        if self.visual_elements is None:
            self.visual_elements = []

class PDFProcessor:
    """PDF 處理器 - 簡化版本，用於 API 兼容性"""
    
    def __init__(self, enable_vision_analysis: bool = False):
        """
        初始化 PDF 處理器
        
        Args:
            enable_vision_analysis: 是否啟用視覺分析
        """
        self.enable_vision_analysis = enable_vision_analysis
        logger.info(f"PDFProcessor 初始化完成 - 視覺分析: {enable_vision_analysis}")
    
    def process_pdf(self, pdf_path: str, output_path: str = None) -> List[DocumentChunk]:
        """
        處理 PDF 文件 - 簡化版本
        
        Args:
            pdf_path: PDF 文件路徑
            output_path: 輸出路徑（可選）
            
        Returns:
            List[DocumentChunk]: 文檔段落列表
        """
        try:
            logger.info(f"開始處理 PDF: {pdf_path}")
            
            # 使用 Zerox 處理器作為後端
            from src.processors.zerox_pdf_processor import ZeroxPDFProcessor
            
            # 創建 Zerox 處理器實例
            zerox_processor = ZeroxPDFProcessor()
            
            # 同步調用異步方法
            import asyncio
            
            async def _process():
                # 處理 PDF
                result = await zerox_processor.process_pdf_with_zerox(pdf_path)
                if result:
                    # 轉換為段落格式
                    chunks = await zerox_processor.convert_zerox_to_chunks(result, pdf_path)
                    return chunks
                return []
            
            # 運行異步處理
            chunks = asyncio.run(_process())
            
            # 轉換為 DocumentChunk 格式
            document_chunks = []
            for i, chunk in enumerate(chunks):
                doc_chunk = DocumentChunk(
                    content=chunk.content,
                    page_number=chunk.page_number,
                    chunk_index=i,
                    metadata=chunk.metadata,
                    file_path=pdf_path,
                    chunk_id=f"{Path(pdf_path).stem}_chunk_{i}"
                )
                document_chunks.append(doc_chunk)
            
            # 保存到輸出文件（如果指定）
            if output_path:
                self._save_chunks(document_chunks, output_path)
            
            logger.info(f"PDF 處理完成，生成 {len(document_chunks)} 個段落")
            return document_chunks
            
        except Exception as e:
            logger.error(f"PDF 處理失敗: {e}")
            return []
    
    def _save_chunks(self, chunks: List[DocumentChunk], output_path: str):
        """保存段落到文件"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for chunk in chunks:
                    f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + '\n')
            
            logger.info(f"段落已保存到: {output_path}")
            
        except Exception as e:
            logger.error(f"保存段落失敗: {e}")
