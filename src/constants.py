

'''
静态常量 (不会变的) 放在 constants.py。例如：默认 Prompt、UI 的布局宽窄、固定的文件名。
这些属于“代码的一部分”，改了它们相当于改代码逻辑，所以用 Python 变量更好（有 IDE 提示，无需 IO 读取）。
'''


# ================= 配置区域 ====================
API_KEY = "sk-o1QYDOlis0gd3xDmpKyoyuCscLXDxclPDaM450tzL17XIFJy"
# API_KEY = "sk-3tNsGmdWcoa95je3fCQxWa5umbSecN6AZOFoK8nbX0fgp5xh"  # default
# API_KEY = "sk-rtN1YRXssJKv3QtHTnAE4lpZY8AkL6bCWrpK5FsfZ9KvOGVo"  # 国产
BASE_URL = "https://api.fate86.cn/v1"


# ================= 支持的模型列表 =================
MODEL_NAME_LIST = ["gemini-3-flash-preview", "gemini-2.5-pro-thinking", "deepseek-v3.2-thinking", "deepseek-chat"]


# ================= 默认设置 =================
# 默认的人设和参数: meta 的默认参数
DEFAULT_SYSTEM_PROMPT = """你是一只傲娇的猫娘"""  # 系统提示词 (Streamlit 允许我们在侧边栏动态修改这个内容)
DEFAULT_SETTINGS = {   
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "model": MODEL_NAME_LIST[0],
    "history_len": 10,
}

# ================= 应用常量 =================
# 定义本地配置文件名 (存放数据的存储路径，相当于软件的"首选项")
APP_CONFIG_FILE_NAME = "app_config.json"         # 应用配置文件，该文件是一个dict格式的json文件，{"meta":{...}, "messages":[...]}, 非常重要
DEFAULT_HISTORY_FILE_NAME = "chat_history.json"  # 默认聊天记录名
# 这里只定义"默认"路径字符串，不要在这里做 path join 计算或 makedirs，具体的路径计算逻辑移交给 storage.py 或 main.py 初始化阶段
DEFAULT_BASE_HISTORY_DIR = r"/mnt/c/Users/laplas/OneDrive/Laplas_OneDrive/Develop_Code_OneDrive/AI_Memory"  # 聊天记录保存路径 (WSL 挂载 Windows OneDrive)，拆分路径配置是为了方便扫描文件夹

# # 获取当前聊天记录的存储路径，并确保该目录存在
# HISTORY_DIR = f.get_history_dir()
# os.makedirs(HISTORY_DIR, exist_ok=True)
    