import time
import os
import json
import streamlit as st  


import shared.constants as const
import frontend.handlers.file_handler as storage
import frontend.api_client as api_client


def on_user_submit(user_text):
    """
    负责：
    1. 更新 Session State (让 UI 立即显示用户输入)
    2. 调用 API (让后端算)
    3. 接收结果再次更新 Session State (让 UI 显示 AI 回复)
    """
    # 1. UI 立即反馈
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    # 2. 调用后端
    client = api_client.get_api_client()
    response = client.chat(messages=st.session_state.messages)
    
    # 3. 处理结果
    st.session_state.messages.append({"role": "assistant", "content": response["content"]})
    
    # 4. 强制刷新驱动 UI 重绘
    st.rerun()




def archive_current_chat(path):
    """归档当前聊天"""
    # 1. 检查当前是否已经是归档过的对话（文件名不是默认的 chat_history.json）
    current_filename = os.path.basename(path)
    is_default_chat = (current_filename == const.DEFAULT_HISTORY_FILE_NAME)

    # 2. 如果是默认对话且有内容，则执行归档保存逻辑
    if is_default_chat and len(st.session_state.messages) > 0:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        archive_filename = f"chat_history_{timestamp}.json"
        archive_path = os.path.join(const.DEFAULT_BASE_HISTORY_DIR, archive_filename)
        
        storage.save_history(st.session_state.meta, st.session_state.messages, archive_path)
        # 如果旧的默认文件存在，将其重命名为归档文件（或者直接删除，因为上面save_history已经存了新文件）
        # 这里选择重命名旧文件以保留可能的元数据，或者如果save_history已经覆盖了，就没必要rename了
        # 但原来的逻辑里有 rename，我们保留逻辑的一致性，但加上条件
        if os.path.exists(path):
            try:
                os.rename(path, archive_path)
            except Exception as e:
                print(f"🕵️ [DEBUG] Rename failed: {e}")

        st.toast(f"✅ 已归档: {archive_filename}")
    elif not is_default_chat:
        st.toast("💡 当前已是归档对话，直接切换到新对话")
    
    # 3. 无论如何，都重置内存中的状态，回到默认的新对话
    storage.reset_session_state(force=True)

    new_default_path = os.path.join(const.DEFAULT_BASE_HISTORY_DIR, "chat_history.json")
    storage.save_history(const.DEFAULT_SETTINGS, [], new_default_path)
    
    # [极简架构] 重置为默认新对话后，也同步活跃存档路径
    from backend.core import storage
    storage.set_active_archive_path(new_default_path)
