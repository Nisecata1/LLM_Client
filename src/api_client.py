"""
API 客户端模块 - 用于调用 FastAPI 后端服务

这个模块封装了所有与后端 API 的通信逻辑，实现前后端分离。
前端（Streamlit）通过这个模块调用后端服务，而不是直接调用本地函数。
"""

import requests
from typing import Dict, Any, Optional
import streamlit as st


class APIClient:
    """API 客户端类，封装所有后端调用"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """
        初始化 API 客户端
        
        Args:
            base_url: FastAPI 后端的基础 URL，默认是本地开发服务器
        """
        self.base_url = base_url
        
    def convert_py_to_txt(self, source_paths: list, target_path: Optional[str] = None) -> Dict[str, Any]:
        """
        调用后端批量转换 Python 文件为 TXT 文件
        
        Args:
            source_paths: 源文件夹路径列表
            target_path: 目标文件夹路径（可选）
            
        Returns:
            包含转换结果的字典
            
        Raises:
            requests.exceptions.ConnectionError: 无法连接到后端服务
            Exception: 其他请求错误
        """
        # 构造 API 端点 URL
        api_url = f"{self.base_url}/api/tools/convert/py-to-txt"
        
        # 构造请求体
        payload = {
            "source_paths": source_paths,
            "target_path": target_path
        }
        
        try:
            # 发送 POST 请求到 FastAPI 后端
            response = requests.post(api_url, json=payload, timeout=30)
            
            # 检查响应状态
            if response.status_code == 200:
                return response.json()
            else:
                # 返回错误信息
                return {
                    "status": "error",
                    "message": f"API 返回错误状态码: {response.status_code}",
                    "details": response.text
                }
                
        except requests.exceptions.ConnectionError:
            # 连接错误 - 后端服务可能没有运行
            return {
                "status": "error",
                "message": "无法连接到后端服务！请确保 FastAPI 后端正在运行。",
                "details": "运行命令: `python backend/main.py`"
            }
        except requests.exceptions.Timeout:
            # 请求超时
            return {
                "status": "error",
                "message": "请求超时，后端服务响应时间过长。",
                "details": "请检查后端服务是否正常运行"
            }
        except Exception as e:
            # 其他错误
            return {
                "status": "error",
                "message": f"请求出错: {str(e)}",
                "details": str(e)
            }


# 创建全局 API 客户端实例
# 注意：这里使用单例模式，确保整个应用使用同一个客户端实例
_api_client = None

def get_api_client() -> APIClient:
    """
    获取 API 客户端实例（单例模式）
    
    Returns:
        APIClient 实例
    """
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client


def test_backend_connection() -> bool:
    """
    测试后端连接是否正常
    
    Returns:
        bool: 连接是否成功
    """
    try:
        # 尝试访问后端健康检查接口
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        return response.status_code == 200
    except:
        return False