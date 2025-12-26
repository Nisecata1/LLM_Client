
import json
import os
import streamlit as st

import src.constants as c  # 导入全局常量模块

# ===============================================
# ===============文件操作函数定义区===============
# ===============================================
# get_history_dir、save_app_config、load_history、save_history函数

def get_history_dir():
    """
    这个函数用于拿 app_config.json (默认配置文件) 中的路径设置，如果没有找到该配置文件或读取失败，就返回一个默认路径。
    这样用户可以通过修改配置文件来改变聊天记录的存储位置，而不需要修改代码。
    该函数返回一个字符串，表示历史记录存储的目录路径。
    """
    default_dir = f"/mnt/c/Users/laplas/OneDrive/Laplas_OneDrive/Develop_Code_OneDrive/AI_Memory" 
    # 先显式检查文件是否存在（防御性编程的第一步）,没找到就用上面定义的默认路径
    if not os.path.exists(c.APP_CONFIG_FILE_NAME):
        return default_dir
    # 如果本地有配置文件，读取里面的路径，
    try:
        with open(c.APP_CONFIG_FILE_NAME, 'r', encoding='utf-8') as f:
            config = json.load(f)  # 反序列化：json.load 把 app_config.json 里的那串冷冰冰的字符，变回了可操作的 Python 字典 config
            return config.get("history_dir", default_dir)  # 用 config.get() 方法去拿里面的路径并返回
    
    # 下面是精准捕获异常的部分
    except json.JSONDecodeError as e:
        # 1. 专门处理 JSON 格式错误，这是最重要的改动。它能告诉你到底是哪一行、哪个字符写错了。在调试阶段，这能帮你节省几十个买小鱼干的时间！
        # 解释：比如文件里多了一个逗号，或者是个空文件。这种报错能让用户知道：喂！你的配置文件写坏了，快去修！
        st.warning(f"⚠️ 配置文件格式错误，已使用默认路径。具体原因: {e}")
        return default_dir
    except PermissionError:
        # 2. 处理权限问题
        # 解释：比如文件被其他程序占用，或者你没权限读那个文件夹。
        st.error(f"❌ 权限不足：无法读取配置文件 {c.APP_CONFIG_FILE_NAME}")
        return default_dir
    except Exception as e:
        # 3. 兜底捕获其他未知错误
        # 解释：防止一些极罕见的错误导致整个程序崩溃。
        st.error(f"🔥 读取配置时发生未知错误: {e}")
        return default_dir
    return default_dir

def save_app_config(new_dir):
    """保存新的路径设置到配置文件"""
    config = {"history_dir": new_dir}
    with open(c.APP_CONFIG_FILE_NAME, 'w', encoding='utf-8') as f:  # 写入模式打开config文件
        json.dump(config, f, indent=4)  # 将格式化的 JSON 写入config文件


def load_history(file_path):  
    """
    该函数打开 file_path 文件并读取，返回一个元组 (元数据字典meta，消息列表message)
    读取历史记录,支持两种格式：
    1. 旧格式 (List): [{"role":...}, ...]  // list相当于c里的数组，数组元素为dict
    2. 新格式 (Dict): {"meta": {...}, "messages": [...]}
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:  # 读取模式通过打开file_pathk路径的文件
                data = json.load(f)  # 读取并转成JSON给到data对象
            # 判断格式
            if isinstance(data, dict) and "messages" in data:
                return data.get("meta", c.DEFAULT_SETTINGS), data["messages"] # 返回消息列表和元数据（实际上是打包好的元组）
            elif isinstance(data, list):  # 旧格式 (纯列表)
                return c.DEFAULT_SETTINGS, data  # 返回默认设置和消息列表（也是一个打包好的元组）
        except Exception as e:
            st.error(f"读取记录出错: {e}")
            return c.DEFAULT_SETTINGS, []
    # 文件不存在，返回空
    return c.DEFAULT_SETTINGS, []

def save_history(meta, messages, file_path):
    """
    保存记录到指定路径的 JSON，现在会把 meta (人设、温度、模型) 一起打包保存
    file_path: 保存路径
    messages: 消息列表
    meta: 元数据字典 (人设、温度、模型)
    """
    # 构造新结构,包含传入的 meta 和 messages
    data = {
        "meta": meta,
        "messages": messages
    }
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:  # 打开file_path文件
            json.dump(data, f, ensure_ascii=False, indent=4)  # 将刚刚构建的data字典用json.dump方法序列化并写入file_path
        st.toast(f" [系统] ✅记忆已同步至: {c.HISTORY_DIR}")  # 弹出提示小气泡
    except Exception as e:
        print(f"保存失败: {e}")





