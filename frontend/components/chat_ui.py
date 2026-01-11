import json
import streamlit as st
import shared.constants as const                        # 导入全局常量模块
from frontend.handlers import session_handler,chat_handler 
import frontend.api_client as api

# 负责前端聊天的相关逻辑: 渲染消息、构建参数、向后端发送请求等等



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
                    session_handler.save_history(st.session_state.meta, st.session_state.messages, st.session_state.file_path)
                    st.rerun()

                col_del.button( 
                    "🗑️ 删除", 
                    key=f"del_btn_{i}",
                    type="primary",
                    # 回调函数执行时机：用户点击该按钮时
                    on_click=session_handler.delete_msg_callback, args=(i,)
                )


























def user_input_area():
    
    # 创建上传图片按钮
    col_upload, col_space = st.columns([1, 8])  # 创建两列，左边放个小的回形针按钮，右边留空
    with col_upload:
        with st.popover("📎", help="上传图片"):  # 变成一个气泡菜单，图标是回形针
            uploaded_file = st.file_uploader("选择图片", type=["png", "jpg", "jpeg"], key="img_uploader")

    session_handler.debug_log(f"准备初始化锁...")
    st.session_state.request_pending = False
    session_handler.debug_log(f"初始化完成")

    # st.chat_input 是st内置的方法, 类似于 input()，
    # disabled 控制输入框是否禁用，通过状态锁 request_pending 决定
    if user_input := st.chat_input(
                        "Shift+Enter 换行...输入你的问题...",
                        disabled = st.session_state.request_pending):  
        session_handler.debug_log(f"用户输入了: {user_input[:20]}...")
        
        # 确认请求锁(重点)
        st.session_state.request_confirmed = True

        # 1. 构造基础消息
        new_msg = {"role": "user", "content": []}
        
        # 2. 如果有图，模式切换为 List
        if uploaded_file:
            session_handler.debug_log(f"检测到图片上传，正在转码...")
            # 从 Streamlit 上传对象中获取字节和 MIME 类型
            bytes_data = uploaded_file.getvalue()
            mime_type = uploaded_file.type
            base64_img = session_handler.base64_encode_image(bytes_data, mime_type)

            # 追加图片 base64 进 new_msg
            new_msg["content"].append({
                "type": "image_url",
                "image_url": {"url": base64_img}
            })
            # 追加文本
            new_msg["content"].append({
                "type": "text", 
                "text": user_input
            })
        else:  # 如果没图，保持纯文本字符串 (兼容旧模式)
            new_msg["content"] = user_input   # 回退到纯字符串模式，最安全
        
        session_handler.debug_log(f"消息已构造完毕，准备存入内存 Session...")
        # 消息追加到内存 messages 关键字，并显示
        st.session_state.messages.append(new_msg)
        session_handler.debug_log(f"存入完成")

        st.rerun()




















def chat_render():
    session_handler.debug_log(f"当前内存中有 {len(st.session_state.messages)} 条消息")

    # 渲染历史消息
    session_handler.debug_log("渲染历史消息")
    render_history_timeline()
    session_handler.debug_log("渲染完成")

    # 渲染输入框，并准备接收用户输入，完了更新内存 message
    session_handler.debug_log("进入user_input_area()逻辑")
    user_input_area() 
    session_handler.debug_log("退出user_input_area()逻辑")

    # 通过读取刚刚更新的内存内容，发送请求
    session_handler.debug_log("进入frontend_chat_request函数")
    chat_handler.frontend_chat_request()
    session_handler.debug_log("退出frontend_chat_request函数")
