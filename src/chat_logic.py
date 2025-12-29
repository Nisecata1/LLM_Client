import json
from openai import OpenAI

import streamlit as st
import src.tools_call_functions as tools
import src.constants as const               # 导入全局常量模块
import src.storage_module as storage   # 导入文件操作函数模块

# 负责聊天相关的逻辑:渲染消息、构建参数、发送请求等等


def render_history_timeline():
    """
    渲染整个聊天历史记录的时间轴，包括：
    1. 区分纯文本和多模态渲染
    2. 每条消息的管理菜单 (编辑/删除/保存)
    """

    # for循环配合 enumerate 获取每次遍历元素的索引 i，这是精确定位消息的关键
    # enumerate返回一个元组{当前下标，消息列表}，messages 已经在 ui 模块里初始化过了

    for i, msg in enumerate(st.session_state.messages):  
        # with 创建该消息的一个上下文环境，里面的组件渲染在 <aside> 侧边栏里
        with st.chat_message(msg["role"]):  # 通过 msg["role"] 访问msg，而不是写 messages[i]["role"]
            
            # 1. 取出消息内容
            content = msg["content"]

            # Case A: 多模态消息 (包含图片和文字的List 类型)
            if isinstance(content, list):
                for item in content:
                    # 渲染图片
                    if item.get("type") == "image_url":
                        img_url = item["image_url"]["url"]
                        # 渲染 Base64 图片
                        st.image(img_url, width=300) # 可以限制图片显示宽度
                    # 渲染文本
                    elif item.get("type") == "text":
                        st.markdown(item["text"])
            # Case B: 纯文本消息 (String 类型)
            else:
                st.markdown(content)


            # (可选) 如果是 AI 回复，检查是否有 tool_calls 并显示折叠块
            if msg.get("tool_calls"):
                with st.status("🔧 工具调用记录", state="complete"):
                    st.json(msg["tool_calls"])


            # 2. 添加一个管理工具上下文环境
            with st.popover("🔧", help="管理这条消息"):  # popover (气泡菜单) , 仅在鼠标悬停或点击时展开，保持界面整洁
                
                # --- 编辑 ---
                new_content = st.text_area( "编辑内容", value=msg["content"], height=150, key=f"edit_text_{i}")
                
                col_edit, col_del, col_cancel = st.columns([1, 1, 1])  # 分割三列，准备放按钮
                # 保存按钮
                if col_edit.button("💾 保存", key=f"save_btn_{i}"):
                    st.session_state.messages[i]["content"] = new_content  # 更新内存消息中的某一条
                    # 写入硬盘，注意该函数是覆盖写，所以要一起写
                    storage.save_history(st.session_state.meta, st.session_state.messages, st.session_state.file_path)
                    st.rerun()

                # --- 删除按钮 (Callback) ---
                # 这里的 key 使用 f-string 动态生成，保证唯一性
                col_del.button( 
                    "🗑️ 删除", 
                    key=f"del_btn_{i}",  # 该句保证了在循环中，每个按钮在 内存（即会话Session State） 中都有一个独立的指针key指向，方便后续操作
                    type="primary",   # 按钮颜色
                    # 当用户点击，Streamlit 暂停脚本，先去执行回调函数。
                    # 关于参数：st.button给回调函数传参实际上是把传入的元组解引用并传入，当它调用回调函数时，它会执行类似 callback(*args) 的操作，所以args必须是元组形式(即使回调函数只有一个形参),元组也是一个可迭代对象
                    on_click=storage.delete_msg_callback, args=(i,)  # 绑定回调函数
                )

                # # --- 取消按钮 ---
                # if col_cancel.button("✖️ 取消", key=f"cancel_btn_{i}"):
                #     st.rerun()  # 这里的 rerun 会让 popover 收起，且重置 text_area 的内容
        
  


def initial_client(): 
    '''
    在内存中初始化client
    '''
    if "client" not in st.session_state:  # 初始化 Client（如果不在内存）
        st.session_state.client = OpenAI(api_key=const.API_KEY, base_url=const.BASE_URL)
    storage.debug_log("初始化client完成")


def build_request_messages():
    """
    通过滑动窗口机制构建发给 AI 的完整消息上下文messages
    return: 拼装好的 messages 列表
    """
    # 系统提示词和历史消息都从 st.session_state 读取，这两个都在ui模块绑定
    sys_msg = {"role": "system", "content": st.session_state.ui_prompt}  # 取系统提示词
    ctx_len = int(st.session_state.get("ui_history_len", 10))*2  # 乘以2是因为一轮对话包含用户和AI两条消息 
    recent_history = st.session_state.messages[-ctx_len:] 
    request_messages = [sys_msg] + recent_history  # 拼接: [系统提示词] + [最近历史]
    return request_messages


def build_api_params(request_messages):
    """
    request_messages: 要发送的历史消息上下文
    该函数负责构建 OpenAI SDK 需要的所有参数(基础参数、工具定义、模型特有参数等等)，并包含request_messages
    """
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
        "tool_choice": "auto"
    }
    # 注入本地 Python 工具描述表(如果有的话)
    tool_schema = tools.get_tools_schema()
    if tool_schema:  # 只有当真的有工具时，才传 tools 参数
        kwargs["tools"] = tool_schema
        kwargs["tool_choice"] = "auto"

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

    return kwargs


def stream_first_response(client, api_kwargs, main_placeholder):
    """
    第一阶段：第一轮渲染
    发流式请求，如果返回的chunk的toolcall=null就正常流式输出渲染，如果发现toocall有效就在后台收集工具调用信息。
    :param main_placeholder: 传入一个 st.empty() 容器，用于渲染
    :return: (full_content, full_reasoning, tool_calls_buffer)
    """
    full_reasoning = ""
    full_content = ""
    tool_calls_buffer = {}
    
    # 1. 发起请求
    with st.status("AI 正在思考中...", expanded=False) as s:
        print(">>> [Logic] 发起第一轮 API 请求")
        stream = client.chat.completions.create(stream=True, **api_kwargs)
        s.update(label="AI 正在生成...", state="running")

    # 2. 在占位符中渲染
    with main_placeholder.container():
        reasoning_area = st.empty()  # 思维链区域
        content_area = st.empty()  # 正文区域
        
        print(">>> [Logic] 开始循环chunk")
        for chunk in stream:
            if not chunk.choices: continue
            delta = chunk.choices[0].delta

            # A. 思维链
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                full_reasoning += delta.reasoning_content
                reasoning_area.markdown(f"*> 🧠 {full_reasoning}*")  # 在占位符中渲染思维链

            # B. 正文
            if delta.content:
                full_content += delta.content
                content_area.markdown(full_content + "▌")

            # C. 工具参数缓冲
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

    s.update(label="生成完成")
    
    print(">>> [Logic] 第一轮输出完成")

    return full_content, full_reasoning, tool_calls_buffer


def handle_tool_execution(tool_calls_buffer, messages_history):
    """
    第二阶段：如果有工具调用，执行它们，并把结果追加到 messages_history。
    注意：这里会直接修改传入的 messages_history 列表（引用传递）。
    :return: 模拟的 tool_calls 列表，用于 API 格式对齐
    """
    print(f">>> [Logic] 检测到 {len(tool_calls_buffer)} 个工具调用")
    
    # 1. 构造标准 Tool Call 结构
    simulated_tool_calls = []
    for idx in sorted(tool_calls_buffer.keys()):
        t = tool_calls_buffer[idx]
        simulated_tool_calls.append({
            "id": t["id"],
            "type": "function",
            "function": {"name": t["name"], "arguments": t["args"]}
        })

    # 2. 执行并展示 UI
    # 注意：这里我们使用一个 status 容器把工具执行过程折叠起来，保持界面整洁
    with st.status("正在调用工具 (Tool Execution)...", expanded=False, state="complete"):
        for tool_data in simulated_tool_calls:
            func_name = tool_data["function"]["name"]
            
            # 解析参数
            try:
                args = json.loads(tool_data["function"]["arguments"])
            except:
                args = {}
            
            # 运行函数
            if func_name in tools.AVAILABLE_FUNCTIONS:
                st.write(f"⚙️ 正在执行: `{func_name}`")
                tool_result = tools.AVAILABLE_FUNCTIONS[func_name](**args)
            else:
                tool_result = f"Error: Function {func_name} not found"

            # 显示结果
            st.code(tool_result, language="json")

            # 3. 将结果追加到历史记录
            messages_history.append({
                "role": "tool",
                "tool_call_id": tool_data["id"],
                "content": str(tool_result)
            })
    
    return simulated_tool_calls


def stream_final_response(client, api_kwargs):
    """
    第三阶段：工具执行完后，发起第二轮请求获取最终解释。
    直接使用 st.write_stream 简化代码。
    """
    print(">>> [Logic] 发起第二轮 API 请求 (总结工具结果)")
    stream = client.chat.completions.create(stream=True, **api_kwargs)
    return st.write_stream(stream)



def request_logic():
    '''
    准备参数，发送api请求，接收，处理并渲染
    '''

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        st.toast("✅ 正在请求 AI...", icon="🤖")

        # 打开一个助手消息的框框
        with st.chat_message("assistant"):

            # --- 准备参数 --- 
            try:
                # 1. 构建请求消息列表
                request_messages = build_request_messages()
                # 2. 构建完整请求参数(包含上下文和工具定义)
                kwargs = build_api_params(request_messages)

                # =========== 乐观流式 + 占位符回溯 =============
                # [关键点1] 创建一个巨大的占位符，占据整个回复区域, 我们先在这个区域里疯狂输出流式内容
                # 如果发现需要调用工具(tool_call字段非空)，我们就把这个区域清空 (empty)，换成一个折叠框
                # 创建占位符
                main_placeholder = st.empty()  # 这是一个空的容器，占据了屏幕最下方
                
                # 发起第一轮请求，获取流式响应
                full_content, full_reasoning, tool_calls_buffer = stream_first_response(st.session_state.client, kwargs, main_placeholder)
                final_response = full_content # 默认最终结果就是第一轮的文字

                # 调试测试返回值
                if full_content:
                    storage.debug_log(f"第一轮响应内容: {full_content[:30]}...")
                if full_reasoning:
                    storage.debug_log(f"第一轮思维链内容: {full_reasoning[:30]}...")

                # 3. 判断是否需要调用工具
                if tool_calls_buffer:
                    storage.debug_log(f"检测到工具调用请求...\n工具调用请求内容：{str(tool_calls_buffer)[:30]}...")
                    # A. 如果需要，先清空刚才的大占位符 (回溯 UI)
                    main_placeholder.empty()

                    # B. 补全第一轮的 Assistant 消息进历史
                    # (因为刚才只是流式显示，还没存进 memory)
                    # 我们需要重构一下 tool_calls 的格式存进去
                    # 这里为了简单，让 handle_tool_execution 去生成结构，我们这里先手动存一个
                    simulated_tool_calls = []
                    for idx in sorted(tool_calls_buffer.keys()):
                        t = tool_calls_buffer[idx]
                        simulated_tool_calls.append({
                            "id": t["id"], "type": "function", 
                            "function": {"name": t["name"], "arguments": t["args"]}
                        })
                    
                    ai_msg_pre = {
                        "role": "assistant",
                        "content": full_content if full_content else None,
                        "tool_calls": simulated_tool_calls
                    }
                    # 更新 Session 和 当前请求的 messages
                    st.session_state.messages.append(ai_msg_pre)
                    request_messages.append(ai_msg_pre)
                    
                    # C. 在界面上回显刚才的思考过程 (可选，为了体验丝滑)
                    if full_reasoning:
                        st.info(f"🧠 思考回溯: {full_reasoning}", icon="💭")
                    if full_content:
                        st.markdown(full_content)

                    # D. 执行工具逻辑 (核心解耦)
                    # 这个函数会帮我们运行函数，并把结果 append 到 request_messages 里
                    # 注意：传入 request_messages 是为了让第二轮请求知道上下文，
                    # 同时也传入 st.session_state.messages 确保存盘
                    # 这里为了简单，我们传入 st.session_state.messages，然后再同步给 request_messages
                    
                    handle_tool_execution(tool_calls_buffer, st.session_state.messages)
                    
                    # 同步一下 request_messages (把刚才工具产生的新消息加进去)
                    # 这是一个简单的技巧：找出 session 里新增的那几条
                    new_msg_count = len(st.session_state.messages) - (len(request_messages) - 1) # 减1是因为上面刚append了ai_msg
                    if new_msg_count > 0:
                        request_messages.extend(st.session_state.messages[-new_msg_count:])

                    # E. 发起第二轮请求
                    final_response = stream_final_response(st.session_state.client, kwargs)

            
                # =========================================================
                # ✨ 统一出口：在这里只执行一次 append 和 save
                # =========================================================
                if final_response : # 防止空内容
                    st.session_state.messages.append({"role": "assistant", "content": final_response })  # 在内存追加回复的消息
                    storage.save_history(st.session_state.meta, st.session_state.messages, st.session_state.file_path)  # 全部写回硬盘

            except Exception as e:
                st.error(f"API 请求错误: {e}")
