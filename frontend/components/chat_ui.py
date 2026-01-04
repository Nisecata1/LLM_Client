import json
import streamlit as st
import shared.constants as const           # 导入全局常量模块
import frontend.handlers.file_handler as storage           # 导入文件操作函数模块
import frontend.api_client as api

# 负责前端聊天的相关逻辑: 渲染消息、构建参数、向后端发送请求等等


def render_chat_area(messages):
    """只负责把 messages 列表渲染出来"""
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

def render_input_area():
    """只负责显示输入框，返回用户输入的内容"""
    return st.chat_input("请输入...")




def render_history_timeline():
    """渲染整个聊天历史记录的时间轴"""
    for i, msg in enumerate(st.session_state.messages):  
        # 创建遍历到的该条消息的一个上下文环境
        with st.chat_message(msg["role"]):  
            content = msg.get("content")  # 取出content

            # Case A: 多模态消息(List 类型: 包含base64图片和文字的)
            if isinstance(content, list):
                for item in content:
                    # 渲染 Base64 图片
                    if item.get("type") == "image_url":
                        img_url = item["image_url"]["url"]
                        st.image(img_url, width=300)  
                    # 渲染文本
                    elif item.get("type") == "text":
                        st.markdown(item["text"])  
            # Case B: 纯文本消息
            elif content:
                st.markdown(content)

            # 显示思维链 (如有)
            if msg.get("reasoning"):
                with st.expander("💭 查看思考过程"):
                    st.markdown(msg["reasoning"])

            # 显示工具调用记录 (如有)
            if msg.get("tool_calls"):
                with st.status("🔧 工具调用记录", state="complete"):
                    st.json(msg["tool_calls"])


            # 2. 管理工具气泡菜单
            with st.popover("🔧", help="管理"):
                new_content = st.text_area("编辑内容", value=content if content else "", height=150, key=f"edit_text_{i}")
                col_edit, col_del = st.columns([1, 1])
                
                if col_edit.button("💾 保存", key=f"save_btn_{i}"):
                    st.session_state.messages[i]["content"] = new_content
                    storage.save_history(st.session_state.meta, st.session_state.messages, st.session_state.file_path)
                    st.rerun()

                col_del.button( 
                    "🗑️ 删除", 
                    key=f"del_btn_{i}",
                    type="primary",
                    # 回调函数执行时机：用户点击该按钮时
                    on_click=storage.delete_msg_callback, args=(i,)
                )



def request_logic():
    """准备参数，调用后端 API，接收并渲染响应"""
    # 状态锁检查：如果已经在请求中，则不重复执行
    if st.session_state.get("request_pending"):
        return

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        # 激活状态锁
        st.session_state.request_pending = True
        st.toast("✅ 正在请求 AI (通过后端)...", icon="🤖")

        try:
            with st.chat_message("assistant"):
                # 1. 获取 API 客户端
                client = api.get_api_client()
                
                # 2. 构建消息上下文 (滑动窗口)
                ctx_len = int(st.session_state.get("ui_history_len", 10)) * 2
                recent_history = st.session_state.messages[-ctx_len:]

                # 3. 发送请求给后端
                # [极简架构]：只传消息列表，后端根据活跃存档自取配置
                with st.status("AI 正在思考中...", expanded=True) as status:
                    response = client.chat(
                        messages=recent_history
                    )
                    
                    if "status" in response and response["status"] == "error":
                        error_msg = response.get("message", "未知错误")
                        st.error(f"后端错误: {error_msg}")
                        status.update(label="请求失败", state="error")
                        # 追加错误消息到历史，打破“最后一条是user则不断重试”的逻辑循环
                        st.session_state.messages.append({"role": "assistant", "content": f"❌ 请求失败: {error_msg}"})
                        storage.save_history()
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
                storage.save_history(st.session_state.meta, st.session_state.messages, st.session_state.file_path)

        except Exception as e:
            error_info = str(e)
            st.error(f"前端请求异常: {error_info}")
            # 追加异常消息到历史，彻底杜绝死循环
            st.session_state.messages.append({"role": "assistant", "content": f"🚨 系统异常: {error_info}"})
            storage.save_history()
        finally:
            # 释放状态锁
            st.session_state.request_pending = False
            # 强制刷新以同步 UI 状态（清除状态锁影响，如可能存在的禁用状态）
            st.rerun()
