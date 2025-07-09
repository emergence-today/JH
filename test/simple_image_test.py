#!/usr/bin/env python3
"""
簡化的圖片測試腳本
可以選擇每個類別要測試幾張圖片
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

# 添加父目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(current_dir)

from image_qa_test_system import ImageQATestSystem
from config.config import Config

def get_image_categories(images_dir: str = "images") -> Dict[str, List[str]]:
    """獲取圖片分類"""
    categories = defaultdict(list)
    
    if not os.path.exists(images_dir):
        print(f"❌ 圖片目錄不存在: {images_dir}")
        return {}
    
    for filename in os.listdir(images_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            # 提取類別名稱（檔名中第一個 '_' 之前的部分）
            category = filename.split('_')[0]
            categories[category].append(os.path.join(images_dir, filename))
    
    return dict(categories)

def display_categories(categories: Dict[str, List[str]]):
    """顯示所有類別和圖片數量"""
    print("\n📂 可用的圖片類別:")
    print("=" * 60)
    
    for i, (category, images) in enumerate(categories.items(), 1):
        print(f"{i:2d}. {category:<30} ({len(images)} 張圖片)")
    
    print("=" * 60)

def get_user_selection(categories: Dict[str, List[str]]) -> Dict[str, int]:
    """獲取用戶選擇"""
    selection = {}
    category_list = list(categories.keys())
    
    print("\n🎯 請選擇要測試的類別和數量:")
    print("格式: 類別編號:數量 (例如: 1:3 表示第1個類別測試3張)")
    print("多個選擇用空格分隔 (例如: 1:3 5:2 10:1)")
    print("輸入 'all:N' 表示每個類別都測試N張")
    print("直接按 Enter 使用預設 (每個類別1張)")
    
    user_input = input("\n請輸入選擇: ").strip()
    
    if not user_input:
        # 預設每個類別1張
        for category in categories.keys():
            selection[category] = 1
        print("✅ 使用預設設定: 每個類別測試 1 張圖片")
    elif user_input.startswith('all:'):
        # 所有類別相同數量
        try:
            count = int(user_input.split(':')[1])
            for category in categories.keys():
                selection[category] = min(count, len(categories[category]))
            print(f"✅ 所有類別都測試 {count} 張圖片")
        except ValueError:
            print("❌ 格式錯誤，使用預設設定")
            for category in categories.keys():
                selection[category] = 1
    else:
        # 解析用戶輸入
        try:
            for item in user_input.split():
                if ':' in item:
                    idx_str, count_str = item.split(':')
                    idx = int(idx_str) - 1  # 轉換為0基索引
                    count = int(count_str)
                    
                    if 0 <= idx < len(category_list):
                        category = category_list[idx]
                        max_count = len(categories[category])
                        selection[category] = min(count, max_count)
                        print(f"✅ {category}: 測試 {selection[category]} 張圖片")
                    else:
                        print(f"❌ 類別編號 {idx + 1} 超出範圍")
        except ValueError:
            print("❌ 格式錯誤，使用預設設定")
            for category in categories.keys():
                selection[category] = 1
    
    return selection

def run_test(selection: Dict[str, int], categories: Dict[str, List[str]]):
    """執行測試"""
    print("\n🚀 開始執行圖片測試...")
    print("=" * 60)
    
    # 初始化測試系統
    try:
        test_system = ImageQATestSystem()
        print("✅ 測試系統初始化成功")
    except Exception as e:
        print(f"❌ 測試系統初始化失敗: {e}")
        return
    
    total_images = sum(selection.values())
    current_image = 0
    all_results = []
    
    for category, count in selection.items():
        if count == 0:
            continue
            
        print(f"\n📁 測試類別: {category}")
        print("-" * 40)
        
        # 隨機選擇圖片
        available_images = categories[category]
        selected_images = random.sample(available_images, min(count, len(available_images)))
        
        category_scores = []
        
        for image_path in selected_images:
            current_image += 1
            image_name = os.path.basename(image_path)
            
            print(f"[{current_image}/{total_images}] 測試圖片: {image_name}")
            
            try:
                # 執行測試
                start_time = time.time()
                result = test_system.test_single_image(image_path)
                end_time = time.time()
                
                if result:
                    score = result.overall_score
                    category_scores.append(score)
                    all_results.append({
                        'category': category,
                        'image': image_name,
                        'score': score,
                        'time': end_time - start_time
                    })
                    
                    print(f"  ✅ 得分: {score:.3f} (耗時: {end_time - start_time:.1f}s)")
                else:
                    print(f"  ❌ 測試失敗")
                    
            except Exception as e:
                print(f"  ❌ 測試出錯: {e}")
        
        # 顯示類別統計
        if category_scores:
            avg_score = sum(category_scores) / len(category_scores)
            print(f"📊 {category} 平均得分: {avg_score:.3f}")
    
    # 顯示總結
    print("\n" + "=" * 60)
    print("📈 測試結果總結")
    print("=" * 60)
    
    if all_results:
        # 按類別統計
        category_stats = defaultdict(list)
        for result in all_results:
            category_stats[result['category']].append(result['score'])
        
        for category, scores in category_stats.items():
            avg_score = sum(scores) / len(scores)
            print(f"{category:<30} 平均: {avg_score:.3f} ({len(scores)} 張)")
        
        # 總體統計
        all_scores = [r['score'] for r in all_results]
        overall_avg = sum(all_scores) / len(all_scores)
        total_time = sum(r['time'] for r in all_results)
        
        print("-" * 60)
        print(f"總體平均得分: {overall_avg:.3f}")
        print(f"測試圖片總數: {len(all_results)}")
        print(f"總耗時: {total_time:.1f} 秒")
        print(f"平均每張: {total_time/len(all_results):.1f} 秒")
        
        # 保存結果
        save_results(all_results)
    else:
        print("❌ 沒有成功的測試結果")

def save_results(results: List[Dict]):
    """保存測試結果"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"📄 結果已保存到: {filename}")
    except Exception as e:
        print(f"❌ 保存結果失敗: {e}")

def main():
    """主函數"""
    print("🧪 簡化圖片測試系統")
    print("=" * 60)
    
    # 檢查 OpenAI API Key
    if not Config.OPENAI_API_KEY:
        print("❌ 請設置 OPENAI_API_KEY 環境變數")
        return
    
    # 獲取圖片分類
    categories = get_image_categories()
    if not categories:
        print("❌ 沒有找到圖片檔案")
        return
    
    # 顯示類別
    display_categories(categories)
    
    # 獲取用戶選擇
    selection = get_user_selection(categories)
    
    if not any(selection.values()):
        print("❌ 沒有選擇任何圖片進行測試")
        return
    
    # 執行測試
    run_test(selection, categories)

if __name__ == "__main__":
    main()
