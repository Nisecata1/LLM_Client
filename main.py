import time
import os
import json
from openai import OpenAI
import streamlit as st  # Web 版需要用到 Streamlit，下面st开头的都是这个库里的方法，搞清楚在干什么就行

# 自己的库
import src.constants as c  # 导入全局常量模块
import src.file_store_load_functions as f # 导入文件操作函数模块
import src.ui_components as ui  # 导入UI组件模块
import src.function_tools_call as tools  # 导入函数工具调用模块


# ====================================================================================================
# 使用 st.session_state 作为“数据总线”，在不同函数和组件间传递数据
# 在 Streamlit 中，跨文件/跨模块传递变量的最佳实践不是 return，而是直接读写 st.session_state。
# 因为你的 UI 组件里已经绑定了 key="ui_prompt"，其实 Streamlit 已经自动把它存到 session_state 里了。
# ====================================================================================================



# ===================== Streamlit 界面交互主逻辑 ======================
# 页面基本配置
st.set_page_config(page_title="AI 助手 (Web版)", page_icon="🐱", layout="wide") # wide模式视野更好
st.title("🐱 AI Chat Assistant")

ui.render_sidebar()  # 渲染侧边栏组件，这个函数定义在 ui_components.py 里，负责侧边栏的所有交互逻辑


# ================= 初始化/加载 记忆(Session State) =====================

if "client" not in st.session_state:  # 初始化 Client（如果不在内存）
    st.session_state.client = OpenAI(api_key=c.API_KEY, base_url=c.BASE_URL)

# ================= 渲染历史消息 (带编辑/删除功能) =================
# 使用 enumerate 获取索引 i，这是精确定位消息的关键
for i, msg in enumerate(st.session_state.messages):  # 这个 messages 已经在加载ui模块逻辑里初始化过了
    with st.chat_message(msg["role"]):
        # 1. 显示消息内容
        st.markdown(msg["content"])
        # 2. 添加管理工具 (仅在鼠标悬停或点击时展开，保持界面整洁)
        with st.popover("🔧", help="管理这条消息"):  # popover (气泡菜单) 
            # --- 功能 A: 编辑模式 ---
            # 这里的 key 必须唯一！使用 f"edit_text_{i}" 绑定到当前这条消息
            new_content = st.text_area( 
                "编辑内容", 
                value=msg["content"], 
                height=150, 
                key=f"edit_text_{i}"
            )
            
            col_edit, col_del, col_cancel = st.columns([1, 1, 1])

            # 保存按钮
            if col_edit.button("💾 保存", key=f"save_btn_{i}"):
                # 1. 更新内存
                st.session_state.messages[i]["content"] = new_content
                # 2. 写入硬盘 (调用你的 functions 库)
                f.save_history(
                    st.session_state.current_meta, 
                    st.session_state.messages, 
                    st.session_state.current_file_path
                )
                # 3. 强制刷新页面以显示更新后的内容
                st.rerun()

            # 删除按钮
            if col_del.button("🗑️ 删除", key=f"del_btn_{i}", type="primary"):
                # 标注：利用 Streamlit 的状态变量做一个简单的“确认拦截”
                # 或者直接使用快捷的逻辑：
                st.warning("确定要删除吗？")
                if st.button("我确定！", key=f"confirm_del_{i}"): # 标注：二次确认按钮
                    del st.session_state.messages[i]  # 1. 从内存移除
                    f.save_history(  # 2. 写入硬盘
                        st.session_state.current_meta, 
                        st.session_state.messages, 
                        st.session_state.current_file_path
                    )
                    st.rerun()  # 3. 强制刷新

            if col_cancel.button("✖️ 取消", key=f"cancel_btn_{i}"):
                # 解释：不需要写任何数据修改逻辑，直接 Rerun。
                # 由于之前的修改只存在于 text_area 的临时状态里，
                # 重新渲染时，它会再次从内存读取原始的 msg["content"]。
                st.rerun()

        




# ====== 处理用户输入 (对应Cli版的 while True 和 input)========
# st.chat_input 类似于 input()，但它构建了整个 Web 的交互循环
if user_input := st.chat_input("Shift+Enter 换行...输入你的问题..."):
    
    # --- A. 显示用户输入 ---
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})  # 加入内存

    # --- B. 构造请求 (滑动窗口逻辑) ---system_prompt在ui模块中更新
    sys_msg = {"role": "system", "content": st.session_state.ui_prompt}  # 从 session_state 读取 ui_components 模块里定义的 key="ui_prompt"
    recent_history = st.session_state.messages[-40:]  # 截取最近 40 条
    request_messages = [sys_msg] + recent_history  # 动态拼接: [系统提示词] + [最近历史]
    

    # --- C. 智能循环 (ReAct Loop) ---

    # --- C. 调用API 请求并流式输出 --- 
    with st.chat_message("assistant"):
        try:
            # 1. 获取 UI 参数 (如果没初始化给个空字典)
            params = st.session_state.get("gemini_params", {})
            
            # 2. 基础 OpenAI 参数
            openai_kwargs = {
                "model": st.session_state.ui_model, # 确保选的是 gemini-3-pro-preview
                "messages": request_messages,
                "stream": True,
                # 文档强烈建议：Gemini 3 温度设为 1.0
                "temperature": params.get("temperature", 1.0), 
                # 文档提到：OAI reasoning_effort 映射到 thinking_level
                # 但为了兼容性最好，我们直接用 extra_body 传 thinking_level
                "reasoning_effort": "medium",
                "max_tokens": params.get("max_tokens", 65535),
            }

            # 4. 注入参数
            if params:
                openai_kwargs["extra_body"] = params

            # # 标注：在真正发送请求前，把我们要发的东西打印出来
            # # 这样你就能在你的运行终端看到具体的 JSON 结构了喵！
            # print("--- [DEBUG] 准备发送的 API 参数 ---")
            # for k, v in openai_kwargs.items():
            #     if k != "messages": # messages 太长了，我们单独看参数
            #         print(f"| {k}: {v}")
            # print("---------------------------------")

            # 4. 调用 OpenAI API 发起请求 (用已经初始化好的client)
            stream = st.session_state.client.chat.completions.create(**openai_kwargs)
            # 5. 实时显示流式回复
            full_reply = st.write_stream(stream)  # write_stream方法自动代替了Cli代码中复杂的 for chunk in response 循环。它会自动处理 delta.content，实现打字机效果，并返回完整字符串
            


            # --- D. 保存回复 (包含 meta 数据) ---
            st.session_state.messages.append({"role": "assistant", "content": full_reply})
            # 这里的 save 传入了当前的 meta，实现了"配置跟随存档"
            f.save_history(
                st.session_state.current_meta, 
                st.session_state.messages, 
                st.session_state.current_file_path  # 使用我们在第一步里挂载到 session_state 的路径
            )
            
        except Exception as e:
            st.error(f"API 请求错误: {e}")
