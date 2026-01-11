import json
from openai import OpenAI
from typing import List, Dict, Any, Optional

from shared import constants as const
from core import model_tools_call_functions as tools
from core import storage

class ChatEngine:
    def __init__(
            self, api_key: str = const.API_KEY, 
            base_url: str = const.BASE_URL
        ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def run_chat(
            self, 
            messages: List[Dict[str, Any]], 
            model: Optional[str] = None, 
            system_prompt: Optional[str] = None,
            params: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
        """
        执行完整的对话逻辑，包括自动工具调用循环。
        [极简架构]：优先从活跃存档中加载 Meta 信息作为配置。
        """
        # 0. 参数补全逻辑 (后端自主从活跃存档加载配置)
        from storage import get_active_archive_path, load_history_data
        active_path = get_active_archive_path()
        
        meta = {}
        if active_path:
            meta, _ = load_history_data(active_path)
        
        # 优先级：传入参数 > 存档 Meta > 常量默认值
        model = model or meta.get("model") or const.MODEL_NAME_LIST[0]
        system_prompt = system_prompt or meta.get("system_prompt") or const.DEFAULT_SYSTEM_PROMPT
        params = params or meta.get("gemini_config") or {"thinking_level": "high"}

        # 1. 准备请求消息
        request_messages = []
        if system_prompt:  # 整合系统提示
            request_messages.append({"role": "system", "content": system_prompt})
        
        # 消息转换：确保格式符合 OpenAI SDK 要求
        for msg in messages:
            m = {"role": msg["role"], "content": msg.get("content")}
            if msg.get("tool_calls"):
                m["tool_calls"] = msg["tool_calls"]
            if msg.get("tool_call_id"):
                m["tool_call_id"] = msg["tool_call_id"]
            request_messages.append(m)

        # 2. 构建基础参数
        api_kwargs = {
            "model": model,
            "messages": request_messages,
            "temperature": 1.0,
            "top_p": 0.95,
            "max_tokens": 4096, # 默认限制，防止溢出
        }

        # 注入工具 Schema
        tool_schema = tools.get_tools_schema()
        if tool_schema:
            api_kwargs["tools"] = tool_schema
            api_kwargs["tool_choice"] = "auto"

        # 注入 Gemini 特有配置 (如有)
        if params and "thinking_level" in params:
            level = params["thinking_level"].upper()
            extra_body = {
                "generationConfig": {
                    "thinkingConfig": {
                        "includeThoughts": True,
                        "thinking_level": level
                    }
                }
            }
            api_kwargs["extra_body"] = extra_body

        # 3. 第一轮请求
        response = self.client.chat.completions.create(**api_kwargs)
        message = response.choices[0].message
        
        # 处理思维链 (如有)
        reasoning = getattr(message, "reasoning_content", None)

        # 4. 检查是否需要调用工具
        if message.tool_calls:
            # 将 AI 的工具调用请求加入上下文
            request_messages.append(message)
            
            # 执行工具
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # 路由到本地函数
                func = tools.AVAILABLE_FUNCTIONS.get(function_name)
                if func:
                    result = func(**function_args)
                else:
                    result = f"Error: Function {function_name} not found."
                
                # 将结果加入上下文
                request_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            
            # 第二轮请求
            final_response = self.client.chat.completions.create(
                model=model,
                messages=request_messages,
                # 注意：第二轮通常不需要传 tools 了，除非你想支持多轮工具调用
            )
            final_message = final_response.choices[0].message
            return {
                "role": "assistant",
                "content": final_message.content,
                "reasoning": reasoning,
                "tool_calls": [t.model_dump() for t in message.tool_calls] if message.tool_calls else None
            }
        
        # 如果没有工具调用，直接返回
        return {
            "role": "assistant",
            "content": message.content,
            "reasoning": reasoning
        }

# 单例模式
_engine = None
def get_chat_engine():
    global _engine
    if _engine is None:
        _engine = ChatEngine()
    return _engine
