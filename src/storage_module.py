import json
import os
import base64
import streamlit as st

# 自己的库
import src.constants as const  # 导入全局常量模块


# ==================== 调试日志函数 ====================
def debug_log(message):
    """把日志同时打在终端和网页侧边栏，防走丢"""
    print(f"🕵️ [DEBUG] {message}")
    # 也可以选择显示在网页上方便看
    # st.toast(message) 


# =============== 文件操作函数定义区 ===============
# get_history_dir、save_app_config、load_history、save_history
# 回调函数：delete_msg_callback、archive_current_chat

def get_history_dir():
    """
    该函数返回一个字符串，表示历史记录存储的目录路径。
    这个函数用于拿 app_config.json (默认配置文件) 中的路径，如果失败就使用const模块定义的默认路径。
    这样用户可以通过修改配置文件来改变聊天记录的存储位置，而不需要修改代码。
    """
    # 检查配置文件是否存在（防御性编程的第一步），没找到就用上面定义的默认路径
    if not os.path.exists(const.APP_CONFIG_FILE_NAME):
        return const.DEFAULT_BASE_HISTORY_DIR
    
    # 尝试读取配置文件内容（防御性编程的第二步）
    try:
        with open(const.APP_CONFIG_FILE_NAME, 'r', encoding='utf-8') as f:
            config = json.load(f)  # 反序列化：json.load 把 app_config.json 里的那串冷冰冰的字符，变回了可操作的 Python 字典 config
            return config.get("history_dir", const.DEFAULT_BASE_HISTORY_DIR)  # 用 config.get() 方法去拿里面的路径并返回
    # 精准捕获异常
    except json.JSONDecodeError as e:
        # 1. 专门处理 JSON 格式错误，这是最重要的改动。它能告诉你到底是哪一行、哪个字符写错了。在调试阶段，这能帮你节省几十个买小鱼干的时间！
        # 解释：比如文件里多了一个逗号，或者是个空文件。这种报错能让用户知道：喂！你的配置文件写坏了，快去修！
        st.warning(f"⚠️ 配置文件格式错误，已使用默认路径。具体原因: {e}")
        return const.DEFAULT_BASE_HISTORY_DIR
    except PermissionError:
        # 2. 处理权限问题
        # 解释：比如文件被其他程序占用，或者你没权限读那个文件夹。
        st.error(f"❌ 权限不足：无法读取配置文件 {const.APP_CONFIG_FILE_NAME}")
        return const.DEFAULT_BASE_HISTORY_DIR
    except Exception as e:
        # 3. 兜底捕获其他未知错误
        # 解释：防止一些极罕见的错误导致整个程序崩溃。
        st.error(f"🔥 读取配置时发生未知错误: {e}")
        return const.DEFAULT_BASE_HISTORY_DIR
    return const.DEFAULT_BASE_HISTORY_DIR


def save_app_config(new_dir):
    """保存新的路径设置到配置文件"""
    config = {"history_dir": new_dir}
    try:
        with open(const.APP_CONFIG_FILE_NAME, 'w', encoding='utf-8') as f:  # 写入模式打开config文件
            json.dump(config, f, indent=4, ensure_ascii=False)  # 将格式化的 JSON 写入config文件
        return True
    except Exception as e:
        st.error(f"配置保存失败: {e}")
        return False


def load_history(file_path):  
    """
    该函数打开 file_path 文件并读取其中的数据，返回一个元组 (元数据字典meta，消息列表message)
    读取历史记录,支持两种格式：
    1. 旧格式 (List): [{"role":...}, ...]  // list相当于c里的数组，数组元素为dict
    2. 新格式 (Dict): {"meta": {...}, "messages": [...]}
    """
    # 文件不存在，返回默认设置和空列表
    if not os.path.exists(file_path):
        return const.DEFAULT_SETTINGS, []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:  # 读取模式通过打开file_pathk路径的文件
            data = json.load(f)  # 反序列化给到data对象

        # 兼容性处理：支持旧版列表格式和新版字典格式
        # 判断格式
        if isinstance(data, dict) and "messages" in data:  # 如果是新格式 (包含 meta)
            return data.get("meta", const.DEFAULT_SETTINGS), data["messages"] # 返回元数据和消息列表（实际上是返回一个打包好的tuple）
        elif isinstance(data, list):  # 旧格式 (纯列表)
            return const.DEFAULT_SETTINGS, data  # 返回默认设置和消息列表
    except Exception as e:
        st.error(f"读取记录出错: {e}")
        return const.DEFAULT_SETTINGS, []


def save_history(meta=None, messages=None, file_path=None):
    """
    将传入的meta，messages，打包保存到指定的file_path路径，三个参数的默认值都从内存session拿
    meta: 元数据字典 (人设、温度、模型)
    messages: 消息列表
    file_path: 要存入的json文件路径
    """

    # 2. 函数体内部：这时候函数被调用了，session_state 肯定已经准备好了
    if meta is None:
        # 使用 .get() 避免如果 session_state 里没有 meta 时再次报错
        meta = st.session_state.get("meta", {}) 
    if messages is None:
        messages = st.session_state.get("messages", [])
    if file_path is None:
        file_path = st.session_state.get("file_path", "")


    # 构造新结构, 包含 meta 和 messages
    data = {"meta": meta,"messages": messages}

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:  # 打开file_path文件
            json.dump(data, f, ensure_ascii=False, indent=4)  # 将刚刚构建的data字典用json.dump方法序列化并写入file_path
        st.toast(f" [系统] ✅记忆已同步至: {const.DEFAULT_BASE_HISTORY_DIR}")  # 弹出提示小气泡
    except Exception as e:
        print(f"保存失败: {e}")



# --- 定义删除功能的回调函数 ---
def delete_msg_callback(index):
    """
    回调定义：点击删除按钮时触发的逻辑
    """
    # 1. 从内存移除指定索引的消息
    if 0 <= index < len(st.session_state.messages):
        del st.session_state.messages[index]  # 标注：利用 Python 的 del 关键字删除指定下标的元素
        # 2. 立即写入硬盘 (可选，建议放在这里保证持久性)
        save_history(
            st.session_state.meta, 
            st.session_state.messages, 
            st.session_state.file_path
        )
        # 注意：这里不需要写 st.rerun()，因为 on_click 触发的回调完成后，Streamlit 会自动触发 rerun。
        st.toast("🗑️ 消息已删除")
    


def sync_ui_to_meta():
    """
    只更新内存！将 UI 组件的值同步到 st.session_state.meta 中。
    不涉及任何硬盘读写。
    """
    if "meta" not in st.session_state: return

    # A. 基础参数
    if "ui_prompt" in st.session_state:
        st.session_state.meta["system_prompt"] = st.session_state.ui_prompt
    if "ui_history_len" in st.session_state:
        st.session_state.meta["history_len"] = st.session_state.ui_history_len
    
    # B. Thinking Level (UI -> API)
    if "ui_thinking" in st.session_state:
        val = st.session_state.ui_thinking.lower()
        st.session_state.meta["gemini_config"] = {"thinking_level": val}
        # 同时更新给 main.py 用的 params
        st.session_state.gemini_params = {"thinking_level": val}


def save_current_context_to_disk():
    """
    【手动/自动触发】将当前的 Meta 和 Messages 写入硬盘
    """
    if "file_path" in st.session_state and st.session_state.file_path:
        # 1. 保存前最后确认一次内存是最新的
        sync_ui_to_meta() 
        
        # 2. 写硬盘
        save_history(
            st.session_state.meta, 
            st.session_state.messages, 
            st.session_state.file_path
        )
        st.toast(f"Saved: {os.path.basename(st.session_state.file_path)}", icon="💾")


def on_param_change():
    """
    当任何 UI 组件发生变化时触发。
    它负责：同步 UI 状态 -> Meta 数据 -> 写入硬盘
    """
    # 确保 Meta 数据同步
    if "meta" in st.session_state:
        # 将 session_state 里所有最新的 UI 值更新到内存的 meta 中
        st.session_state.meta["system_prompt"] = st.session_state.ui_prompt
        st.session_state.meta["model"] = st.session_state.ui_model
        st.session_state.meta["history_len"] = st.session_state.ui_history_len
        # 同步 Thinking Level (简化版)
        # 逻辑：UI是 "High" -> API要是 "high" (转小写即可)
        if "ui_thinking" in st.session_state:
            val = st.session_state.ui_thinking.lower() 
            st.session_state.meta["gemini_config"] = {"thinking_level": val}
            st.session_state.gemini_params = {"thinking_level": val}

        # 保存到硬盘
        if "file_path" in st.session_state and st.session_state.file_path:
            save_history(
                st.session_state.meta, 
                st.session_state.messages, 
                st.session_state.file_path
            )
            st.toast("配置已自动保存 💾")


def archive_current_chat(path):
    """
    标注：这是回调函数，它会在在脚本重新渲染页面之前执行。
    作用：直接修改内存数据（数据总线）。并写回硬盘。
    注意：不能在这里修改 UI 组件的状态，因为此时页面还没开始重绘，修改会报错。
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    archive_filename = f"chat_history_{timestamp}.json"
    archive_path = os.path.join(const.DEFAULT_BASE_HISTORY_DIR, archive_filename)
    
    # A. 保存归档
    if len(st.session_state.messages) > 0:
        # 使用当前的 meta 和 messages 保存
        save_history(st.session_state.meta, st.session_state.messages, archive_path)
        # 重命名旧文件 (如果存在)
        if os.path.exists(path):
            os.rename(path, archive_path)  # 如果不是原名，这里我们简单处理：重命名当前文件
        st.toast(f"✅ 已归档: {archive_filename}")
    
    # B. 重置内存数据
    st.session_state.messages = []  # 清空消息列表
    st.session_state.meta = const.DEFAULT_SETTINGS  # 恢复默认设置
    
    # C. 重置 UI ，因为是在回调里修改，此时页面还没开始重绘，所以是合法的！
    st.session_state.ui_prompt = const.DEFAULT_SYSTEM_PROMPT
    st.session_state.ui_model = const.MODEL_NAME_LIST[0]

    # D. 创建新文件
    new_default_path = os.path.join(const.DEFAULT_BASE_HISTORY_DIR, "chat_history.json")
    save_history(const.DEFAULT_SETTINGS, [], new_default_path)
        


def encode_image_to_base64(uploaded_file):
    """将 Streamlit 的上传对象转换为 Base64 字符串"""
    bytes_data = uploaded_file.getvalue()
    base64_str = base64.b64encode(bytes_data).decode('utf-8')
    # 根据文件类型自动判断前缀
    mime_type = uploaded_file.type
    return f"data:{mime_type};base64,{base64_str}"






