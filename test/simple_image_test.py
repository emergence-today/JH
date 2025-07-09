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
import base64
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

# 添加父目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(current_dir)

try:
    from claude_image_qa_test import ClaudeImageQATestSystem
    USE_CLAUDE = True
    print("✅ 使用 Claude 圖像問答系統")
except ImportError:
    try:
        from image_qa_test_system import ImageQATestSystem
        from config.config import Config
        USE_CLAUDE = False
        print("⚠️ 回退到 OpenAI 圖像問答系統")
    except ImportError:
        print("❌ 無法導入任何圖像問答系統")
        sys.exit(1)

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
        if USE_CLAUDE:
            test_system = ClaudeImageQATestSystem()
            print("✅ Claude 測試系統初始化成功")
        else:
            test_system = ImageQATestSystem()
            print("✅ OpenAI 測試系統初始化成功")
    except Exception as e:
        print(f"❌ 測試系統初始化失敗: {e}")
        print("💡 請檢查:")
        if USE_CLAUDE:
            print("   - AWS 憑證是否正確設定在 .env 檔案中")
            print("   - 是否已安裝 anthropic[bedrock] 套件")
        else:
            print("   - OpenAI API Key 是否正確設定")
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
                        'image_path': image_path,
                        'score': score,
                        'time': end_time - start_time,
                        'questions': result.questions,
                        'answers': result.answers,
                        'individual_scores': result.scores,
                        'analysis_time': result.analysis_time
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
    """保存測試結果為 HTML 格式"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    html_filename = f"test_results_{timestamp}.html"
    json_filename = f"test_results_{timestamp}.json"

    try:
        # 保存 JSON 格式（備份）
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 生成 HTML 報告（包含圖片）
        html_content = generate_html_report_with_images(results, timestamp)

        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"📄 HTML 報告已保存到: {html_filename}")
        print(f"📄 JSON 備份已保存到: {json_filename}")
        print(f"🖼️ 報告包含圖片展示功能")
    except Exception as e:
        print(f"❌ 保存結果失敗: {e}")

def generate_html_report(results: List[Dict], timestamp: str) -> str:
    """生成 HTML 測試報告"""

    # 計算統計數據
    total_images = len(results)
    if total_images == 0:
        return "<html><body><h1>沒有測試結果</h1></body></html>"

    total_score = sum(r['score'] for r in results)
    avg_score = total_score / total_images
    total_time = sum(r['time'] for r in results)

    # 按類別統計
    category_stats = defaultdict(list)
    for result in results:
        category_stats[result['category']].append(result['score'])

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>圖片測試結果報告 - {timestamp}</title>
    <style>
        body {{
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        h3 {{
            color: #2980b9;
            margin-top: 25px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .summary-item {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border-left: 4px solid #3498db;
        }}
        .summary-item .value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .summary-item .label {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .category-stats {{
            margin: 20px 0;
        }}
        .category-item {{
            background-color: #f8f9fa;
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .image-result {{
            background-color: #fafafa;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 20px 0;
            padding: 20px;
        }}
        .image-header {{
            background-color: #3498db;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .score {{
            font-size: 18px;
            font-weight: bold;
        }}
        .score.high {{ color: #27ae60; }}
        .score.medium {{ color: #f39c12; }}
        .score.low {{ color: #e74c3c; }}
        .qa-section {{
            margin: 15px 0;
        }}
        .question {{
            background-color: #e8f4fd;
            padding: 12px;
            border-left: 4px solid #3498db;
            margin: 10px 0 5px 0;
            border-radius: 0 5px 5px 0;
        }}
        .answer {{
            background-color: #f0f8f0;
            padding: 12px;
            border-left: 4px solid #27ae60;
            margin: 5px 0 10px 20px;
            border-radius: 0 5px 5px 0;
        }}
        .question-score {{
            float: right;
            background-color: #34495e;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 30px;
            border-top: 1px solid #ecf0f1;
            padding-top: 15px;
        }}
        .progress-bar {{
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            height: 20px;
            margin: 5px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #e74c3c 0%, #f39c12 50%, #27ae60 100%);
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 圖片測試結果報告</h1>

        <div class="summary">
            <h2>📊 測試總結</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="value">{avg_score:.3f}</div>
                    <div class="label">平均得分</div>
                </div>
                <div class="summary-item">
                    <div class="value">{total_images}</div>
                    <div class="label">測試圖片</div>
                </div>
                <div class="summary-item">
                    <div class="value">{total_time:.1f}s</div>
                    <div class="label">總耗時</div>
                </div>
                <div class="summary-item">
                    <div class="value">{total_time/total_images:.1f}s</div>
                    <div class="label">平均每張</div>
                </div>
            </div>
        </div>

        <div class="category-stats">
            <h2>📂 類別統計</h2>"""

    # 添加類別統計
    for category, scores in category_stats.items():
        avg_cat_score = sum(scores) / len(scores)
        score_class = "high" if avg_cat_score >= 0.8 else "medium" if avg_cat_score >= 0.6 else "low"

        html_content += f"""
            <div class="category-item">
                <span>{category}</span>
                <div>
                    <span class="score {score_class}">{avg_cat_score:.3f}</span>
                    <span style="color: #7f8c8d; margin-left: 10px;">({len(scores)} 張)</span>
                </div>
            </div>"""

    html_content += """
        </div>

        <h2>🖼️ 詳細測試結果</h2>"""

    # 添加每張圖片的詳細結果
    for i, result in enumerate(results, 1):
        score_class = "high" if result['score'] >= 0.8 else "medium" if result['score'] >= 0.6 else "low"

        html_content += f"""
        <div class="image-result">
            <div class="image-header">
                <div>
                    <strong>#{i} {result['image']}</strong>
                    <div style="font-size: 14px; opacity: 0.9;">類別: {result['category']}</div>
                </div>
                <div class="score {score_class}">{result['score']:.3f}</div>
            </div>

            <div style="margin-bottom: 15px;">
                <strong>⏱️ 處理時間:</strong> {result['time']:.1f} 秒
            </div>

            <div class="progress-bar">
                <div class="progress-fill" style="width: {result['score']*100}%"></div>
            </div>

            <div class="qa-section">
                <h3>💬 問答詳情</h3>"""

        # 添加問題和答案
        questions = result.get('questions', [])
        answers = result.get('answers', [])
        individual_scores = result.get('individual_scores', [])

        for j, (question, answer, q_score) in enumerate(zip(questions, answers, individual_scores), 1):
            question_text = question.get('text', question) if isinstance(question, dict) else question
            score_class_q = "high" if q_score >= 0.8 else "medium" if q_score >= 0.6 else "low"

            html_content += f"""
                <div class="question">
                    <strong>Q{j}:</strong> {question_text}
                    <span class="question-score {score_class_q}">{q_score:.3f}</span>
                </div>
                <div class="answer">
                    <strong>A{j}:</strong> {answer}
                </div>"""

        html_content += """
            </div>
        </div>"""

    # 添加頁腳
    html_content += f"""
        <div class="timestamp">
            📅 報告生成時間: {time.strftime('%Y-%m-%d %H:%M:%S')}
            <br>
            🤖 圖片測試系統 v2.0 - 基於 {'Claude' if USE_CLAUDE else 'GPT-4o'} 視覺模型
        </div>
    </div>
</body>
</html>"""

    return html_content

def encode_image_to_base64(image_path: str) -> str:
    """將圖片編碼為 base64 用於 HTML 嵌入"""
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            # 根據檔案副檔名確定 MIME 類型
            ext = Path(image_path).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif ext == '.png':
                mime_type = 'image/png'
            elif ext == '.gif':
                mime_type = 'image/gif'
            else:
                mime_type = 'image/png'  # 預設

            return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        print(f"⚠️ 無法編碼圖片 {image_path}: {e}")
        return ""

def generate_html_report_with_images(results: List[Dict], timestamp: str) -> str:
    """生成包含圖片的 HTML 測試報告"""

    # 計算統計數據
    total_images = len(results)
    if total_images == 0:
        return "<html><body><h1>沒有測試結果</h1></body></html>"

    total_score = sum(r['score'] for r in results)
    avg_score = total_score / total_images
    total_time = sum(r['time'] for r in results)

    # 按類別統計
    category_stats = defaultdict(list)
    for result in results:
        category_stats[result['category']].append(result['score'])

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>圖片測試結果報告 - {timestamp}</title>
    <style>
        body {{
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        h3 {{
            color: #2980b9;
            margin-top: 25px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .summary-item {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border-left: 4px solid #3498db;
        }}
        .summary-item .value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .summary-item .label {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .category-stats {{
            margin: 20px 0;
        }}
        .category-item {{
            background-color: #f8f9fa;
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .image-result {{
            background-color: #fafafa;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 20px 0;
            padding: 20px;
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
            align-items: start;
        }}
        .image-container {{
            position: sticky;
            top: 20px;
        }}
        .test-image {{
            width: 100%;
            max-width: 300px;
            height: auto;
            border-radius: 8px;
            border: 2px solid #ddd;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        .test-image:hover {{
            transform: scale(1.05);
            border-color: #3498db;
        }}
        .image-info {{
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 12px;
            color: #666;
        }}
        .content-area {{
            min-height: 400px;
        }}
        .image-header {{
            background-color: #3498db;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .score {{
            font-size: 18px;
            font-weight: bold;
        }}
        .score.high {{ color: #27ae60; }}
        .score.medium {{ color: #f39c12; }}
        .score.low {{ color: #e74c3c; }}
        .qa-section {{
            margin: 15px 0;
        }}
        .question {{
            background-color: #e8f4fd;
            padding: 12px;
            border-left: 4px solid #3498db;
            margin: 10px 0 5px 0;
            border-radius: 0 5px 5px 0;
        }}
        .answer {{
            background-color: #f0f8f0;
            padding: 12px;
            border-left: 4px solid #27ae60;
            margin: 5px 0 10px 20px;
            border-radius: 0 5px 5px 0;
        }}
        .question-score {{
            float: right;
            background-color: #34495e;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }}
        .progress-bar {{
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            height: 20px;
            margin: 5px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #e74c3c 0%, #f39c12 50%, #27ae60 100%);
            transition: width 0.3s ease;
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 30px;
            border-top: 1px solid #ecf0f1;
            padding-top: 15px;
        }}
        /* 圖片放大模態框 */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }}
        .modal-content {{
            margin: auto;
            display: block;
            width: 80%;
            max-width: 900px;
            max-height: 80%;
            margin-top: 5%;
        }}
        .close {{
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        .close:hover {{
            color: #bbb;
        }}
        @media (max-width: 768px) {{
            .image-result {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}
            .test-image {{
                max-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 圖片測試結果報告</h1>

        <div class="summary">
            <h2>📊 測試總結</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="value">{avg_score:.3f}</div>
                    <div class="label">平均得分</div>
                </div>
                <div class="summary-item">
                    <div class="value">{total_images}</div>
                    <div class="label">測試圖片</div>
                </div>
                <div class="summary-item">
                    <div class="value">{total_time:.1f}s</div>
                    <div class="label">總耗時</div>
                </div>
                <div class="summary-item">
                    <div class="value">{total_time/total_images:.1f}s</div>
                    <div class="label">平均每張</div>
                </div>
            </div>
        </div>

        <div class="category-stats">
            <h2>📂 類別統計</h2>"""

    # 添加類別統計
    for category, scores in category_stats.items():
        avg_cat_score = sum(scores) / len(scores)
        score_class = "high" if avg_cat_score >= 0.8 else "medium" if avg_cat_score >= 0.6 else "low"

        html_content += f"""
            <div class="category-item">
                <span>{category}</span>
                <div>
                    <span class="score {score_class}">{avg_cat_score:.3f}</span>
                    <span style="color: #7f8c8d; margin-left: 10px;">({len(scores)} 張)</span>
                </div>
            </div>"""

    html_content += """
        </div>

        <h2>🖼️ 詳細測試結果</h2>"""

    # 添加每個圖片的詳細結果
    for i, result in enumerate(results, 1):
        score_class = "high" if result['score'] >= 0.8 else "medium" if result['score'] >= 0.6 else "low"

        # 編碼圖片為 base64
        image_data = encode_image_to_base64(result['image_path'])
        image_name = Path(result['image_path']).name

        html_content += f"""
        <div class="image-result">
            <div class="image-container">
                <img src="{image_data}" alt="{image_name}" class="test-image" onclick="openModal(this)">
                <div class="image-info">
                    <strong>檔案:</strong> {image_name}<br>
                    <strong>類別:</strong> {result['category']}<br>
                    <strong>大小:</strong> {os.path.getsize(result['image_path']) // 1024} KB
                </div>
            </div>

            <div class="content-area">
                <div class="image-header">
                    <h3 style="margin: 0; color: white;">測試 #{i}: {image_name}</h3>
                    <div>
                        <span class="score {score_class}">得分: {result['score']:.3f}</span>
                        <span style="margin-left: 15px;">⏱️ {result['time']:.1f}s</span>
                    </div>
                </div>

                <div class="progress-bar">
                    <div class="progress-fill" style="width: {result['score']*100}%"></div>
                </div>

                <div class="qa-section">"""

        # 添加問答內容
        if 'questions' in result and 'answers' in result:
            questions = result['questions']
            answers = result['answers']
            scores = result.get('scores', [0.5] * len(questions))

            for j, (q, a, s) in enumerate(zip(questions, answers, scores)):
                question_text = q['text'] if isinstance(q, dict) else str(q)
                html_content += f"""
                    <div class="question">
                        <strong>Q{j+1}:</strong> {question_text}
                        <span class="question-score">{s:.3f}</span>
                    </div>
                    <div class="answer">
                        <strong>A{j+1}:</strong> {a}
                    </div>"""
        else:
            html_content += f"""
                    <div class="answer">
                        <strong>測試結果:</strong> 圖片分析完成，得分 {result['score']:.3f}
                    </div>"""

        html_content += """
                </div>
            </div>
        </div>"""

    # 添加頁面結尾和 JavaScript
    html_content += f"""
        <div class="timestamp">
            報告生成時間: {timestamp} | 使用 {'Claude' if USE_CLAUDE else 'GPT-4o'} 視覺模型
        </div>
    </div>

    <!-- 圖片放大模態框 -->
    <div id="imageModal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>

    <script>
        function openModal(img) {{
            var modal = document.getElementById("imageModal");
            var modalImg = document.getElementById("modalImage");
            modal.style.display = "block";
            modalImg.src = img.src;
        }}

        function closeModal() {{
            var modal = document.getElementById("imageModal");
            modal.style.display = "none";
        }}

        // 點擊模態框背景關閉
        window.onclick = function(event) {{
            var modal = document.getElementById("imageModal");
            if (event.target == modal) {{
                modal.style.display = "none";
            }}
        }}

        // ESC 鍵關閉模態框
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                closeModal();
            }}
        }});

        // 頁面載入完成後的動畫效果
        document.addEventListener('DOMContentLoaded', function() {{
            const progressBars = document.querySelectorAll('.progress-fill');
            progressBars.forEach(bar => {{
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {{
                    bar.style.width = width;
                }}, 100);
            }});
        }});
    </script>
</body>
</html>"""

    return html_content

def main():
    """主函數"""
    print("🧪 簡化圖片測試系統")
    print("=" * 60)
    
    # 檢查 API 配置
    if USE_CLAUDE:
        # 檢查 AWS 憑證
        from dotenv import load_dotenv
        load_dotenv('.env')

        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        if not aws_access_key or not aws_secret_key:
            print("❌ 請在 .env 檔案中設置 AWS 憑證")
            print("   需要設定: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            return

        print(f"✅ 使用 Claude 模型: {os.getenv('BEDROCK_MODEL', 'anthropic.claude-3-sonnet-20240229-v1:0')}")
        print(f"✅ AWS 區域: {os.getenv('AWS_REGION', 'us-east-1')}")
    else:
        # 檢查 OpenAI API Key
        if not Config.OPENAI_API_KEY:
            print("❌ 請設置 OPENAI_API_KEY 環境變數")
            return
        print("✅ 使用 OpenAI GPT-4o 模型")
    
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
