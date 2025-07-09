"""
批量處理資料夾中的文件並建立Qdrant集合
支援PDF、PPT、Word、Excel等格式
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Optional
import argparse

from pdf_processor import PDFProcessor
from file_converter import FileConverter
from rag_system import TeachingRAGSystem
from config import Config

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_process.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchFileProcessor:
    """批量文件處理器"""
    
    def __init__(self, enable_vision: bool = True):
        self.enable_vision = enable_vision
        self.file_converter = FileConverter()
        self.pdf_processor = PDFProcessor(enable_vision_analysis=enable_vision)
        
        # 支援的文件格式
        self.supported_extensions = {
            '.pdf', '.ppt', '.pptx', '.doc', '.docx', 
            '.xls', '.xlsx'
        }
    
    def find_files_in_directory(self, directory: str) -> List[str]:
        """在目錄中尋找支援的文件"""
        files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            logger.error(f"目錄不存在: {directory}")
            return files
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                files.append(str(file_path))
                logger.info(f"找到文件: {file_path}")
        
        return files
    
    def process_single_file(self, file_path: str, temp_dir: str = "temp") -> Optional[List]:
        """處理單個文件"""
        try:
            file_path_obj = Path(file_path)
            file_ext = file_path_obj.suffix.lower()
            
            logger.info(f"開始處理文件: {file_path} (格式: {file_ext})")
            
            # 創建臨時目錄
            os.makedirs(temp_dir, exist_ok=True)
            
            # 如果不是PDF，先轉換為PDF
            if file_ext != '.pdf':
                logger.info(f"正在將 {file_ext} 格式轉換為PDF...")
                temp_pdf_path = os.path.join(temp_dir, f"{file_path_obj.stem}.pdf")
                
                converted_pdf = self.file_converter.convert_to_pdf(file_path, temp_pdf_path)
                if not converted_pdf:
                    logger.error(f"檔案格式轉換失敗：{file_path}")
                    return None
                
                pdf_path = converted_pdf
                logger.info(f"格式轉換成功: {pdf_path}")
            else:
                pdf_path = file_path
            
            # 處理PDF文件
            chunks = self.pdf_processor.process_pdf(
                pdf_path=pdf_path,
                output_path=os.path.join(temp_dir, f"{file_path_obj.stem}_chunks.jsonl")
            )
            
            if not chunks:
                logger.error(f"PDF處理失敗，未能提取到任何內容: {file_path}")
                return None
            
            logger.info(f"文件處理完成: {file_path}, 提取到 {len(chunks)} 個段落")
            return chunks
            
        except Exception as e:
            logger.error(f"處理文件時發生錯誤 {file_path}: {e}")
            return None
    
    def process_directory(self, directory: str, collection_name: str, 
                         force_recreate: bool = False) -> dict:
        """處理整個目錄"""
        start_time = time.time()
        
        # 尋找文件
        files = self.find_files_in_directory(directory)
        if not files:
            return {
                "success": False,
                "message": f"在目錄 {directory} 中沒有找到支援的文件",
                "files_processed": 0,
                "total_chunks": 0,
                "total_images": 0
            }
        
        logger.info(f"找到 {len(files)} 個文件待處理")
        
        # 處理所有文件
        all_chunks = []
        processed_files = 0
        total_images = 0
        
        for file_path in files:
            chunks = self.process_single_file(file_path)
            if chunks:
                all_chunks.extend(chunks)
                processed_files += 1
                
                # 統計圖片數量
                images_count = len([c for c in chunks if hasattr(c, 'has_images') and c.has_images])
                total_images += images_count
                logger.info(f"文件 {Path(file_path).name} 包含 {images_count} 張圖片")
        
        if not all_chunks:
            return {
                "success": False,
                "message": "所有文件處理失敗，未能提取到任何內容",
                "files_processed": 0,
                "total_chunks": 0,
                "total_images": 0
            }
        
        # 初始化RAG系統並創建向量嵌入
        logger.info(f"開始創建向量嵌入到集合: {collection_name}")
        rag_system = TeachingRAGSystem()
        rag_system.collection_name = collection_name
        rag_system.chunks = all_chunks
        
        try:
            if force_recreate:
                logger.info("強制重新創建向量嵌入...")
                rag_system.force_recreate_embeddings()
            else:
                logger.info("創建向量嵌入...")
                rag_system.create_embeddings()
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "message": f"成功處理 {processed_files} 個文件",
                "files_processed": processed_files,
                "total_chunks": len(all_chunks),
                "total_images": total_images,
                "collection_name": collection_name,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"創建向量嵌入失敗: {e}")
            return {
                "success": False,
                "message": f"向量嵌入失敗: {str(e)}",
                "files_processed": processed_files,
                "total_chunks": len(all_chunks),
                "total_images": total_images
            }

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='批量處理資料夾中的文件並建立Qdrant集合')
    parser.add_argument('directory', help='要處理的資料夾路徑')
    parser.add_argument('--collection', '-c', default=None, help='Qdrant集合名稱（預設使用時間戳）')
    parser.add_argument('--no-vision', action='store_true', help='停用視覺分析')
    parser.add_argument('--force-recreate', action='store_true', help='強制重新創建集合')
    
    args = parser.parse_args()
    
    # 設定集合名稱
    if args.collection:
        collection_name = args.collection
    else:
        collection_name = f"batch_processed_{int(time.time())}"
    
    # 初始化處理器
    processor = BatchFileProcessor(enable_vision=not args.no_vision)
    
    logger.info(f"開始批量處理資料夾: {args.directory}")
    logger.info(f"目標集合: {collection_name}")
    logger.info(f"視覺分析: {'停用' if args.no_vision else '啟用'}")
    logger.info(f"強制重新創建: {'是' if args.force_recreate else '否'}")
    
    # 執行處理
    result = processor.process_directory(
        directory=args.directory,
        collection_name=collection_name,
        force_recreate=args.force_recreate
    )
    
    # 輸出結果
    print("\n" + "="*50)
    print("批量處理結果")
    print("="*50)
    
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"📁 處理文件數: {result['files_processed']}")
        print(f"📄 總段落數: {result['total_chunks']}")
        print(f"🖼️  總圖片數: {result['total_images']}")
        print(f"🗂️  集合名稱: {result['collection_name']}")
        if 'processing_time' in result:
            print(f"⏱️  處理時間: {result['processing_time']:.2f} 秒")
    else:
        print(f"❌ {result['message']}")
        print(f"📁 已處理文件數: {result['files_processed']}")
        print(f"📄 已提取段落數: {result['total_chunks']}")
        print(f"🖼️  已提取圖片數: {result['total_images']}")

if __name__ == "__main__":
    main()
