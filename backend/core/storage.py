import json
import os
import base64
import shared.constants as const

def base64_encode_image(bytes_data, mime_type):
    """将字节数据转换为 Base64 字符串 (不依赖 UI 框架)"""
    base64_str = base64.b64encode(bytes_data).decode('utf-8')
    return f"data:{mime_type};base64,{base64_str}"

def get_history_dir_path():
    """获取历史记录目录路径，不依赖 UI 框架"""
    if not os.path.exists(const.APP_CONFIG_FILE_NAME):
        return const.DEFAULT_BASE_HISTORY_DIR
    
    try:
        with open(const.APP_CONFIG_FILE_NAME, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("history_dir", const.DEFAULT_BASE_HISTORY_DIR)
    except:
        return const.DEFAULT_BASE_HISTORY_DIR

def get_app_config():
    """获取完整的本地配置文件数据"""
    if not os.path.exists(const.APP_CONFIG_FILE_NAME):
        return {}
    try:
        with open(const.APP_CONFIG_FILE_NAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_app_config_data(config_dict_or_dir):
    """保存配置数据到文件。兼容传入字典或单一路径字符串。"""
    if isinstance(config_dict_or_dir, str):
        # 兼容旧版本调用，如果传的是字符串，认为是 history_dir
        current_config = get_app_config()
        current_config["history_dir"] = config_dict_or_dir
        config = current_config
    else:
        # 否则认为是完整的配置字典
        config = config_dict_or_dir

    try:
        with open(const.APP_CONFIG_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_active_archive_path():
    """从本地配置获取当前活跃的存档文件路径"""
    return get_app_config().get("active_archive_path")

def set_active_archive_path(file_path):
    """设置当前活跃的存档文件路径到本地配置"""
    config = get_app_config()
    config["active_archive_path"] = file_path
    return save_app_config_data(config)

def load_history_data(file_path):
    """从指定路径加载历史记录数据"""
    if not os.path.exists(file_path):
        return const.DEFAULT_SETTINGS, []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict) and "messages" in data:
            return data.get("meta", const.DEFAULT_SETTINGS), data["messages"]
        elif isinstance(data, list):
            return const.DEFAULT_SETTINGS, data
    except Exception as e:
        print(f"Error loading history: {e}")
        return const.DEFAULT_SETTINGS, []

def save_history_data(meta, messages, file_path):
    """将数据保存到指定的 JSON 文件"""
    if not file_path:
        return False
        
    data = {"meta": meta, "messages": messages}
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error saving history to {file_path}: {e}")
        return False
