
# 负责初始化 Session State（内存）和简单的文件配置读取。

import json
import os
import time
import streamlit as st

# 自己的库
import shared.constants as const             # 导入全局常量模块
import backend.core.storage as core_storage  # 导入核心存储逻辑

# 这是前端的存储逻辑（存内存）

# ==================== 调试日志函数 ====================
def debug_log(message):
    print(f"🕵️ [DEBUG] {message}")


# 定义状态重置与初始化函数，只在刚开始加载还没有对话或加载新存档时候用
def reset_session_state(force=False):
    """
    智能驱动的 Session State 初始化或重置
    直接从 shared.constants.INITIAL_SESSION_STATE 获取配置，实现单点维护。
    """
    for key, value in const.INITIAL_SESSION_STATE.items():  # 循环遍历初始化配置
        if force or key not in st.session_state:  # 默认（ force = False 时）只初始化缺失的键
            st.session_state[key] = value

    if force or "init_done" not in st.session_state: # 避免无效重置，提升性能
        st.session_state.init_done = True
        print(f"🕵️ [DEBUG] ✅ Session State {'强制重置' if force else '初始化'}完成")



# =============== 文件操作 (UI 包装层) ===============

def get_history_dir():
    """获取历史记录目录，带 UI 错误提示"""
    # 检查配置文件是否存在
    if not os.path.exists(const.APP_CONFIG_FILE_NAME):
        return const.DEFAULT_BASE_HISTORY_DIR
    
    try:
        return core_storage.get_history_dir_path()
    # 捕获错误三连
    except json.JSONDecodeError as e:
        st.warning(f"⚠️ 配置文件格式错误，已使用默认路径。具体原因: {e}")
        return const.DEFAULT_BASE_HISTORY_DIR
    except PermissionError:
        st.error(f"❌ 权限不足：无法读取配置文件 {const.APP_CONFIG_FILE_NAME}")
        return const.DEFAULT_BASE_HISTORY_DIR
    except Exception as e:
        st.error(f"🔥 读取配置时发生未知错误: {e}")
        return const.DEFAULT_BASE_HISTORY_DIR


def save_app_config(new_dir):
    """保存新的路径设置到配置文件，带 UI 提示"""
    success = core_storage.save_app_config_data(new_dir)
    if not success:
        st.error("配置保存失败")
    return success


def load_history(file_path):  
    """读取历史记录，带 UI 提示"""
    try:
        return core_storage.load_history_data(file_path)
    except Exception as e:
        st.error(f"读取记录出错: {e}")
        return const.DEFAULT_SETTINGS, []


def save_history(meta=None, messages=None, file_path=None):
    """将数据保存到指定的路径，带 UI 提示"""
    if meta is None:
        meta = st.session_state.get("meta", {}) 
    if messages is None:
        messages = st.session_state.get("messages", [])
    if file_path is None:
        file_path = st.session_state.get("file_path", "")

    success = core_storage.save_history_data(meta, messages, file_path)
    if success:
        st.toast(f" [系统] ✅记忆已同步至: {const.DEFAULT_BASE_HISTORY_DIR}")
    else:
        print(f"保存失败: {file_path}")


# --- 定义删除功能的回调函数 ---
def delete_msg_callback(index):
    """点击删除按钮时触发的逻辑"""
    if 0 <= index < len(st.session_state.messages):
        del st.session_state.messages[index]
        save_history(
            st.session_state.meta, 
            st.session_state.messages, 
            st.session_state.file_path
        )
        st.toast("🗑️ 消息已删除")
    

# --- 定义更新配置进内存的回调函数
def sync_ui_to_meta():
    """只更新内存！将 UI 组件的值同步到 st.session_state.meta 中。"""
    if "meta" not in st.session_state: return

    if "ui_prompt" in st.session_state:
        st.session_state.meta["system_prompt"] = st.session_state.ui_prompt
    if "ui_history_len" in st.session_state:
        st.session_state.meta["history_len"] = st.session_state.ui_history_len
    
    if "ui_thinking" in st.session_state:
        val = st.session_state.ui_thinking.lower()
        st.session_state.meta["gemini_config"] = {"thinking_level": val}
        st.session_state.gemini_params = {"thinking_level": val}


def save_current_context_to_disk():
    """将当前的 Meta 和 Messages 写入硬盘"""
    if "file_path" in st.session_state and st.session_state.file_path:
        sync_ui_to_meta() 
        save_history(
            st.session_state.meta, 
            st.session_state.messages, 
            st.session_state.file_path
        )
        st.toast(f"Saved: {os.path.basename(st.session_state.file_path)}", icon="💾")


def on_param_change():
    """当任何 UI 组件发生变化时触发"""
    if "meta" in st.session_state:
        st.session_state.meta["system_prompt"] = st.session_state.ui_prompt
        st.session_state.meta["model"] = st.session_state.ui_model
        st.session_state.meta["history_len"] = st.session_state.ui_history_len
        if "ui_thinking" in st.session_state:
            val = st.session_state.ui_thinking.lower() 
            st.session_state.meta["gemini_config"] = {"thinking_level": val}
            st.session_state.gemini_params = {"thinking_level": val}

        if "file_path" in st.session_state and st.session_state.file_path:
            save_history(
                st.session_state.meta, 
                st.session_state.messages, 
                st.session_state.file_path
            )
            st.toast("配置已自动保存 💾")
