#!/usr/bin/env python3
"""
演示 HTML 報告功能的簡單測試
只測試 2 張圖片來展示 HTML 報告效果
"""

import os
import sys
import json
import time
from pathlib import Path

# 添加父目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(current_dir)

from image_qa_test_system import ImageQATestSystem
from config.config import Config

def main():
    """演示 HTML 報告功能"""
    print("🧪 HTML 報告演示測試")
    print("=" * 50)
    
    # 檢查 OpenAI API Key
    if not Config.OPENAI_API_KEY:
        print("❌ 請設置 OPENAI_API_KEY 環境變數")
        return
    
    # 初始化測試系統
    try:
        test_system = ImageQATestSystem()
        print("✅ 測試系統初始化成功")
    except Exception as e:
        print(f"❌ 測試系統初始化失敗: {e}")
        return
    
    # 選擇測試圖片 - 嘗試不同類型的圖片
    test_images = [
        "images/材料介紹._page_1.png",
        "images/Wire harness Introduction_page_1.png",
        "images/生產線學習_page_1.png"
    ]
    
    # 檢查圖片是否存在
    available_images = []
    for img_path in test_images:
        if os.path.exists(img_path):
            available_images.append(img_path)
        else:
            print(f"⚠️ 圖片不存在: {img_path}")
    
    if not available_images:
        print("❌ 沒有可用的測試圖片")
        return
    
    print(f"📸 將測試 {len(available_images)} 張圖片")
    
    # 執行測試
    all_results = []
    for i, image_path in enumerate(available_images, 1):
        image_name = os.path.basename(image_path)
        category = image_name.split('_')[0]
        
        print(f"\n[{i}/{len(available_images)}] 測試圖片: {image_name}")
        
        try:
            start_time = time.time()
            result = test_system.test_single_image(image_path)
            end_time = time.time()
            
            if result:
                score = result.overall_score
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
    
    # 生成 HTML 報告
    if all_results:
        print(f"\n📊 測試完成，共 {len(all_results)} 張圖片")
        save_html_report(all_results)
    else:
        print("❌ 沒有成功的測試結果")

def save_html_report(results):
    """保存 HTML 報告"""
    from collections import defaultdict
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    html_filename = f"demo_test_results_{timestamp}.html"
    
    # 計算統計數據
    total_images = len(results)
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
        <h1>🧪 圖片測試結果報告 (演示版)</h1>
        
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
            🤖 圖片測試系統 v2.0 - 基於 GPT-4o 視覺模型
            <br>
            ✨ 測試原理: 從圖片生成問題 → 根據圖片回答問題 → 評估回答品質
        </div>
    </div>
</body>
</html>"""
    
    # 保存 HTML 檔案
    try:
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"📄 HTML 報告已保存到: {html_filename}")
        
        # 也保存 JSON 備份
        json_filename = f"demo_test_results_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"📄 JSON 備份已保存到: {json_filename}")
        
    except Exception as e:
        print(f"❌ 保存報告失敗: {e}")

if __name__ == "__main__":
    main()
