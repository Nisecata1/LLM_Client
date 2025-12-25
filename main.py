import time
import os
import json
from openai import OpenAI
import streamlit as st  # Web 版需要用到 Streamlit，下面st开头的都是这个库里的方法，搞清楚在干什么就行

# 自己的库
import src.constants as c  # 导入全局常量模块
import src.storage_files_option_function as f # 导入文件操作函数模块
import src.ui_components as ui  # 导入UI组件模块


# 使用 st.session_state 作为“数据总线”，在不同函数和组件间传递数据
# 在 Streamlit 中，跨文件/跨模块传递变量的最佳实践不是 return，而是直接读写 st.session_state。
# 因为你的 UI 组件里已经绑定了 key="ui_prompt"，其实 Streamlit 已经自动把它存到 session_state 里了。

# ===================== Streamlit 界面交互主逻辑 ======================
# 页面基本配置
st.set_page_config(page_title="AI 助手 (Web版)", page_icon="🐱", layout="wide") # wide模式视野更好
st.title("🐱 AI Chat Assistant")

ui.render_sidebar()  # 渲染侧边栏组件，这个函数定义在 ui_components.py 里，负责侧边栏的所有交互逻辑


# ================= 初始化/加载 记忆(Session State) =====================
# 初始化 Client（如果不在内存）
if "client" not in st.session_state:
    st.session_state.client = OpenAI(api_key=c.API_KEY, base_url=c.BASE_URL)

# # 对应 Cli 版 main 函数里的 messages = load_history()
# if "messages" not in st.session_state:
#     st.session_state.messages = load_history()

# 渲染历史消息 (Web 版必须每次重绘所有历史，对应你原版 print 历史记录的部分
for msg in st.session_state.messages:  # 这个 messages 上面已经在加载逻辑里初始化过了
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===========================================================
# ====== 处理用户输入 (对应Cli版的 while True 和 input)========
# ===========================================================
# st.chat_input 类似于 input()，但它构建了整个 Web 的交互循环
if user_input := st.chat_input("Shift+Enter 换行...输入你的问题..."):
    
    # --- A. 显示用户输入 ---
    with st.chat_message("user"):
        st.markdown(user_input)
    # 加入内存
    st.session_state.messages.append({"role": "user", "content": user_input})

    # --- B. 构造请求 (滑动窗口逻辑) ---使用侧边栏配置的system_prompt 
    sys_msg = {"role": "system", "content": st.session_state.ui_prompt}  # 从 session_state 读取 ui_components 模块里定义的 key="ui_prompt"
    recent_history = st.session_state.messages[-30:]  # 截取最近 30 条
    request_messages = [sys_msg] + recent_history  # 动态拼接: [系统提示词] + [最近历史]
    
    # --- C. 调用API 请求并流式输出 --- 
    with st.chat_message("assistant"):
        try:
            stream = st.session_state.client.chat.completions.create(
                model=st.session_state.ui_model,  # 直接读 key="ui_model"，ui模块中在侧边栏选的
                messages=request_messages,
                stream=True,
                temperature=st.session_state.ui_temperature,  # 直接读 key="ui_temperature" 使ui模块中在侧边栏选的
            )
            # Streamlit 专属神器 write_stream, 它自动代替了你原代码中复杂的 for chunk in response 循环
            full_reply = st.write_stream(stream)  # 它会自动处理 delta.content，实现打字机效果，并返回完整字符串
            
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
