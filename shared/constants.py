
# ================= API 配置 ====================
API_KEY = "sk-o1QYDOlis0gd3xDmpKyoyuCscLXDxclPDaM450tzL17XIFJy"
# API_KEY = "sk-3tNsGmdWcoa95je3fCQxWa5umbSecN6AZOFoK8nbX0fgp5xh"  # default
# API_KEY = "sk-rtN1YRXssJKv3QtHTnAE4lpZY8AkL6bCWrpK5FsfZ9KvOGVo"  # 国产
BASE_URL = "https://api.fate86.cn/v1"

# ================= 支持的模型列表 =================
MODEL_NAME_LIST = ["gemini-3-flash-preview", "gemini-2.5-pro-thinking", "deepseek-v3.2-thinking", "deepseek-chat"]


# ================= 存档中 meta 的默认参数 =================
DEFAULT_SYSTEM_PROMPT = """你是一只傲娇的猫娘"""  # 系统提示词 (Streamlit 允许我们在侧边栏动态修改这个内容)
DEFAULT_SETTINGS = {   # 这部分通常传给meta，跟随存档
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "model": MODEL_NAME_LIST[0],
    "history_len": 10,
}

# ================= Session 默认状态 (智能初始化字典) =================
# 前端初始化时会遍历这个字典，将其键值对同步到 st.session_state 中
INITIAL_SESSION_STATE = {
    "messages": [],
    "meta": DEFAULT_SETTINGS,
    "ui_prompt": DEFAULT_SYSTEM_PROMPT,
    "ui_model": MODEL_NAME_LIST[0],
    "ui_history_len": 10,
    "gemini_params": {"thinking_level": "high"},
    "file_path": None,
    "request_pending": False, # 是否正在请求中 (锁)
}

# ================= 应用常量 =================
# 定义本地配置文件名 (存放数据的存储路径，相当于软件的"首选项")
APP_CONFIG_FILE_NAME = "app_config.json"         # 应用配置文件，该文件是一个dict格式的json文件，{"meta":{...}, "messages":[...]}, 非常重要
DEFAULT_HISTORY_FILE_NAME = "chat_history.json"  # 默认聊天记录名
# 这里只定义"默认"路径字符串，不要在这里做 path join 计算或 makedirs，具体的路径计算逻辑移交给 storage.py 或 main.py 初始化阶段
DEFAULT_BASE_HISTORY_DIR = r"/mnt/c/Users/laplas/OneDrive/Laplas_OneDrive/Develop_Code_OneDrive/AI_Memory"  # 聊天记录保存路径 (WSL 挂载 Windows OneDrive)，拆分路径配置是为了方便扫描文件夹

# ================= 工具箱配置 =================
# 定义源文件夹列表 (你原来的所有项目路径都可以放这里)
SOURCE_CODE_DIRS = [
    r"/home/laplas/my_ai_project/LLM_client_app/services/",
    r"/home/laplas/my_ai_project/LLM_client_app/",
    r"/home/laplas/my_ai_project/LLM_client_app/backend/",
    r"/home/laplas/my_ai_project/LLM_client_app/frontend/",
    # r"C:\Users\laplas\OneDrive\MyProject\Another_Project",  # 可以无限添加
]

# 定义默认的输出目标文件夹 (如果不指定，脚本会自动在源文件夹下建子文件夹，但指定一个汇总文件夹更方便)
DEFAULT_EXPORT_DIR = r"/mnt/c/Users/laplas/OneDrive/Laplas_OneDrive/Develop_Code_OneDrive/script_output_files"


# ================= AI 工具描述表 (给大模型看的 Schema) =================
# 定义前端发给 AI 的工具列表，保持与后端提供的接口一致
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current real-world date and time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "当用户询问实时信息、新闻或我不具备的知识时使用。搜索互联网获取信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "针对搜索引擎优化的搜索关键词"}
                },
                "required": ["query"]
            }
        }
    }
]
