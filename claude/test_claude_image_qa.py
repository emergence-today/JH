#!/usr/bin/env python3
"""
測試 Claude 圖像問答系統
"""

import os
import sys
from pathlib import Path

# 直接導入
sys.path.append(os.path.join(os.path.dirname(__file__), 'test'))

try:
    from claude_image_qa_test import ClaudeImageQATestSystem
except ImportError:
    print("❌ 無法導入 ClaudeImageQATestSystem")
    print("請確認 test/claude_image_qa_test.py 檔案存在")
    sys.exit(1)

def test_single_image():
    """測試單張圖片"""
    print("🧪 Claude 圖像問答系統測試")
    print("=" * 50)
    
    try:
        # 初始化測試系統
        test_system = ClaudeImageQATestSystem()
        
        # 測試圖片路徑
        test_image = "images/材料认识_page_6.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 測試圖片不存在: {test_image}")
            return
        
        print(f"📸 測試圖片: {test_image}")
        print("🔄 開始分析...")
        
        # 執行測試
        result = test_system.test_single_image(test_image)
        
        if result and not result.error_message:
            print(f"\n✅ 測試完成！")
            print(f"📊 總體得分: {result.overall_score:.3f}")
            print(f"⏱️ 分析時間: {result.analysis_time:.1f} 秒")
            print(f"📝 問題數量: {len(result.questions)}")
            
            print("\n" + "=" * 60)
            print("📋 詳細結果:")
            print("=" * 60)
            
            for i, (q, a, s) in enumerate(zip(result.questions, result.answers, result.scores)):
                print(f"\n🔍 問題 {i+1}: {q['text']}")
                print(f"💬 回答: {a}")
                print(f"⭐ 得分: {s:.3f}")
                print("-" * 40)
                
        else:
            error_msg = result.error_message if result else "未知錯誤"
            print(f"❌ 測試失敗: {error_msg}")
            
    except Exception as e:
        print(f"❌ 系統初始化失敗: {e}")
        print("\n💡 請檢查:")
        print("1. AWS 憑證是否正確設定在 .env 檔案中")
        print("2. 是否已安裝 anthropic[bedrock] 套件")
        print("3. AWS 區域是否支援 Claude 模型")

def test_custom_questions():
    """測試自定義問題"""
    print("\n🧪 測試自定義問題")
    print("=" * 50)
    
    try:
        test_system = ClaudeImageQATestSystem()
        
        # 自定義問題
        custom_questions = [
            "這張圖片中顯示了哪些材料或組件？",
            "圖片中有哪些技術規格或參數？",
            "這些材料的主要特性是什麼？"
        ]
        
        test_image = "images/材料认识_page_6.png"
        
        if not os.path.exists(test_image):
            print(f"❌ 測試圖片不存在: {test_image}")
            return
        
        print(f"📸 測試圖片: {test_image}")
        print(f"❓ 自定義問題數量: {len(custom_questions)}")
        
        result = test_system.test_single_image(test_image, custom_questions)
        
        if result and not result.error_message:
            print(f"\n✅ 自定義問題測試完成！")
            print(f"📊 總體得分: {result.overall_score:.3f}")
            
            for i, (q, a, s) in enumerate(zip(result.questions, result.answers, result.scores)):
                print(f"\n🔍 問題 {i+1}: {q['text']}")
                print(f"💬 回答: {a}")
                print(f"⭐ 得分: {s:.3f}")
        else:
            error_msg = result.error_message if result else "未知錯誤"
            print(f"❌ 自定義問題測試失敗: {error_msg}")
            
    except Exception as e:
        print(f"❌ 自定義問題測試失敗: {e}")

def test_batch_images():
    """測試批量圖片處理"""
    print("\n🧪 測試批量圖片處理")
    print("=" * 50)
    
    try:
        test_system = ClaudeImageQATestSystem()
        
        # 找到一些測試圖片
        image_dir = Path("images")
        image_files = list(image_dir.glob("材料认识_page_*.png"))[:3]  # 只測試前3張
        
        if not image_files:
            print("❌ 沒有找到測試圖片")
            return
        
        image_paths = [str(img) for img in image_files]
        print(f"📸 批量測試圖片數量: {len(image_paths)}")
        
        results = test_system.batch_test_images(image_paths)
        
        if results:
            print(f"\n✅ 批量測試完成！")
            print(f"📊 成功處理: {len(results)}/{len(image_paths)} 張圖片")
            
            total_score = sum(r.overall_score for r in results) / len(results)
            print(f"📈 平均得分: {total_score:.3f}")
            
            for i, result in enumerate(results):
                print(f"\n📸 圖片 {i+1}: {Path(result.image_path).name}")
                print(f"   得分: {result.overall_score:.3f}")
                print(f"   時間: {result.analysis_time:.1f}s")
        else:
            print("❌ 批量測試失敗")
            
    except Exception as e:
        print(f"❌ 批量測試失敗: {e}")

def main():
    """主函數"""
    print("🚀 Claude 圖像問答系統完整測試")
    print("=" * 60)
    
    # 檢查環境
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_region = os.getenv("AWS_REGION")
    model = os.getenv("BEDROCK_MODEL")
    
    print(f"🔧 環境檢查:")
    print(f"   AWS Access Key: {'✅ 已設定' if aws_access_key else '❌ 未設定'}")
    print(f"   AWS Region: {aws_region or '❌ 未設定'}")
    print(f"   Bedrock Model: {model or '❌ 未設定'}")
    
    if not aws_access_key:
        print("\n❌ 請先在 .env 檔案中設定 AWS 憑證")
        return
    
    # 執行測試
    test_single_image()
    
    # 可選的額外測試
    choice = input("\n❓ 是否執行自定義問題測試？(y/n): ").lower()
    if choice == 'y':
        test_custom_questions()
    
    choice = input("\n❓ 是否執行批量圖片測試？(y/n): ").lower()
    if choice == 'y':
        test_batch_images()
    
    print("\n🎉 測試完成！")

if __name__ == "__main__":
    main()
