import time
import os
import json
from openai import OpenAI
import streamlit as st      # Web 版需要用到 Streamlit库的方法, 搞清楚在干什么就行

# 自己的库
import src.constants as const               # 导入全局常量模块
import src.app_base_functions as storagef   # 导入文件操作函数模块
import src.ui_components as ui              # 导入UI组件模块
import src.tools_call_functions as tools    # 导入函数工具调用模块


# ===================================架构逻辑===============================================
# 使用 st.session_state 作为“数据总线”，在不同函数和组件间传递数据，他在内存里，存活于整个 Streamlit 会话期间。
# 在 Streamlit 中，跨文件/跨模块传递变量的最佳实践不是 return，而是直接读写 st.session_state。

# UI 模块 (ui_components) 负责采集参数（用户选了什么）。
# Session State 负责传输参数（数据总线）。
# Main 模块 负责消费参数（发送 API 请求）。
# 这种 MVC (Model-View-Controller) 的分离非常清晰。
# =========================================================================================



# ================ Streamlit 界面交互主逻辑 ================
# 页面基本配置
st.set_page_config(page_title="AI 助手 (Web版)", page_icon="🐱", layout="wide") # wide模式视野更好
st.title("🐱 AI Chat Assistant")

ui.render_sidebar()  # 渲染侧边栏组件，这个函数定义在 ui_components.py 里，负责侧边栏的所有交互逻辑

# 初始化 Client（如果不在内存）
if "client" not in st.session_state:  
    st.session_state.client = OpenAI(api_key=const.API_KEY, base_url=const.BASE_URL)

# ================= 渲染历史消息 =================
# 使用 enumerate 获取索引 i，这是精确定位消息的关键
# enumerate返回一个元组{当前下标，消息列表}，messages 已经在 ui 模块里初始化过了
# 每条消息还会伴随渲染一些功能按钮
for i, msg in enumerate(st.session_state.messages):  
    # with 创建该消息的一个上下文环境，里面的组件渲染在 <aside> 侧边栏里
    with st.chat_message(msg["role"]):  # 通过 msg["role"] 访问msg，而不是写 messages[i]["role"]
        # 1. 显示消息内容
        st.markdown(msg["content"])

        # 2. 添加一个管理工具上下文环境
        with st.popover("🔧", help="管理这条消息"):  # popover (气泡菜单) , 仅在鼠标悬停或点击时展开，保持界面整洁
            
            # --- 编辑 ---
            new_content = st.text_area( "编辑内容", value=msg["content"], height=150, key=f"edit_text_{i}")
            
            col_edit, col_del, col_cancel = st.columns([1, 1, 1])  # 分割三列，准备放按钮
            # 保存按钮
            if col_edit.button("💾 保存", key=f"save_btn_{i}"):
                st.session_state.messages[i]["content"] = new_content  # 更新内存消息中的某一条
                # 写入硬盘，注意该函数是覆盖写，所以要一起写
                storagef.save_history(st.session_state.meta, st.session_state.messages, st.session_state.file_path)
                st.rerun()

            # --- 删除按钮 (Callback) ---
            # 这里的 key 使用 f-string 动态生成，保证唯一性
            col_del.button( 
                "🗑️ 删除", 
                key=f"del_btn_{i}",  # 该句保证了在循环中，每个按钮在 内存（即会话Session State） 中都有一个独立的指针key指向，方便后续操作
                type="primary",   # 按钮颜色
                # 当用户点击，Streamlit 暂停脚本，先去执行回调函数。
                # 关于参数：st.button给回调函数传参实际上是把传入的元组解引用并传入，当它调用回调函数时，它会执行类似 callback(*args) 的操作，所以args必须是元组形式(即使回调函数只有一个形参),元组也是一个可迭代对象
                on_click=storagef.delete_msg_callback, args=(i,)  # 绑定回调函数
            )

            # --- 取消按钮 ---
            if col_cancel.button("✖️ 取消", key=f"cancel_btn_{i}"):
                st.rerun()  # 这里的 rerun 会让 popover 收起，且重置 text_area 的内容
        


# ===================== 用户输入 =======================
# st.chat_input 类似于 input()，但它同时构建了整个 Web 的交互循环
if user_input := st.chat_input("Shift+Enter 换行...输入你的问题..."):  
    
    # --- 渲染用户输入进对话框 ---
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})  # 同时append进内存

    # --- 构造 messages (滑动窗口) ---
    # 系统提示词和历史消息都从 st.session_state 读取，这两个都在ui模块绑定
    sys_msg = {"role": "system", "content": st.session_state.ui_prompt}  # 取系统提示词
    ctx_len = int(st.session_state.get("ui_history_len", 10))*2  # 乘以2是因为一轮对话包含用户和AI两条消息 
    recent_history = st.session_state.messages[-ctx_len:] 
    request_messages = [sys_msg] + recent_history  # 拼接: [系统提示词] + [最近历史]


    
    # 打开一个助手消息的框框
    with st.chat_message("assistant"):


        # --- 准备参数 --- 
        try:
            # 1. 获取ui模块获取的参数 (如果没初始化给个空字典)
            params = st.session_state.get("gemini_params", {})
            
            # 2. 准备基础 OpenAI 参数
            kwargs = {
                "model": st.session_state.ui_model, # 确保选的是 gemini-3-pro-preview
                "messages": request_messages,
                # "stream": True,  # 我们在调用 .create() 时手动指定
                "temperature": 1.0, 
                "top_p": 0.95,
                "max_tokens": 65535,
                "tools": tools.get_tools_schema(), # 注入本地 Python 工具描述表
                "tool_choice": "auto"
            }

            # 3. 构造 extra_body (字典结构，存Gemini 特有配置，直接透传给 Google REST API)
            # 【注意】因为是透传，Key 必须符合 Google REST JSON 规范 (驼峰命名)
            extra_body = {
                "generationConfig": {},
                # "tools": [] # 如果后续有联网功能，初始化这个列表
            }

            # 处理 Thinking Level，使用驼峰命名 thinkingConfig
            if "thinking_level" in params:
                # 在 extra_body 中的 generationConfig 下添加 thinkingConfig 字段
                extra_body["generationConfig"]["thinkingConfig"] = {
                    "includeThoughts": True,                    # (可选) 某些 Proxy/Client 需要这个来强制返回思考过程
                    "thinking_level": params["thinking_level"]  # 值通常是小写: low/medium/high
                }

            # (预留) 处理 Google Search
            if params.get("use_search"):
                 # Google Search 作为 Gemini 原生工具通过 extra_body 传入
                 extra_body["tools"] = [{
                     "googleSearchRetrieval": {
                         "dynamicRetrievalConfig": {
                             "mode": "dynamic",
                             "dynamicThreshold": 0.3
                         }
                     }
                 }]

            # 4. 往 kwargs 注入 extra_body (只有当里面有内容时才注入)
            if extra_body["generationConfig"] or extra_body.get("tools"):
                kwargs["extra_body"] = extra_body  # 最终参数 kwargs 构建完毕
            
            # --- 🔍 调试：打印最终发给 OpenAI SDK 的参数 ---
            # print(f"DEBUG kwargs: {json.dumps(kwargs, indent=2, ensure_ascii=False)}")

            # =========================================================
            # 🎭 核心逻辑：乐观流式 + 占位符回溯
            # =========================================================
            
            # [关键点1] 创建一个巨大的占位符，占据整个回复区域
            # 我们先在这个区域里疯狂输出流式内容
            # 如果后来发现需要调用工具，我们就把这个区域清空 (empty)，换成一个折叠框
            # 创建占位符
            main_placeholder = st.empty()        
        
            # 缓冲区
            full_reasoning = ""
            full_content = ""
            tool_calls_buffer = {}  # 用于后台拼接碎片化的工具参数
            final_response_content = "" # 最终要保存的内容

            # 1. 第一轮流式请求 (立刻开始，不等待)
            with st.status("AI 正在思考中..."):
                stream = st.session_state.client.chat.completions.create(stream=True, **kwargs)

            # 在占位符里开辟一个临时的容器，用于实时渲染
            with main_placeholder.container():
                # 思维链区域
                reasoning_area = st.empty()
                # 正文区域
                content_area = st.empty()
                
                for chunk in stream:
                    if not chunk.choices: continue
                    delta = chunk.choices[0].delta

                    # --- A. 收集并显示思维链 ---
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        full_reasoning += delta.reasoning_content
                        # 实时显示思维链 (带样式)
                        reasoning_area.markdown(f"*> 🧠 {full_reasoning}*")

                    # --- B. 收集并显示正文 (乐观渲染) ---
                    if delta.content:
                        full_content += delta.content
                        content_area.markdown(full_content + "▌") # 打字机光标

                    # --- C. 默默收集工具参数 (后台进行，不干扰屏幕) ---
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {"id": "", "name": "", "args": ""}
                            if tc.id: tool_calls_buffer[idx]["id"] += tc.id
                            if tc.function.name: tool_calls_buffer[idx]["name"] += tc.function.name
                            if tc.function.arguments: tool_calls_buffer[idx]["args"] += tc.function.arguments

                # 循环结束，移除光标
                content_area.markdown(full_content)


            # =========================================================
            # ⚖️ 判决时刻：刚才收集到工具调用了吗？
            # =========================================================
            
            final_response_content = full_content # 默认最终结果就是刚才输出的文本

            if tool_calls_buffer:
                # -----------------------------------------------------
                # 🛠️ 触发了工具调用！执行“回溯”逻辑
                # -----------------------------------------------------
                
                # [关键点2] 清空刚才那个占据屏幕的大占位符
                main_placeholder.empty() 

                # 重新在折叠框里渲染刚才的内容 (收纳起来)
                with st.status("Thinking & Analysis...", expanded=False, state="complete") as s:
                    if full_reasoning:
                        st.markdown(f"*> {full_reasoning}*")
                    if full_content:
                        st.markdown(full_content)
                    st.write("🔧 正在调用工具...")

                # --- 构造工具调用数据结构 ---
                simulated_tool_calls = []
                for idx in sorted(tool_calls_buffer.keys()):
                    t = tool_calls_buffer[idx]
                    simulated_tool_calls.append({
                        "id": t["id"],
                        "type": "function",
                        "function": {"name": t["name"], "arguments": t["args"]}
                    })

                # 保存第一轮交互到历史
                ai_msg = {
                    "role": "assistant", 
                    "content": full_content if full_content else None,
                    "tool_calls": simulated_tool_calls
                }
                st.session_state.messages.append(ai_msg)
                request_messages.append(ai_msg)

                # --- 执行工具 ---
                for tool_data in simulated_tool_calls:
                    func_name = tool_data["function"]["name"]
                    try:
                        args = json.loads(tool_data["function"]["arguments"])
                    except:
                        args = {} # 解析失败容错
                    
                    # 查找并运行函数
                    if func_name in tools.AVAILABLE_FUNCTIONS:
                        tool_result = tools.AVAILABLE_FUNCTIONS[func_name](**args)
                    else:
                        tool_result = f"Error: Function {func_name} not found"

                    # UI 显示工具结果小折叠框
                    with st.status(f"🛠️ Tool Output: {func_name}", expanded=False, state="complete"):
                        st.code(tool_result)

                    # 保存工具结果到历史
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tool_data["id"],
                        "content": str(tool_result)
                    }
                    st.session_state.messages.append(tool_msg)
                    request_messages.append(tool_msg)

                # --- 发起第二轮最终请求 ---
                # 这次直接流式输出到屏幕最下方
                stream2 = st.session_state.client.chat.completions.create(stream=True, **kwargs)
                final_response_content = st.write_stream(stream2)
            

            # =========================================================
            # 🌲 没有触发工具？那就保持原样
            # =========================================================
            else:
                # 这里的逻辑很简单：因为刚才已经在 main_placeholder 里渲染好了
                # 而且我们没有执行 empty()，所以文字就留在了屏幕上，完美！
                pass 


            
            # =========================================================
            # ✨ 统一出口：在这里只执行一次 append 和 save
            # =========================================================
            if final_response_content: # 防止空内容
                st.session_state.messages.append({"role": "assistant", "content": final_response_content})  # 在内存追加回复的消息
                storagef.save_history(st.session_state.meta, st.session_state.messages, st.session_state.file_path)  # 全部写回硬盘

            

        except Exception as e:
            st.error(f"API 请求错误: {e}")
