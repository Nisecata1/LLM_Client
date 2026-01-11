import time
import os
import json
import streamlit as st  


from shared import constants as const
from frontend.handlers import session_handler
from frontend import api_client


# 负责聊天请求的逻辑，与后端交互

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




def frontend_chat_request():
    """
    准备参数
    调用后端 API
    接收并渲染后端的响应
    """


    # --- 调试探针 ---
    if st.session_state.messages:
        last_msg = st.session_state.messages[-1]
        last_role = last_msg.get("role")
        pending_status = st.session_state.get("request_pending")
        session_handler.debug_log(f"🕵️ [PROBE] 最后一条消息角色: '{last_role}' (类型: {type(last_role)})")
        session_handler.debug_log(f"🕵️ [PROBE] request_pending 状态: {pending_status} (类型: {type(pending_status)})")
    else:
        session_handler.debug_log("🕵️ [PROBE] 消息列表为空")
    # ----------------

    session_handler.debug_log("检查请求锁")
    # 状态锁检查：如果已经在请求中，则不重复执行
    if (st.session_state.messages[-1]["role"] == "user") and (st.session_state.get("request_pending") == False):
        # 激活状态锁
        session_handler.debug_log("锁未激活，上锁并准备执行请求")
        st.session_state.request_pending = True
        session_handler.debug_log("request_pending = True, 请求上锁成功")
        st.toast("✅ 正在通过后端请求 AI...", icon="🤖")

        try:
            with st.chat_message("assistant"):
                # 获取 API 客户端
                client = api_client.get_api_client()
                
                session_handler.debug_log("正在构建消息上下文并发送给后端")
                # 获取滑动窗口长度
                ctx_len = int(st.session_state.get("ui_history_len", 10)) * 2
                # 构建并发送请求给后端: 只传消息列表，后端根据存档自取系统提示词等其余配置
                with st.status("AI 正在思考中...", expanded=True) as status:
                    response = client.chat(
                        messages = st.session_state.messages[-ctx_len:]  # 构建消息上下文 (滑动窗口)
                    )
                    
                    session_handler.debug_log("已获得后端 response，正在拆解...")
                    
                    if "status" in response and response["status"] == "error":
                        error_msg = response.get("message", "未知错误")
                        st.error(f"后端错误: {error_msg}")
                        status.update(label="请求失败", state="error")
                        # 追加错误消息到历史，打破“最后一条是user则不断重试”的逻辑循环
                        st.session_state.messages.append({"role": "assistant", "content": f"❌ 请求失败: {error_msg}"})
                        session_handler.save_history()
                        return

                    status.update(label="生成完成", state="complete")

                # 4. 渲染思维链和内容
                if response.get("reasoning"):
                    with st.expander("💭 查看思考过程"):
                        st.markdown(response["reasoning"])
                
                st.markdown(response["content"])

                # 5. 更新内存和硬盘
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response["content"],
                    "reasoning": response.get("reasoning"),
                    "tool_calls": response.get("tool_calls")
                })
                session_handler.save_history(st.session_state.meta, st.session_state.messages, st.session_state.file_path)

        except Exception as e:
            error_info = str(e)
            st.error(f"前端请求异常: {error_info}")
            # 追加异常消息到历史，彻底杜绝死循环
            st.session_state.messages.append({"role": "assistant", "content": f"🚨 系统异常: {error_info}"})
            session_handler.save_history()
        finally:
            # 释放状态锁
            st.session_state.request_pending = False
            # 强制刷新以同步 UI 状态（清除状态锁影响，如可能存在的禁用状态）
            st.rerun()
