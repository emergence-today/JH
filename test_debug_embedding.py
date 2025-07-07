#!/usr/bin/env python3
"""
測試調試功能的腳本
用於驗證 embedding 生成和調試輸出是否正常
"""

import sys
import os
from pathlib import Path

# 添加當前目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent))

from meteor_utilities import MeteorUtilities
from rag_system import TeachingRAGSystem
from pdf_processor import DocumentChunk

def test_meteor_utilities():
    """測試 MeteorUtilities 的調試功能"""
    print("🧪 測試 MeteorUtilities 調試功能")
    print("="*50)
    
    try:
        meteor = MeteorUtilities()
        
        # 測試文本
        test_texts = [
            "這是一個測試文本",
            "電線規格 AWG24",
            "",  # 空文本測試
            "材料介紹 - 線材特性說明"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n--- 測試 {i}: \"{text}\" ---")
            embedding = meteor.get_embedding(text, debug_print=True)
            print(f"結果向量維度: {len(embedding)}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def test_chunk_processing():
    """測試 chunk 處理的調試功能"""
    print("\n\n🧪 測試 Chunk 處理調試功能")
    print("="*50)
    
    try:
        # 創建測試 chunks
        test_chunks = [
            DocumentChunk(
                page_num=1,
                topic="材料介紹",
                sub_topic="電線規格",
                content="AWG24線材具有良好的導電性能，適用於一般電子產品。",
                content_type="definition",
                keywords=["AWG24", "線材", "導電性"],
                difficulty_level="basic",
                chunk_id="test_001"
            ),
            DocumentChunk(
                page_num=2,
                topic="材料介紹", 
                sub_topic="連接器類型",
                content="常見的連接器包括JST、Molex等品牌，具有不同的PIN腳配置。",
                content_type="example",
                keywords=["連接器", "JST", "Molex", "PIN"],
                difficulty_level="intermediate",
                chunk_id="test_002"
            )
        ]
        
        # 初始化 RAG 系統
        rag_system = TeachingRAGSystem()
        rag_system.chunks = test_chunks
        rag_system.collection_name = "test_debug_collection"
        
        print(f"📋 準備處理 {len(test_chunks)} 個測試 chunks")
        
        # 測試向量生成（這會觸發調試輸出）
        print("\n開始測試向量生成...")
        rag_system._generate_and_store_embeddings()
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 開始調試功能測試")
    print("="*60)
    
    # 測試 1: MeteorUtilities
    test_meteor_utilities()
    
    # 測試 2: Chunk 處理
    test_chunk_processing()
    
    print("\n" + "="*60)
    print("✅ 測試完成！")
    print("\n💡 如果看到詳細的調試輸出，說明功能正常")
    print("💡 現在您可以使用以下命令重新處理您的檔案:")
    print("uv run batch_process_files.py \"/home/ubuntu/projects/JH/今皓專家RAG(鑑識圖片PPT)/專家/圖紙認識/材料介紹\" --collection steven_0704")