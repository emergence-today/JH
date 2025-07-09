#!/usr/bin/env python3
"""
圖片問答測試系統
基於 OpenAI GPT-4o 視覺模型的圖片分析和問答測試
"""

import os
import base64
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
from config.config import Config

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """測試結果數據類"""
    image_path: str
    questions: List[Dict[str, Any]]
    answers: List[str]
    scores: List[float]
    overall_score: float
    analysis_time: float
    error_message: Optional[str] = None

class ImageQATestSystem:
    """圖片問答測試系統"""
    
    def __init__(self, api_key: str = None):
        """初始化測試系統"""
        self.api_key = api_key or Config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("需要提供 OpenAI API Key")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # 使用 GPT-4o 視覺模型
        
        # 預設問題模板
        self.question_templates = [
            "請描述這張圖片中的主要內容和技術要點。",
            "這張圖片展示了什麼類型的技術文件或工程圖面？",
            "圖片中有哪些重要的技術規格、尺寸或標註？",
            "這張圖片的內容屬於哪個技術領域或應用場景？",
            "從品質管理的角度，這張圖片包含了哪些關鍵資訊？"
        ]
    
    def encode_image(self, image_path: str) -> str:
        """將圖片編碼為 base64 格式"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"圖片編碼失敗: {e}")
            raise
    
    def analyze_image_with_questions(self, image_path: str, questions: List[str] = None) -> Dict[str, Any]:
        """使用 GPT-4o 分析圖片並回答問題"""
        if questions is None:
            questions = self.question_templates
        
        try:
            # 編碼圖片
            base64_image = self.encode_image(image_path)
            
            # 構建問題列表
            questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
            
            # 構建提示詞
            prompt = f"""請仔細分析這張圖片，並回答以下問題：

{questions_text}

請為每個問題提供詳細、準確的回答。如果圖片中沒有相關資訊，請明確說明。

回答格式：
1. [第一個問題的回答]
2. [第二個問題的回答]
...

請確保回答專業、準確且具體。"""

            # 調用 OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "usage": response.usage.dict() if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"圖片分析失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def evaluate_answer_quality(self, question: str, answer: str, image_context: str = "") -> float:
        """評估回答品質 (0-1 分數)"""
        try:
            evaluation_prompt = f"""請評估以下回答的品質，給出 0-1 之間的分數：

問題: {question}
回答: {answer}
圖片背景: {image_context}

評估標準：
- 準確性 (40%): 回答是否準確描述了圖片內容
- 完整性 (30%): 回答是否涵蓋了問題的所有要點
- 專業性 (20%): 回答是否使用了適當的技術術語
- 清晰度 (10%): 回答是否清楚易懂

請只回答一個 0-1 之間的數字，保留三位小數。"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一位專業的技術文件評估專家。"},
                    {"role": "user", "content": evaluation_prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            # 提取分數
            score_text = response.choices[0].message.content.strip()
            try:
                score = float(score_text)
                return max(0.0, min(1.0, score))  # 確保分數在 0-1 範圍內
            except ValueError:
                logger.warning(f"無法解析評估分數: {score_text}")
                return 0.5  # 預設分數
                
        except Exception as e:
            logger.error(f"評估回答品質失敗: {e}")
            return 0.5  # 預設分數
    
    def parse_answers(self, response_text: str, num_questions: int) -> List[str]:
        """解析回答文本，提取各個問題的答案"""
        answers = []
        lines = response_text.split('\n')
        current_answer = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 檢查是否是新問題的開始 (格式: "1. " 或 "2. " 等)
            if line.startswith(tuple(f"{i}. " for i in range(1, num_questions + 1))):
                if current_answer:
                    answers.append(current_answer.strip())
                current_answer = line[3:]  # 移除 "1. " 部分
            else:
                if current_answer:
                    current_answer += " " + line
        
        # 添加最後一個答案
        if current_answer:
            answers.append(current_answer.strip())
        
        # 確保答案數量正確
        while len(answers) < num_questions:
            answers.append("無法提供答案")
        
        return answers[:num_questions]
    
    def test_single_image(self, image_path: str, custom_questions: List[str] = None) -> Optional[TestResult]:
        """測試單張圖片"""
        start_time = time.time()
        
        try:
            # 檢查圖片是否存在
            if not os.path.exists(image_path):
                logger.error(f"圖片檔案不存在: {image_path}")
                return None
            
            # 使用自定義問題或預設問題
            questions = custom_questions or self.question_templates
            
            # 分析圖片
            logger.info(f"開始分析圖片: {os.path.basename(image_path)}")
            analysis_result = self.analyze_image_with_questions(image_path, questions)
            
            if not analysis_result["success"]:
                logger.error(f"圖片分析失敗: {analysis_result.get('error', 'Unknown error')}")
                return TestResult(
                    image_path=image_path,
                    questions=[],
                    answers=[],
                    scores=[],
                    overall_score=0.0,
                    analysis_time=time.time() - start_time,
                    error_message=analysis_result.get('error', 'Analysis failed')
                )
            
            # 解析答案
            response_text = analysis_result["response"]
            answers = self.parse_answers(response_text, len(questions))
            
            # 評估每個答案的品質
            scores = []
            for i, (question, answer) in enumerate(zip(questions, answers)):
                score = self.evaluate_answer_quality(question, answer, f"技術圖片: {os.path.basename(image_path)}")
                scores.append(score)
                logger.info(f"問題 {i+1} 得分: {score:.3f}")
            
            # 計算總體分數
            overall_score = sum(scores) / len(scores) if scores else 0.0
            analysis_time = time.time() - start_time
            
            logger.info(f"圖片分析完成，總體得分: {overall_score:.3f}，耗時: {analysis_time:.1f}秒")
            
            # 創建問題字典列表
            question_dicts = [{"text": q, "index": i+1} for i, q in enumerate(questions)]
            
            return TestResult(
                image_path=image_path,
                questions=question_dicts,
                answers=answers,
                scores=scores,
                overall_score=overall_score,
                analysis_time=analysis_time
            )
            
        except Exception as e:
            logger.error(f"測試圖片時發生錯誤: {e}")
            return TestResult(
                image_path=image_path,
                questions=[],
                answers=[],
                scores=[],
                overall_score=0.0,
                analysis_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def batch_test_images(self, image_paths: List[str], custom_questions: List[str] = None) -> List[TestResult]:
        """批量測試多張圖片"""
        results = []
        total_images = len(image_paths)
        
        logger.info(f"開始批量測試 {total_images} 張圖片")
        
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"處理第 {i}/{total_images} 張圖片: {os.path.basename(image_path)}")
            
            result = self.test_single_image(image_path, custom_questions)
            if result:
                results.append(result)
            
            # 避免 API 限制，添加短暫延遲
            if i < total_images:
                time.sleep(1)
        
        logger.info(f"批量測試完成，成功處理 {len(results)}/{total_images} 張圖片")
        return results

if __name__ == "__main__":
    # 測試範例
    test_system = ImageQATestSystem()
    
    # 測試單張圖片
    test_image = "images/圖面識別教材_page_1.png"
    if os.path.exists(test_image):
        result = test_system.test_single_image(test_image)
        if result:
            print(f"測試結果: {result.overall_score:.3f}")
            for i, (q, a, s) in enumerate(zip(result.questions, result.answers, result.scores)):
                print(f"Q{i+1}: {q['text']}")
                print(f"A{i+1}: {a}")
                print(f"Score: {s:.3f}\n")
    else:
        print(f"測試圖片不存在: {test_image}")
