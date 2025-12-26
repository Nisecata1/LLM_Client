import time
import os
import json
from openai import OpenAI
import streamlit as st  # Web 版需要用到 Streamlit，下面st开头的都是这个库里的方法，搞清楚在干什么就行

# 自己的库
import src.constants as const  # 导入全局常量模块
import src.storage_functions as storagef # 导入文件操作函数模块
import src.ui_components as ui  # 导入UI组件模块
import src.tools_call_functions as tools  # 导入函数工具调用模块


# ===================================架构逻辑===============================================
# 使用 st.session_state 作为“数据总线”，在不同函数和组件间传递数据
# 在 Streamlit 中，跨文件/跨模块传递变量的最佳实践不是 return，而是直接读写 st.session_state。

# UI 模块 (ui_components) 负责采集参数（用户选了什么）。
# Session State 负责传输参数（数据总线）。
# Main 模块 负责消费参数（发送 API 请求）。
# 这种 MVC (Model-View-Controller) 的分离非常清晰。
# =========================================================================================



# ===================== Streamlit 界面交互主逻辑 ======================
# 页面基本配置
st.set_page_config(page_title="AI 助手 (Web版)", page_icon="🐱", layout="wide") # wide模式视野更好
st.title("🐱 AI Chat Assistant")

ui.render_sidebar()  # 渲染侧边栏组件，这个函数定义在 ui_components.py 里，负责侧边栏的所有交互逻辑


# ================= 初始化/加载 记忆(Session State) =====================

if "client" not in st.session_state:  # 初始化 Client（如果不在内存）
    st.session_state.client = OpenAI(api_key=const.API_KEY, base_url=const.BASE_URL)


# ================= 渲染历史消息 (带编辑/删除功能) =================
# 使用 enumerate 获取索引 i，这是精确定位消息的关键
for i, msg in enumerate(st.session_state.messages):  # enumerate返回一个元组{当前下标，消息列表}，messages 已经在 ui 模块里初始化过了
    with st.chat_message(msg["role"]):  # 直接通过 msg["role"] 访问，不需要再写 messages[i]["role"]
        # 1. 显示消息内容
        st.markdown(msg["content"])

        # 2. 添加管理工具
        with st.popover("🔧", help="管理这条消息"):  # popover (气泡菜单) , 仅在鼠标悬停或点击时展开，保持界面整洁
            
            # --- 功能 A: 编辑模式 ---
            # 这里的 key 使用 f-string 动态生成，保证唯一性
            new_content = st.text_area( "编辑内容", value=msg["content"], height=150, key=f"edit_text_{i}")
            
            col_edit, col_del, col_cancel = st.columns([1, 1, 1])  # 分割三列，准备放按钮
            # 保存按钮
            if col_edit.button("💾 保存", key=f"save_btn_{i}"):  # 该方法返回ture or false
                # 1. 更新内存
                st.session_state.messages[i]["content"] = new_content
                # 2. 写入硬盘 (调用你的 functions 库)，注意该函数是覆盖写，所以需要meta和messages一起写
                storagef.save_history(st.session_state.meta, st.session_state.messages, st.session_state.file_path)
                st.rerun()

            # --- 删除按钮 (修改为 Callback 模式) ---
            col_del.button(
                "🗑️ 删除", 
                # 作用：动态生成唯一 ID。
                # 解释：{i} 保证了在循环中，每个按钮在 Session State 中都有独立的槽位。
                key=f"del_btn_{i}", 
                type="primary",   # 按钮颜色
                # 给按钮绑定回调函数，当用户点击，Streamlit 暂停脚本，先去执行回调函数。
                # 关于参数：st.button给回调函数传参实际上是把传入的元组解引用并传入，当它调用回调函数时，它会执行类似 callback(*args) 的操作，所以args必须是元组形式(即使回调函数只有一个形参),元组也是一个可迭代对象
                on_click=storagef.delete_msg_callback, args=(i,)  
            )

            # --- 取消按钮 ---
            if col_cancel.button("✖️ 取消", key=f"cancel_btn_{i}"):
                st.rerun()  # 这里的 rerun 会让 popover 收起，且重置 text_area 的内容
        

# ====== 处理用户输入 (对应Cli版的 while True 和 input)========
# st.chat_input 类似于 input()，但它构建了整个 Web 的交互循环
if user_input := st.chat_input("Shift+Enter 换行...输入你的问题..."):
    
    # --- A. 显示用户输入 ---
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})  # 加入内存

    # --- B. 构造请求 (滑动窗口逻辑) ---system_prompt在ui模块中更新
    sys_msg = {"role": "system", "content": st.session_state.ui_prompt}  # 从 session_state 读取 ui_components 模块里定义的 key="ui_prompt"
    recent_history = st.session_state.messages[-50:]  # 截取最近 60 条
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
                "temperature": 1.0, 
                "max_tokens": 65535,
                "top_p": 0.95,
            }

            # 3. 构造 Gemini 专属参数 (直接透传给 Google REST API)
            # 【注意】因为是透传，Key 必须符合 Google REST JSON 规范 (驼峰命名)
            extra_body = {
                "generationConfig": {},
                # "tools": [] # 如果后续有联网功能，初始化这个列表
            }
            # 处理 Thinking Level
            if "thinking_level" in params:
                # 【修正2】使用驼峰命名 thinkingConfig
                extra_body["generationConfig"]["thinkingConfig"] = {
                    "includeThoughts": True,                    # (可选) 某些 Proxy/Client 需要这个来强制返回思考过程
                    "thinking_level": params["thinking_level"]  # 值通常是小写: low/medium/high
                }

            # (预留) 处理 Google Search
            if params.get("use_search"):
                 # Google 原生工具格式
                 extra_body["tools"] = [{
                     "googleSearchRetrieval": {
                         "dynamicRetrievalConfig": {
                             "mode": "dynamic",
                             "dynamicThreshold": 0.3
                         }
                     }
                 }]

            # 4. 注入 extra_body (只有当里面有内容时才注入，保持请求干净)
            if extra_body["generationConfig"] or extra_body.get("tools"):
                openai_kwargs["extra_body"] = extra_body

            # --- 🔍 调试：打印最终发给 OpenAI SDK 的参数 ---
            # print(f"DEBUG kwargs: {json.dumps(openai_kwargs, indent=2, ensure_ascii=False)}")
           
            # 调用 OpenAI API 发起请求 (用已经初始化好的client)
            stream = st.session_state.client.chat.completions.create(**openai_kwargs)
            st.spinner("正在加载...")
            full_reply = st.write_stream(stream)  # 实时显示流式回复
            # write_stream方法自动代替了Cli代码中复杂的 for chunk in response 循环。它会自动处理 delta.content，实现打字机效果，并返回完整字符串
            

            # --- D. 保存回复 (包含 meta 数据) ---
            st.session_state.messages.append({"role": "assistant", "content": full_reply})
            # 这里的 save 传入了当前的 meta，实现了"配置跟随存档"
            storagef.save_history(
                st.session_state.meta, 
                st.session_state.messages, 
                st.session_state.file_path  # 使用我们在第一步里挂载到 session_state 的路径
            )
            
        except Exception as e:
            st.error(f"API 请求错误: {e}")
