#!/usr/bin/env python3
"""
Amazon Bedrock Claude API 測試腳本
測試 Claude 模型在 AWS Bedrock 上的 API 呼叫功能
"""

import os
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# 載入 .env.bedrock 檔案
load_dotenv('.env.bedrock')

try:
    from anthropic import AnthropicBedrock
    print("✅ Anthropic Bedrock SDK 已安裝")
except ImportError:
    print("❌ 請安裝 Anthropic Bedrock SDK: pip install 'anthropic[bedrock]'")
    exit(1)

class BedrockClaudeTest:
    """Bedrock Claude API 測試類"""
    
    def __init__(self):
        """初始化測試環境"""
        self.client = None
        self.test_results = []
        
        # 可用的 Claude 模型
        self.available_models = {
            "claude-opus-4": "anthropic.claude-opus-4-20250514-v1:0",
            "claude-sonnet-4": "anthropic.claude-sonnet-4-20250514-v1:0", 
            "claude-sonnet-3.7": "anthropic.claude-3-7-sonnet-20250219-v1:0",
            "claude-haiku-3.5": "anthropic.claude-3-5-haiku-20241022-v1:0",
            "claude-sonnet-3.5": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "claude-haiku-3": "anthropic.claude-3-haiku-20240307-v1:0"
        }
        
        # 預設使用的模型 (使用可用的模型)
        self.default_model = "anthropic.claude-3-haiku-20240307-v1:0"
        
    def setup_client(self, aws_access_key: str = None, aws_secret_key: str = None,
                    aws_session_token: str = None, aws_region: str = None):
        """設定 Bedrock 客戶端"""
        try:
            # 從環境變數讀取憑證
            if not aws_access_key:
                aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            if not aws_secret_key:
                aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            if not aws_session_token:
                aws_session_token = os.getenv("AWS_SESSION_TOKEN")
            if not aws_region:
                aws_region = os.getenv("AWS_REGION", "us-east-1")

            # 如果有憑證，明確提供給客戶端
            if aws_access_key and aws_secret_key:
                self.client = AnthropicBedrock(
                    aws_access_key=aws_access_key,
                    aws_secret_key=aws_secret_key,
                    aws_session_token=aws_session_token,
                    aws_region=aws_region
                )
                print(f"✅ 使用環境變數憑證建立 Bedrock 客戶端 (區域: {aws_region})")
            else:
                # 使用預設 AWS 憑證提供者
                self.client = AnthropicBedrock(aws_region=aws_region)
                print(f"✅ 使用預設 AWS 憑證建立 Bedrock 客戶端 (區域: {aws_region})")

            return True

        except Exception as e:
            print(f"❌ 建立 Bedrock 客戶端失敗: {str(e)}")
            return False
    
    def test_simple_message(self, model: str = None, message: str = "Hello, Claude! 請用繁體中文回答。"):
        """測試簡單訊息"""
        if not self.client:
            return {"success": False, "error": "客戶端未初始化"}
            
        model = model or self.default_model
        
        try:
            print(f"\n🧪 測試簡單訊息 (模型: {model})")
            print(f"📝 輸入: {message}")
            
            start_time = time.time()
            
            response = self.client.messages.create(
                model=model,
                max_tokens=256,
                messages=[{"role": "user", "content": message}]
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                "success": True,
                "model": model,
                "input": message,
                "output": response.content[0].text if response.content else "",
                "response_time": response_time,
                "usage": getattr(response, 'usage', None)
            }
            
            print(f"✅ 回應: {result['output']}")
            print(f"⏱️ 回應時間: {response_time:.2f} 秒")
            
            if result['usage']:
                print(f"📊 Token 使用量: {result['usage']}")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "model": model,
                "input": message,
                "error": str(e)
            }
            print(f"❌ 測試失敗: {str(e)}")
            self.test_results.append(error_result)
            return error_result
    
    def test_conversation(self, model: str = None):
        """測試多輪對話"""
        if not self.client:
            return {"success": False, "error": "客戶端未初始化"}
            
        model = model or self.default_model
        
        try:
            print(f"\n🧪 測試多輪對話 (模型: {model})")
            
            messages = [
                {"role": "user", "content": "你好，我想了解 Wire Harness 線束的基本概念。"},
                {"role": "assistant", "content": "您好！Wire Harness（線束）是將多條電線或電纜組合在一起的組件，通常用於電子設備和汽車中。它可以保護電線、簡化安裝並提高可靠性。您想了解線束的哪個特定方面呢？"},
                {"role": "user", "content": "請詳細說明線束的主要組成部分。"}
            ]
            
            start_time = time.time()
            
            response = self.client.messages.create(
                model=model,
                max_tokens=512,
                messages=messages
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                "success": True,
                "model": model,
                "conversation": messages,
                "output": response.content[0].text if response.content else "",
                "response_time": response_time,
                "usage": getattr(response, 'usage', None)
            }
            
            print(f"✅ 回應: {result['output']}")
            print(f"⏱️ 回應時間: {response_time:.2f} 秒")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "model": model,
                "error": str(e)
            }
            print(f"❌ 對話測試失敗: {str(e)}")
            self.test_results.append(error_result)
            return error_result
    
    def test_technical_question(self, model: str = None):
        """測試技術問題回答"""
        if not self.client:
            return {"success": False, "error": "客戶端未初始化"}
            
        model = model or self.default_model
        
        technical_question = """
        請分析以下線束設計問題：
        1. LVDS 線束的特殊要求是什麼？
        2. 在高頻應用中，線束設計需要注意哪些關鍵因素？
        3. 如何確保線束的電磁相容性(EMC)？
        
        請提供詳細的技術分析和建議。
        """
        
        try:
            print(f"\n🧪 測試技術問題 (模型: {model})")
            
            start_time = time.time()
            
            response = self.client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": technical_question}]
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                "success": True,
                "model": model,
                "question_type": "technical",
                "output": response.content[0].text if response.content else "",
                "response_time": response_time,
                "usage": getattr(response, 'usage', None)
            }
            
            print(f"✅ 技術回應長度: {len(result['output'])} 字元")
            print(f"⏱️ 回應時間: {response_time:.2f} 秒")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "model": model,
                "question_type": "technical",
                "error": str(e)
            }
            print(f"❌ 技術問題測試失敗: {str(e)}")
            self.test_results.append(error_result)
            return error_result
    
    def run_all_tests(self, model: str = None):
        """執行所有測試"""
        print("🚀 開始執行 Bedrock Claude API 測試")
        print("=" * 50)
        
        model = model or self.default_model
        
        # 測試 1: 簡單訊息
        self.test_simple_message(model)
        
        # 測試 2: 多輪對話
        self.test_conversation(model)
        
        # 測試 3: 技術問題
        self.test_technical_question(model)
        
        # 顯示測試摘要
        self.show_test_summary()
    
    def show_test_summary(self):
        """顯示測試摘要"""
        print("\n" + "=" * 50)
        print("📊 測試摘要")
        print("=" * 50)
        
        successful_tests = [r for r in self.test_results if r.get('success', False)]
        failed_tests = [r for r in self.test_results if not r.get('success', False)]
        
        print(f"✅ 成功測試: {len(successful_tests)}")
        print(f"❌ 失敗測試: {len(failed_tests)}")
        
        if successful_tests:
            total_time = sum(r.get('response_time', 0) for r in successful_tests)
            avg_time = total_time / len(successful_tests)
            print(f"⏱️ 平均回應時間: {avg_time:.2f} 秒")
        
        if failed_tests:
            print("\n❌ 失敗的測試:")
            for test in failed_tests:
                print(f"  - {test.get('error', '未知錯誤')}")
    
    def save_results(self, filename: str = None):
        """儲存測試結果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bedrock_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"💾 測試結果已儲存至: {filename}")
        except Exception as e:
            print(f"❌ 儲存結果失敗: {str(e)}")

def main():
    """主函數"""
    print("🔧 Amazon Bedrock Claude API 測試工具")
    print("=" * 50)
    
    # 建立測試實例
    tester = BedrockClaudeTest()
    
    # 顯示可用模型
    print("📋 可用的 Claude 模型:")
    for name, model_id in tester.available_models.items():
        print(f"  - {name}: {model_id}")
    
    print(f"\n🎯 預設使用模型: {tester.default_model}")
    
    # 設定憑證 (您需要在這裡提供您的 AWS 憑證)
    print("\n🔐 設定 AWS 憑證...")
    
    # 方法 1: 直接提供憑證 (不建議在生產環境中硬編碼)
    # aws_access_key = "YOUR_ACCESS_KEY"
    # aws_secret_key = "YOUR_SECRET_KEY"
    # success = tester.setup_client(aws_access_key, aws_secret_key)
    
    # 方法 2: 使用環境變數或 AWS 預設憑證
    success = tester.setup_client()
    
    if not success:
        print("❌ 無法建立 Bedrock 客戶端，請檢查 AWS 憑證設定")
        return
    
    # 執行測試
    tester.run_all_tests()
    
    # 儲存結果
    tester.save_results()

if __name__ == "__main__":
    main()
