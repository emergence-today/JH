"""
生產環境 PDF 處理器
用於測試和生產環境的 PDF 處理
"""

import os
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.processors.pdf_processor import DocumentChunk, VisionDocumentChunk
from src.processors.zerox_pdf_processor import ZeroxPDFProcessor
from src.processors.file_converter import FileConverter

logger = logging.getLogger(__name__)

class ProductionPDFProcessor:
    """生產環境 PDF 處理器"""
    
    def __init__(self, enable_vision: bool = True, max_pages: int = None):
        """
        初始化生產環境 PDF 處理器
        
        Args:
            enable_vision: 是否啟用視覺分析
            max_pages: 最大處理頁數
        """
        self.enable_vision = enable_vision
        self.max_pages = max_pages
        
        # 初始化子處理器
        self.zerox_processor = ZeroxPDFProcessor(max_pages=max_pages)
        self.file_converter = FileConverter()
        
        logger.info(f"ProductionPDFProcessor 初始化完成")
        logger.info(f"  視覺分析: {enable_vision}")
        logger.info(f"  最大頁數: {max_pages}")
    
    async def process_file(self, file_path: str, output_dir: str = "outputs") -> List[DocumentChunk]:
        """
        處理文件（支援多種格式）
        
        Args:
            file_path: 文件路徑
            output_dir: 輸出目錄
            
        Returns:
            List[DocumentChunk]: 處理後的文檔段落
        """
        try:
            file_path = Path(file_path)
            logger.info(f"開始處理文件: {file_path.name}")
            
            # 檢查文件是否存在
            if not file_path.exists():
                logger.error(f"文件不存在: {file_path}")
                return []
            
            # 處理不同文件類型
            if file_path.suffix.lower() == '.pdf':
                # 直接處理 PDF
                pdf_path = str(file_path)
            else:
                # 轉換為 PDF
                logger.info(f"檢測到 {file_path.suffix} 格式，正在轉換為PDF...")
                pdf_path = await self._convert_to_pdf(file_path)
                if not pdf_path:
                    logger.error(f"文件轉換失敗: {file_path}")
                    return []
            
            # 使用 Zerox 處理 PDF
            result = await self.zerox_processor.process_pdf_with_zerox(
                pdf_path=pdf_path,
                output_dir=os.path.join(output_dir, "zerox_output")
            )
            
            if not result:
                logger.error(f"PDF 處理失敗: {pdf_path}")
                return []
            
            # 轉換為段落格式
            chunks = await self.zerox_processor.convert_zerox_to_chunks(result, pdf_path)
            
            # 轉換為 DocumentChunk 格式
            document_chunks = []
            for i, chunk in enumerate(chunks):
                if self.enable_vision:
                    doc_chunk = VisionDocumentChunk(
                        content=chunk.content,
                        page_number=chunk.page_number,
                        chunk_index=i,
                        metadata=chunk.metadata,
                        file_path=str(file_path),
                        chunk_id=f"{file_path.stem}_chunk_{i}",
                        image_description=chunk.metadata.get('image_description', ''),
                        visual_elements=chunk.metadata.get('visual_elements', [])
                    )
                else:
                    doc_chunk = DocumentChunk(
                        content=chunk.content,
                        page_number=chunk.page_number,
                        chunk_index=i,
                        metadata=chunk.metadata,
                        file_path=str(file_path),
                        chunk_id=f"{file_path.stem}_chunk_{i}"
                    )
                document_chunks.append(doc_chunk)
            
            # 清理臨時文件
            if pdf_path != str(file_path):
                try:
                    os.remove(pdf_path)
                    logger.info(f"清理臨時文件: {pdf_path}")
                except:
                    pass
            
            logger.info(f"文件處理完成: {len(document_chunks)} 個段落")
            return document_chunks
            
        except Exception as e:
            logger.error(f"文件處理失敗: {e}")
            return []
    
    async def _convert_to_pdf(self, file_path: Path) -> Optional[str]:
        """轉換文件為 PDF"""
        try:
            output_dir = file_path.parent
            converted_path = self.file_converter.convert_to_pdf(str(file_path), str(output_dir))
            
            if converted_path and os.path.exists(converted_path):
                logger.info(f"文件轉換成功: {converted_path}")
                return converted_path
            else:
                logger.error(f"文件轉換失敗: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"文件轉換錯誤: {e}")
            return None
    
    def process_file_sync(self, file_path: str, output_dir: str = "outputs") -> List[DocumentChunk]:
        """同步版本的文件處理"""
        return asyncio.run(self.process_file(file_path, output_dir))
    
    async def batch_process(self, file_paths: List[str], output_dir: str = "outputs") -> Dict[str, List[DocumentChunk]]:
        """批量處理文件"""
        results = {}
        
        for file_path in file_paths:
            try:
                chunks = await self.process_file(file_path, output_dir)
                results[file_path] = chunks
                logger.info(f"批量處理完成: {file_path} -> {len(chunks)} 段落")
            except Exception as e:
                logger.error(f"批量處理失敗: {file_path} -> {e}")
                results[file_path] = []
        
        return results
