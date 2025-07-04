#!/usr/bin/env python3
"""
集合數量檢查工具
用於檢查 Qdrant 集合中的向量數量和狀態資訊
"""

import logging
import time
from typing import Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from config import Config

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CollectionCountChecker:
    """集合數量檢查器"""
    
    def __init__(self, qdrant_url: Optional[str] = None):
        """
        初始化集合數量檢查器
        
        Args:
            qdrant_url: Qdrant 服務器 URL，如果不提供則使用配置文件中的預設值
        """
        self.qdrant_url = qdrant_url or Config.QDRANT_URL
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        logger.info(f"已連接到 Qdrant 服務器: {self.qdrant_url}")
    
    def check_collection_count(self, collection_name: str) -> Dict[str, Any]:
        """
        檢查指定集合的數量資訊
        
        Args:
            collection_name: 要檢查的集合名稱
            
        Returns:
            包含集合資訊的字典
        """
        try:
            # 檢查集合是否存在
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == collection_name for col in collections.collections)
            
            if not collection_exists:
                return {
                    "success": False,
                    "collection_name": collection_name,
                    "exists": False,
                    "error_message": f"集合 '{collection_name}' 不存在",
                    "vectors_count": 0,
                    "points_count": 0,
                    "status": "not_found",
                    "last_activity": time.time()
                }
            
            # 獲取集合詳細資訊
            collection_info = self.qdrant_client.get_collection(collection_name)
            vectors_count = collection_info.vectors_count
            points_count = collection_info.points_count
            
            # 處理 vectors_count 可能為 None 的情況（某些 Qdrant 版本）
            if vectors_count is None:
                vectors_count = points_count if points_count is not None else 0
                logger.info(f"集合 {collection_name} 的 vectors_count 為 None，使用 points_count: {vectors_count}")
            
            # 獲取集合配置資訊
            config_info = collection_info.config
            status = collection_info.status
            
            result = {
                "success": True,
                "collection_name": collection_name,
                "exists": True,
                "vectors_count": vectors_count,
                "points_count": points_count,
                "status": str(status),
                "config": {
                    "vector_size": config_info.params.vectors.size if hasattr(config_info.params, 'vectors') else None,
                    "distance": str(config_info.params.vectors.distance) if hasattr(config_info.params, 'vectors') else None,
                } if config_info else None,
                "last_activity": time.time(),
                "error_message": None
            }
            
            logger.info(f"集合 '{collection_name}' 檢查完成: {vectors_count} 個向量, {points_count} 個點")
            return result
            
        except UnexpectedResponse as e:
            error_msg = f"Qdrant 服務器回應錯誤: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "collection_name": collection_name,
                "exists": False,
                "error_message": error_msg,
                "vectors_count": 0,
                "points_count": 0,
                "status": "error",
                "last_activity": time.time()
            }
        except Exception as e:
            error_msg = f"檢查集合時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "collection_name": collection_name,
                "exists": False,
                "error_message": error_msg,
                "vectors_count": 0,
                "points_count": 0,
                "status": "error",
                "last_activity": time.time()
            }
    
    def check_all_collections(self) -> Dict[str, Any]:
        """
        檢查所有集合的數量資訊
        
        Returns:
            包含所有集合資訊的字典
        """
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if not collection_names:
                return {
                    "success": True,
                    "total_collections": 0,
                    "collections": [],
                    "summary": {
                        "total_vectors": 0,
                        "total_points": 0,
                        "healthy_collections": 0,
                        "error_collections": 0
                    },
                    "last_activity": time.time()
                }
            
            results = []
            total_vectors = 0
            total_points = 0
            healthy_count = 0
            error_count = 0
            
            for collection_name in collection_names:
                collection_result = self.check_collection_count(collection_name)
                results.append(collection_result)
                
                if collection_result["success"]:
                    total_vectors += collection_result["vectors_count"]
                    total_points += collection_result["points_count"]
                    healthy_count += 1
                else:
                    error_count += 1
            
            return {
                "success": True,
                "total_collections": len(collection_names),
                "collections": results,
                "summary": {
                    "total_vectors": total_vectors,
                    "total_points": total_points,
                    "healthy_collections": healthy_count,
                    "error_collections": error_count
                },
                "last_activity": time.time()
            }
            
        except Exception as e:
            error_msg = f"檢查所有集合時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg,
                "total_collections": 0,
                "collections": [],
                "last_activity": time.time()
            }
    
    def get_collection_statistics(self, collection_name: str) -> Dict[str, Any]:
        """
        獲取集合的詳細統計資訊
        
        Args:
            collection_name: 集合名稱
            
        Returns:
            集合統計資訊
        """
        try:
            # 基本資訊檢查
            basic_info = self.check_collection_count(collection_name)
            
            if not basic_info["success"] or not basic_info["exists"]:
                return basic_info
            
            # 獲取更詳細的統計資訊
            try:
                # 嘗試獲取一些樣本點來分析
                sample_points = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=10,  # 只取少量樣本
                    with_payload=True,
                    with_vectors=False
                )
                
                sample_count = len(sample_points[0]) if sample_points[0] else 0
                
                # 分析 payload 結構
                payload_keys = set()
                if sample_points[0]:
                    for point in sample_points[0]:
                        if point.payload:
                            payload_keys.update(point.payload.keys())
                
                basic_info.update({
                    "sample_count": sample_count,
                    "payload_keys": list(payload_keys),
                    "has_payload": len(payload_keys) > 0
                })
                
            except Exception as e:
                logger.warning(f"無法獲取集合 {collection_name} 的詳細統計: {e}")
                basic_info["warning"] = f"無法獲取詳細統計: {str(e)}"
            
            return basic_info
            
        except Exception as e:
            error_msg = f"獲取集合統計時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "collection_name": collection_name,
                "error_message": error_msg,
                "last_activity": time.time()
            }


def main():
    """主函數 - 命令行介面"""
    import argparse
    
    parser = argparse.ArgumentParser(description="檢查 Qdrant 集合數量")
    parser.add_argument("--collection", "-c", type=str, help="指定要檢查的集合名稱")
    parser.add_argument("--all", "-a", action="store_true", help="檢查所有集合")
    parser.add_argument("--stats", "-s", action="store_true", help="顯示詳細統計資訊")
    parser.add_argument("--url", type=str, help="Qdrant 服務器 URL")
    
    args = parser.parse_args()
    
    # 初始化檢查器
    checker = CollectionCountChecker(qdrant_url=args.url)
    
    try:
        if args.all:
            # 檢查所有集合
            result = checker.check_all_collections()
            print("\n=== 所有集合檢查結果 ===")
            print(f"總集合數: {result.get('total_collections', 0)}")
            
            if result["success"] and result.get("collections"):
                print(f"總向量數: {result['summary']['total_vectors']}")
                print(f"總點數: {result['summary']['total_points']}")
                print(f"健康集合: {result['summary']['healthy_collections']}")
                print(f"錯誤集合: {result['summary']['error_collections']}")
                print("\n各集合詳情:")
                
                for collection in result["collections"]:
                    status_icon = "✅" if collection["success"] else "❌"
                    print(f"{status_icon} {collection['collection_name']}: "
                          f"{collection.get('vectors_count', 0)} 向量, "
                          f"{collection.get('points_count', 0)} 點")
            else:
                print("❌ 檢查失敗或無集合")
                
        elif args.collection:
            # 檢查指定集合
            if args.stats:
                result = checker.get_collection_statistics(args.collection)
            else:
                result = checker.check_collection_count(args.collection)
            
            print(f"\n=== 集合 '{args.collection}' 檢查結果 ===")
            
            if result["success"]:
                print(f"✅ 集合存在")
                print(f"向量數量: {result['vectors_count']}")
                print(f"點數量: {result['points_count']}")
                print(f"狀態: {result['status']}")
                
                if args.stats and "payload_keys" in result:
                    print(f"樣本數量: {result.get('sample_count', 0)}")
                    print(f"Payload 欄位: {result.get('payload_keys', [])}")
                    print(f"包含 Payload: {result.get('has_payload', False)}")
            else:
                print(f"❌ 檢查失敗: {result.get('error_message', '未知錯誤')}")
        else:
            # 使用預設集合名稱
            default_collection = Config.QDRANT_COLLECTION_NAME
            result = checker.check_collection_count(default_collection)
            
            print(f"\n=== 預設集合 '{default_collection}' 檢查結果 ===")
            
            if result["success"]:
                print(f"✅ 集合存在")
                print(f"向量數量: {result['vectors_count']}")
                print(f"點數量: {result['points_count']}")
                print(f"狀態: {result['status']}")
            else:
                print(f"❌ 檢查失敗: {result.get('error_message', '未知錯誤')}")
                
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用戶中斷")
    except Exception as e:
        print(f"\n❌ 程式執行錯誤: {e}")


if __name__ == "__main__":
    main()
