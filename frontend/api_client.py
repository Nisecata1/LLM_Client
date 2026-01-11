# 原 backend_api_client (唯一与后端通信的管道)
"""
API 客户端模块 - 用于调用 FastAPI 后端服务
这个模块封装了所有与后端 API 的通信逻辑，实现前后端分离。
前端（Streamlit）通过这个模块调用后端服务，而不是直接调用本地函数。
"""

import requests
from typing import Dict, List, Any, Optional  # 导入类型提示
import streamlit as st

from shared import constants as const


class APIClient:
    """API 客户端类，封装所有后端调用"""
    
    def __init__(self, base_url: str = const.BACKEND_URL):
        """
        初始化 API 客户端
        Args:
            base_url: FastAPI 后端的基础 URL，默认是本地开发服务器
        """
        self.base_url = base_url
        
    def chat(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """发送聊天上下文到后端"""
        api_url = f"{self.base_url}/api/chat/chat"
        payload = {"messages": messages}
        
        # 复用通用的 _post 方法，并指定较长的超时时间供大模型思考
        result = self._post(api_url, payload, timeout=60)
        
        # 为了兼容聊天界面的格式要求，如果返回的是错误字典，进行适配
        if isinstance(result, dict) and result.get("status") == "error":
            return {
                "role": "assistant", 
                "content": f"❌ {result.get('message')}\n\n详情: {result.get('details')}"
            }
        return result


    def convert_py_to_txt(self, source_paths: list, target_path: Optional[str] = None) -> Dict[str, Any]:
        """调用后端批量转换 Python 文件为 TXT 文件"""
        api_url = f"{self.base_url}/api/tools/convert/py-to-txt"
        payload = {"source_paths": source_paths, "target_path": target_path}
        return self._post(api_url, payload)

    def get_current_time(self) -> Dict[str, Any]:
        """从后端获取当前系统时间"""
        # 构建请求地址
        api_url = f"{self.base_url}/api/tools/time"
        return self._get(api_url)

    def web_search(self, query: str) -> Dict[str, Any]:
        """通过后端执行联网搜索"""
        api_url = f"{self.base_url}/api/tools/search"
        payload = {"query": query}
        return self._post(api_url, payload)

    def _post(self, url: str, json_data: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """
        通用的 POST 请求方法，发送JSON数据并处理API响应
        
        参数:
            url (str): 目标API的完整URL地址
            json_data (Dict[str, Any]): 要发送的JSON格式数据
            timeout (int): 超时时间，默认30秒
        """
        try:
            response = requests.post(url, json=json_data, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "message": f"API 错误: {response.status_code}", "details": response.text}
        except Exception as e:
            return self._handle_error(e)

    def _get(self, url: str) -> Dict[str, Any]:
        """通用的 GET 请求方法"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "message": f"API 错误: {response.status_code}", "details": response.text}
        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, e: Exception) -> Dict[str, Any]:
        """统一错误处理"""
        if isinstance(e, requests.exceptions.ConnectionError):
            return {"status": "error", "message": "无法连接到后端服务！", "details": "运行命令: `python backend/main.py`"}
        return {"status": "error", "message": f"请求出错: {str(e)}", "details": str(e)}


# 创建全局 API 客户端实例, 这里使用单例模式，确保整个应用使用同一个客户端实例
# 单例模式 (Singleton Pattern) 是一种常用的软件设计模式
# 它的核心思想是：确保一个类只有一个实例，并提供一个全局访问点来获取它。
_api_client = None

def get_api_client() -> APIClient:
    """
    获取 API 客户端实例（单例模式）
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
        # 尝试访问后端健康检查接口，统一使用常量配置
        response = requests.get(const.BACKEND_URL, timeout=5)
        return response.status_code == 200
    except:
        return False
