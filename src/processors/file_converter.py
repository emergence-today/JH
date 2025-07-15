#!/usr/bin/env python3
"""
檔案格式轉換器
支援將 PPT, PPTX, DOC, DOCX, XLS, XLSX 等格式轉換為 PDF
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class FileConverter:
    """檔案格式轉換器"""
    
    def __init__(self):
        """初始化轉換器"""
        self.supported_formats = {
            '.ppt', '.pptx', '.doc', '.docx', '.xls', '.xlsx'
        }
        logger.info("檔案轉換器初始化完成")
    
    def is_supported(self, file_path: str) -> bool:
        """檢查檔案格式是否支援轉換"""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_formats
    
    def convert_to_pdf(self, input_path: str, output_path: str) -> Optional[str]:
        """
        將檔案轉換為PDF格式
        
        Args:
            input_path: 輸入檔案路徑
            output_path: 輸出PDF檔案路徑
            
        Returns:
            成功時返回輸出檔案路徑，失敗時返回None
        """
        try:
            input_file = Path(input_path)
            output_file = Path(output_path)
            
            if not input_file.exists():
                logger.error(f"輸入檔案不存在: {input_path}")
                return None
            
            if not self.is_supported(input_path):
                logger.error(f"不支援的檔案格式: {input_file.suffix}")
                return None
            
            # 確保輸出目錄存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用 LibreOffice 進行轉換
            success = self._convert_with_libreoffice(input_path, output_path)
            
            if success and output_file.exists():
                logger.info(f"檔案轉換成功: {input_path} -> {output_path}")
                return str(output_path)
            else:
                logger.error(f"檔案轉換失敗: {input_path}")
                return None
                
        except Exception as e:
            logger.error(f"檔案轉換過程中發生錯誤: {e}")
            return None
    
    def _convert_with_libreoffice(self, input_path: str, output_path: str) -> bool:
        """使用 LibreOffice 進行轉換"""
        try:
            output_dir = Path(output_path).parent
            output_name = Path(output_path).stem
            
            # LibreOffice 轉換命令
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', str(output_dir),
                input_path
            ]
            
            logger.info(f"執行轉換命令: {' '.join(cmd)}")
            
            # 執行轉換
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60秒超時
            )
            
            if result.returncode == 0:
                # LibreOffice 會自動生成檔名，需要重新命名
                auto_generated_pdf = output_dir / f"{Path(input_path).stem}.pdf"
                target_pdf = Path(output_path)
                
                if auto_generated_pdf.exists() and auto_generated_pdf != target_pdf:
                    auto_generated_pdf.rename(target_pdf)
                
                return target_pdf.exists()
            else:
                logger.error(f"LibreOffice 轉換失敗: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("LibreOffice 轉換超時")
            return False
        except FileNotFoundError:
            logger.error("LibreOffice 未安裝或不在PATH中")
            return False
        except Exception as e:
            logger.error(f"LibreOffice 轉換過程中發生錯誤: {e}")
            return False
    
    def batch_convert(self, input_dir: str, output_dir: str) -> list:
        """
        批量轉換目錄中的檔案
        
        Args:
            input_dir: 輸入目錄
            output_dir: 輸出目錄
            
        Returns:
            轉換成功的檔案列表
        """
        converted_files = []
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            logger.error(f"輸入目錄不存在: {input_dir}")
            return converted_files
        
        # 確保輸出目錄存在
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 遞歸查找支援的檔案
        for file_path in input_path.rglob('*'):
            if file_path.is_file() and self.is_supported(str(file_path)):
                # 生成輸出檔案路徑
                relative_path = file_path.relative_to(input_path)
                output_file = output_path / relative_path.with_suffix('.pdf')
                
                # 轉換檔案
                result = self.convert_to_pdf(str(file_path), str(output_file))
                if result:
                    converted_files.append(result)
        
        logger.info(f"批量轉換完成，成功轉換 {len(converted_files)} 個檔案")
        return converted_files

def main():
    """測試函數"""
    converter = FileConverter()
    
    # 測試單個檔案轉換
    test_input = "test.pptx"
    test_output = "test.pdf"
    
    if Path(test_input).exists():
        result = converter.convert_to_pdf(test_input, test_output)
        if result:
            print(f"轉換成功: {result}")
        else:
            print("轉換失敗")
    else:
        print(f"測試檔案不存在: {test_input}")

if __name__ == "__main__":
    main()
