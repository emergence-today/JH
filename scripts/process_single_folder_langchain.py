#!/usr/bin/env python3
"""
處理單一資料夾並使用LangChain Parent-Child RAG系統
避免重複處理圖片
"""

import sys
import os
import logging
import time
import hashlib
from pathlib import Path
from typing import Set, List

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langchain_rag_system import LangChainParentChildRAG
from config.config import Config

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_file_hash(file_path: Path) -> str:
    """計算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def is_file_already_processed(file_path: Path) -> bool:
    """檢查文件是否已經處理過（基於markdown文件是否存在）"""
    file_stem = file_path.stem
    output_dir = Path("outputs/images/zerox_output")

    print(f"  🔍 檢查文件是否已處理: {file_stem}")

    # 檢查是否有對應的markdown文件
    # 考慮各種可能的命名模式
    possible_patterns = [
        f"{file_stem}.md",
        f"{file_stem}_converted.md",
        f"{file_stem}__converted.md",  # 雙底線情況
        f"{file_stem.rstrip('.')}_converted.md",  # 移除末尾的點
        f"{file_stem.rstrip('.')}__converted.md"   # 移除末尾的點 + 雙底線
    ]

    for pattern in possible_patterns:
        md_path = output_dir / pattern
        if md_path.exists():
            print(f"  ✅ 找到已處理的markdown文件: {pattern}")
            return True

    # 如果沒有找到精確匹配，嘗試模糊匹配
    # 檢查是否有包含文件名的markdown文件
    base_name = file_stem.rstrip('.').replace('..', '_').replace('.', '_')

    print(f"  🔍 嘗試模糊匹配，基礎名稱: {base_name}")

    for md_file in output_dir.glob("*.md"):
        md_stem = md_file.stem
        # 檢查多種匹配模式
        if (base_name in md_stem or
            md_stem.replace('_', '').replace('.', '') == base_name.replace('_', '').replace('.', '') or
            any(part in md_stem for part in base_name.split('_') if len(part) > 2)):
            print(f"  ✅ 找到相關的markdown文件: {md_file.name}")
            return True

    print(f"  ❌ 未找到對應的markdown文件")
    return False

def find_unique_files(folder_path: Path) -> List[Path]:
    """找到資料夾中的唯一文件，避免重複，排除臨時轉換文件"""

    print(f"🔍 掃描資料夾: {folder_path}")

    if not folder_path.exists():
        print(f"❌ 資料夾不存在: {folder_path}")
        return []

    # 支持的文件類型
    supported_extensions = {'.pdf', '.ppt', '.pptx', '.doc', '.docx'}

    # 收集所有文件
    all_files = []
    for ext in supported_extensions:
        all_files.extend(folder_path.glob(f"*{ext}"))
        all_files.extend(folder_path.glob(f"**/*{ext}"))  # 包含子目錄

    # 過濾掉臨時轉換文件
    filtered_files = []
    for file_path in all_files:
        # 跳過臨時轉換的PDF文件
        if file_path.name.endswith('_converted.pdf') or file_path.name.endswith('__converted.pdf'):
            print(f"  ⏭️  跳過臨時轉換文件: {file_path.name}")
            continue
        filtered_files.append(file_path)

    print(f"📄 找到 {len(filtered_files)} 個有效文件")

    # 去重：使用文件哈希值
    unique_files = []
    seen_hashes: Set[str] = set()

    for file_path in filtered_files:
        try:
            file_hash = get_file_hash(file_path)
            if file_hash not in seen_hashes:
                seen_hashes.add(file_hash)
                unique_files.append(file_path)
                print(f"  ✅ 唯一文件: {file_path.name}")
            else:
                print(f"  ⚠️  重複文件: {file_path.name} (跳過)")
        except Exception as e:
            print(f"  ❌ 無法讀取文件: {file_path.name} - {e}")

    print(f"📊 去重後剩餘 {len(unique_files)} 個唯一文件")
    return unique_files

def process_folder_with_langchain(folder_path: str):
    """處理指定資料夾並使用LangChain系統"""
    
    print("🔄 處理單一資料夾並使用LangChain Parent-Child RAG系統...")
    print(f"📁 目標資料夾: {folder_path}")
    
    try:
        folder_path = Path(folder_path)
        
        # 1. 找到唯一文件
        unique_files = find_unique_files(folder_path)
        
        if not unique_files:
            print("❌ 沒有找到可處理的文件")
            return
        
        # 2. 初始化LangChain RAG系統
        collection_name = "JH-圖紙認識-langchain"
        print(f"📊 初始化LangChain RAG系統: {collection_name}")
        langchain_rag = LangChainParentChildRAG(collection_name)
        
        # 3. 檢查是否已有數據
        if langchain_rag.has_vector_data():
            print("⚠️  LangChain集合已存在數據")
            print("選擇處理模式:")
            print("  1. 疊加模式 - 保留現有數據，只處理新文件 (推薦)")
            print("  2. 重新處理 - 清除現有數據，重新處理所有文件")
            print("  3. 取消處理")

            while True:
                response = input("請選擇 (1/2/3): ").strip()
                if response == '1':
                    print("✅ 使用疊加模式，保留現有數據")
                    break
                elif response == '2':
                    print("⚠️  將清除現有數據並重新處理")
                    # 這裡可以添加清除邏輯，暫時跳過
                    print("❌ 重新處理模式暫未實現，請使用疊加模式")
                    continue
                elif response == '3':
                    print("❌ 取消處理")
                    return
                else:
                    print("❌ 無效選擇，請輸入 1、2 或 3")
        
        # 4. 臨時修改配置使用LangChain
        original_rag_type = Config.RAG_SYSTEM_TYPE
        original_collection = Config.QDRANT_COLLECTION_NAME
        
        Config.RAG_SYSTEM_TYPE = "langchain"
        Config.QDRANT_COLLECTION_NAME = collection_name
        
        try:
            # 5. 導入處理器
            from src.processors.zerox_pdf_processor import ZeroxPDFProcessor
            from src.processors.file_converter import FileConverter

            # 6. 初始化處理器
            processor = ZeroxPDFProcessor()
            converter = FileConverter()

            # 7. 收集所有chunks
            all_chunks = []
            total_time = 0
            processed_files = 0

            for file_path in unique_files:
                print(f"\n🔄 檢查文件: {file_path.name}")

                # 在疊加模式下，檢查文件是否已經處理過
                if is_file_already_processed(file_path):
                    print(f"  ⏭️  文件已處理過，跳過: {file_path.name}")
                    continue

                print(f"  🔄 開始處理新文件: {file_path.name}")
                start_time = time.time()

                try:
                    # 檢查文件格式，如果不是PDF則先轉換
                    file_ext = file_path.suffix.lower()
                    pdf_path = str(file_path)

                    if file_ext != '.pdf':
                        print(f"  📄 檢測到 {file_ext} 格式，正在轉換為PDF...")

                        # 創建臨時PDF文件路徑
                        temp_pdf_path = str(file_path.parent / f"{file_path.stem}_converted.pdf")

                        # 使用FileConverter轉換為PDF
                        converted_pdf = converter.convert_to_pdf(str(file_path), temp_pdf_path)

                        if not converted_pdf:
                            print(f"  ❌ 格式轉換失敗: {file_path.name}")
                            continue

                        pdf_path = converted_pdf
                        print(f"  ✅ 格式轉換成功: {Path(converted_pdf).name}")

                    # 調用Zerox處理PDF
                    import asyncio
                    import warnings

                    # 抑制 asyncio 警告
                    warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Event loop is closed.*")

                    # 使用新的事件循環來避免衝突
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        chunks = loop.run_until_complete(processor.process_pdf(pdf_path))
                    finally:
                        # 確保正確關閉事件循環
                        try:
                            # 等待所有待處理的任務完成
                            pending = asyncio.all_tasks(loop)
                            if pending:
                                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        except Exception:
                            pass
                        finally:
                            loop.close()

                    if chunks:
                        all_chunks.extend(chunks)

                        file_time = time.time() - start_time
                        total_time += file_time
                        processed_files += 1

                        print(f"  ✅ 處理完成: {len(chunks)} 個段落, {file_time:.2f}秒")
                    else:
                        print(f"  ❌ 處理失敗: 沒有生成段落")

                    # 清理臨時PDF文件
                    if file_ext != '.pdf' and Path(pdf_path).exists():
                        try:
                            Path(pdf_path).unlink()
                            print(f"  🗑️  清理臨時文件: {Path(pdf_path).name}")
                        except Exception as cleanup_error:
                            print(f"  ⚠️  清理臨時文件失敗: {cleanup_error}")

                except Exception as e:
                    print(f"  ❌ 處理文件時發生錯誤: {e}")
                    continue

            # 8. 將所有chunks添加到LangChain系統
            if all_chunks:
                print(f"\n🔄 將 {len(all_chunks)} 個段落添加到LangChain系統...")
                langchain_start = time.time()

                langchain_result = langchain_rag.add_documents_from_zerox(all_chunks)

                langchain_time = time.time() - langchain_start
                total_time += langchain_time

                if langchain_result.get("success"):
                    print(f"  ✅ LangChain處理完成: {langchain_result.get('documents_added', 0)} 個文檔")
                else:
                    print(f"  ❌ LangChain處理失敗: {langchain_result.get('error')}")

            # 9. 顯示總結
            print(f"\n✅ 批量處理完成！")
            print(f"  處理文件數: {processed_files}/{len(unique_files)}")
            print(f"  原始段落數: {len(all_chunks)}")
            print(f"  LangChain文檔數: {langchain_result.get('documents_added', 0) if all_chunks else 0}")
            print(f"  總處理時間: {total_time:.2f}秒")
            print(f"  平均每文件: {total_time/processed_files:.2f}秒" if processed_files > 0 else "")
            print(f"  集合名稱: {collection_name}")

            # 10. 測試LangChain檢索
            if all_chunks:
                print("\n🔍 測試LangChain檢索效果...")
                test_queries = [
                    "圖紙",
                    "圖面識別",
                    "技術圖紙",
                    "工程圖",
                    "設計圖"
                ]
                
                for query in test_queries:
                    print(f"\n查詢: {query}")
                    results = langchain_rag.retrieve_relevant_chunks(query, top_k=3)
                    print(f"  結果數量: {len(results)}")
                    
                    for i, result in enumerate(results):
                        print(f"  {i+1}. 相似度: {result.similarity_score:.3f}")
                        print(f"     主題: {result.child_chunk.topic}")
                        print(f"     內容: {result.child_chunk.content[:80]}...")
                
                # 11. 更新配置建議
                print(f"\n💡 如果測試效果良好，可以更新.env配置:")
                print(f"   QDRANT_COLLECTION_NAME={collection_name}")
                print(f"   RAG_SYSTEM_TYPE=langchain")
            
        finally:
            # 恢復原始配置
            Config.RAG_SYSTEM_TYPE = original_rag_type
            Config.QDRANT_COLLECTION_NAME = original_collection
            
    except Exception as e:
        logger.error(f"處理過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

def test_existing_langchain():
    """測試現有的LangChain數據"""
    
    print("🔍 測試現有LangChain數據...")
    
    try:
        collection_name = "JH-圖紙認識-langchain"
        langchain_rag = LangChainParentChildRAG(collection_name)
        
        if not langchain_rag.has_vector_data():
            print("❌ 沒有找到LangChain數據")
            return
        
        test_queries = [
            "圖紙",
            "圖面識別", 
            "技術圖紙",
            "工程圖",
            "設計圖",
            "焊接工藝",
            "材料"
        ]
        
        print(f"📊 測試 {len(test_queries)} 個查詢...")
        
        for query in test_queries:
            print(f"\n查詢: {query}")
            results = langchain_rag.retrieve_relevant_chunks(query, top_k=3)
            print(f"  結果數量: {len(results)}")
            
            for i, result in enumerate(results):
                print(f"  {i+1}. 相似度: {result.similarity_score:.3f}")
                print(f"     主題: {result.child_chunk.topic}")
                print(f"     內容: {result.child_chunk.content[:80]}...")
                
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    target_folder = "/home/chun/heph-dev/JH/專家/其他"
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_existing_langchain()
    else:
        process_folder_with_langchain(target_folder)
