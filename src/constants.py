
import os
import src.storage_files_option_function as f

# ================= 配置区域 ====================
API_KEY = "sk-o1QYDOlis0gd3xDmpKyoyuCscLXDxclPDaM450tzL17XIFJy"
BASE_URL = "https://api.fate86.cn/v1"
MODEL_NAME_LIST = ["gemini-3-flash-preview", "gpt-4o-mini", "deepseek-chat"]
# 定义本地配置文件名 (存放数据的存储路径，相当于软件的"首选项")
APP_CONFIG_FILE_NAME = "app_config.json"  # 该文件是一个dict格式的json文件，{"meta":{...}, "messages":[...]}, 非常重要
# 默认的人设和参数: meta 的默认参数
DEFAULT_SYSTEM_PROMPT = """你是一只傲娇的猫娘"""  # 系统提示词 (Streamlit 允许我们在侧边栏动态修改这个内容)
DEFAULT_SETTINGS = {   
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "temperature": 1.0,
    "model": MODEL_NAME_LIST[0]
}

# 聊天记录保存路径 (WSL 挂载 Windows OneDrive)，拆分路径配置是为了方便扫描文件夹
HISTORY_DIR = f"/mnt/c/Users/laplas/OneDrive/Laplas_OneDrive/Develop_Code_OneDrive/AI_Memory"  # 待扫描的路径 (只到文件夹这一层)
DEFAULT_FILE_NAME = "chat_history.json"  # 默认聊天记录文件名
os.makedirs(HISTORY_DIR, exist_ok=True)  # 确保文件夹存在

# 获取当前聊天记录的存储路径，并确保该目录存在
HISTORY_DIR = f.get_history_dir()
os.makedirs(HISTORY_DIR, exist_ok=True)
    