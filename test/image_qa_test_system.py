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
    
    def generate_questions_from_image(self, image_path: str, num_questions: int = 5) -> Dict[str, Any]:
        """根據圖片內容生成問題"""
        try:
            # 編碼圖片
            base64_image = self.encode_image(image_path)

            # 構建提示詞
            # 動態生成問題格式
            question_format = "\n".join([f"{i}. [第{i}個問題]" for i in range(1, num_questions + 1)])

            prompt = f"""這是一張工程技術文件圖片，用於教育和技術分析目的。請協助分析這張技術圖片，並根據圖片中實際可見的內容生成 {num_questions} 個相關問題。

技術分析要求：
1. 這是合法的技術文件分析，用於工程教育
2. 只針對圖片中實際存在的技術內容提問
3. 問題應該基於可見的文字、圖表、技術規格、工程圖面等
4. 避免過於抽象或需要額外知識的問題
5. 確保問題可以通過觀察圖片來回答

問題類型建議：
- 描述性：圖片中顯示了什麼技術內容？
- 規格性：有哪些具體的技術規格或參數？
- 結構性：技術圖面的組成部分是什麼？

請嚴格按以下格式輸出：
{question_format}

這是正當的技術文件分析，請協助完成。"""

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
                max_tokens=1000,
                temperature=0.3
            )

            response_content = response.choices[0].message.content

            # 檢查是否被拒絕
            if self._is_refusal_response(response_content):
                logger.warning("檢測到拒絕回應，嘗試重新生成問題...")
                return {
                    "success": False,
                    "error": "Content policy refusal",
                    "response": None
                }

            return {
                "success": True,
                "response": response_content,
                "usage": response.usage.dict() if response.usage else None
            }

        except Exception as e:
            logger.error(f"生成問題失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    def _is_refusal_response(self, response: str) -> bool:
        """檢查回應是否為拒絕回應"""
        refusal_patterns = [
            "I'm sorry, I can't",
            "I can't assist",
            "I can't help",
            "I'm not able to",
            "I cannot",
            "I'm unable to",
            "I don't feel comfortable",
            "I can't provide",
            "I'm sorry, but I can't"
        ]

        response_lower = response.lower()
        return any(pattern.lower() in response_lower for pattern in refusal_patterns)

    def analyze_image_with_questions(self, image_path: str, questions: List[str]) -> Dict[str, Any]:
        """使用 GPT-4o 分析圖片並回答問題"""
        try:
            # 編碼圖片
            base64_image = self.encode_image(image_path)

            # 構建問題列表
            questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

            # 構建提示詞
            prompt = f"""這是一張工程技術文件圖片，用於教育和技術分析目的。請協助分析這張技術圖片，並根據圖片中的實際內容回答以下問題：

{questions_text}

技術分析要求：
1. 這是合法的技術文件分析，用於工程教育
2. 只基於圖片中可見的技術內容回答
3. 如果圖片中沒有相關信息，請說明"圖片中未顯示此信息"
4. 提供具體、準確的技術描述
5. 引用圖片中的具體文字、數字或技術元素

請嚴格按以下格式回答：
1. [第一個問題的詳細回答]
2. [第二個問題的詳細回答]
3. [第三個問題的詳細回答]
4. [第四個問題的詳細回答]
5. [第五個問題的詳細回答]

這是正當的技術文件分析，請協助提供專業的技術回答。"""

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

            response_content = response.choices[0].message.content

            # 檢查是否被拒絕
            if self._is_refusal_response(response_content):
                logger.warning("檢測到拒絕回應，嘗試使用預設問題...")
                return {
                    "success": False,
                    "error": "Content policy refusal",
                    "response": None
                }

            return {
                "success": True,
                "response": response_content,
                "usage": response.usage.dict() if response.usage else None
            }

        except Exception as e:
            logger.error(f"圖片分析失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def evaluate_answer_quality(self, question: str, answer: str, image_path: str) -> float:
        """評估回答品質 (0-1 分數) - 基於圖片內容"""
        try:
            # 編碼圖片
            base64_image = self.encode_image(image_path)

            evaluation_prompt = f"""請根據圖片內容評估以下回答的品質，給出 0-1 之間的分數：

問題: {question}
回答: {answer}

評估標準：
- 準確性 (40%): 回答是否準確描述了圖片中的實際內容
- 完整性 (30%): 回答是否涵蓋了問題的所有要點
- 專業性 (20%): 回答是否使用了適當的技術術語
- 清晰度 (10%): 回答是否清楚易懂

請仔細對比圖片內容與回答，只回答一個 0-1 之間的數字，保留三位小數。"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位專業的技術文件評估專家，能夠根據圖片內容準確評估回答品質。"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": evaluation_prompt
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
    
    def parse_questions(self, response_text: str) -> List[str]:
        """解析問題文本，提取各個問題"""
        questions = []
        lines = response_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 檢查是否是問題格式 (格式: "1. " 或 "2. " 等)
            if line.startswith(tuple(f"{i}. " for i in range(1, 21))):  # 支援最多20個問題
                question = line[3:].strip()  # 移除 "1. " 部分
                if question:
                    questions.append(question)

        # 如果沒有找到格式化的問題，嘗試按行分割
        if not questions:
            for line in lines:
                line = line.strip()
                if line and line.endswith('?'):  # 以問號結尾的可能是問題
                    questions.append(line)

        return questions

    def parse_answers(self, response_text: str, num_questions: int) -> List[str]:
        """解析回答文本，提取各個問題的答案 - 改進版本，支持多種格式"""
        logger.info(f"開始解析回答，預期 {num_questions} 個答案")
        logger.debug(f"原始回答文本:\n{response_text}")

        answers = []
        lines = response_text.split('\n')
        current_answer = ""

        # 方法1: 嘗試解析標準格式 "1. 2. 3."
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

        logger.info(f"標準格式解析結果: 找到 {len(answers)} 個答案")

        # 如果標準格式解析失敗，嘗試其他方法
        if len(answers) < num_questions:
            logger.warning("標準格式解析不足，嘗試替代方法...")
            answers = self._parse_answers_fallback(response_text, num_questions)

        # 確保答案數量正確
        while len(answers) < num_questions:
            answers.append("無法提供答案")

        # 記錄最終結果
        for i, answer in enumerate(answers[:num_questions], 1):
            logger.info(f"答案 {i}: {answer[:100]}{'...' if len(answer) > 100 else ''}")

        return answers[:num_questions]

    def _parse_answers_fallback(self, response_text: str, num_questions: int) -> List[str]:
        """備用解析方法 - 處理各種格式的回答"""
        answers = []

        # 方法2: 嘗試按段落分割
        paragraphs = [p.strip() for p in response_text.split('\n\n') if p.strip()]
        if len(paragraphs) >= num_questions:
            logger.info("使用段落分割方法")
            return paragraphs[:num_questions]

        # 方法3: 嘗試尋找其他編號格式
        import re
        patterns = [
            r'^\d+[\.\)]\s*(.+)',  # "1. " 或 "1) "
            r'^[（\(]\d+[）\)]\s*(.+)',  # "(1) " 或 "（1）"
            r'^[一二三四五六七八九十]+[\.\、]\s*(.+)',  # 中文數字
            r'^[A-Za-z][\.\)]\s*(.+)',  # "A. " 或 "a) "
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.MULTILINE)
            if len(matches) >= num_questions:
                logger.info(f"使用正則表達式模式: {pattern}")
                return matches[:num_questions]

        # 方法4: 按行分割，過濾空行
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        if len(lines) >= num_questions:
            logger.info("使用行分割方法")
            return lines[:num_questions]

        # 方法5: 如果所有方法都失敗，將整個回答作為一個答案
        if response_text.strip():
            logger.warning("所有解析方法失敗，使用整個回答作為單一答案")
            answers.append(response_text.strip())

        return answers
    
    def test_single_image(self, image_path: str, custom_questions: List[str] = None) -> Optional[TestResult]:
        """測試單張圖片 - 實現從圖片生成問題然後評估回答的流程"""
        start_time = time.time()

        try:
            # 檢查圖片是否存在
            if not os.path.exists(image_path):
                logger.error(f"圖片檔案不存在: {image_path}")
                return None

            logger.info(f"開始分析圖片: {os.path.basename(image_path)}")

            # 步驟1: 從圖片生成問題（如果沒有提供自定義問題）
            if custom_questions is None:
                logger.info("步驟1: 從圖片生成問題...")
                question_result = self.generate_questions_from_image(image_path, 5)

                if not question_result["success"]:
                    logger.warning(f"生成問題失敗: {question_result.get('error', 'Unknown error')}，使用預設問題")
                    questions = self.question_templates
                    logger.info(f"使用預設問題: {len(questions)} 個")
                else:
                    # 解析生成的問題
                    questions = self.parse_questions(question_result["response"])
                    logger.info(f"成功生成 {len(questions)} 個問題")

            else:
                questions = custom_questions
                logger.info(f"使用自定義問題: {len(questions)} 個")

            # 步驟2: 根據圖片回答問題
            logger.info("步驟2: 根據圖片回答問題...")
            analysis_result = self.analyze_image_with_questions(image_path, questions)

            if not analysis_result["success"]:
                logger.warning(f"圖片分析失敗: {analysis_result.get('error', 'Unknown error')}，使用預設回答")
                # 提供預設回答
                answers = [f"由於技術限制，無法分析此圖片內容來回答問題: {q.get('text', q) if isinstance(q, dict) else q}"
                          for q in questions]
                scores = [0.1] * len(questions)  # 給予最低分數
            else:
                # 解析答案
                response_text = analysis_result["response"]
                answers = self.parse_answers(response_text, len(questions))
                logger.info(f"成功獲得 {len(answers)} 個回答")

                # 步驟3: 評估每個答案的品質（基於圖片內容）
                logger.info("步驟3: 評估回答品質...")
                scores = []
                for i, (question, answer) in enumerate(zip(questions, answers)):
                    score = self.evaluate_answer_quality(question, answer, image_path)
                    scores.append(score)
                    logger.info(f"問題 {i+1} 得分: {score:.3f}")



            # 計算總體分數
            overall_score = sum(scores) / len(scores) if scores else 0.0
            analysis_time = time.time() - start_time

            logger.info(f"圖片測試完成，總體得分: {overall_score:.3f}，耗時: {analysis_time:.1f}秒")

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
