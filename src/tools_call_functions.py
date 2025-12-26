

import json


# 测试中
# 这里包含真正的 Python 函数和给 AI 看的 JSON 定义

# ================= 1. 真正的 Python 函数 (干活的) =================
def web_search(query):
    """
    模拟联网搜索功能 (实际使用时可替换为 DuckDuckGo 或 Google API)
    """
    print(f"DEBUG: 正在搜索 [{query}] ...")
    
    # 这里我们先模拟返回结果，防止你还得配额外的 API Key
    # 等跑通了，你可以换成 requests.get("https://google.com/...")
    mock_results = {
        "query": query,
        "results": [
            {"title": "Python 3.13 新特性", "snippet": "Python 3.13 引入了无 GIL 模式 (No-GIL)..."},
            {"title": "Gemini 3.0 技术报告", "snippet": "Gemini 3.0 在推理能力上大幅提升，支持 Thinking 模式..."}
        ]
    }
    return json.dumps(mock_results, ensure_ascii=False)

# ================= 2. 工具映射表 (给代码用的) =================
# 这是一个字典，让程序知道 AI 叫 "web_search" 时该跑哪个函数
AVAILABLE_FUNCTIONS = {
    "web_search": web_search,
}

# ================= 3. 工具定义 Schema (给 AI 看的) =================
# 这是传给 client.chat.completions.create 的 tools 参数
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "web_search",  # 名称，必须和上面的函数名对应
            "description": "当用户询问实时信息、新闻或我不具备的知识时使用。搜索互联网获取信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string","description": "针对搜索引擎优化的搜索关键词"}
                },
                "required": ["query"]
            }
        }
    }
]