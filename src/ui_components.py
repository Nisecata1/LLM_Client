
import os
import time
import streamlit as st

# 自己的库
import src.constants as c
import src.file_store_load_functions as f


def render_sidebar():
# ======================== 侧边栏配置 =========================
    with st.sidebar:  # [侧边栏容器] with 语句创建了一个上下文环境，里面的组件渲染在 <aside> 侧边栏里
        st.header("⚙️设置面板")

        # ============= 路径管理 (无需改代码即可修改) ==============
        with st.expander("📁 存储路径设置"):  # 创建一个下拉菜单
            new_path = st.text_input("数据存储路径", value=c.HISTORY_DIR)  # 创建new_path对象接收用户输入，默认值为当前路径
            if st.button("更新路径"):  # 按钮事件：如果用户点击了该按钮
                f.save_app_config(new_path)  # 将用户输入的新路径保存到配置文件
                c.HISTORY_DIR = new_path  # 更新当前路径变量
                st.success("路径已更新，正在刷新...")
                time.sleep(1)
                st.rerun()  # 刷新页面

        # =================== 存档切换 ===================
        st.header("📂 存档与记忆")
        # 扫描并排序
        if os.path.exists(c.HISTORY_DIR):  # 扫描文件夹 c.HISTORY_DIR ，列出所有 json 文件，排序并用一个列表对象 all_files 存起来
            all_files = [f for f in os.listdir(c.HISTORY_DIR) if f.endswith('.json')]
            all_files.sort(key=lambda x: os.path.getmtime(os.path.join(c.HISTORY_DIR, x)), reverse=True)  # 排序：利用 os.path.getmtime（获取文件修改时间）配合 sort，把最近聊过天的档案排在最前面
        else:
            all_files = []
        selected_file = st.selectbox("选择历史存档", all_files, index=0 if all_files else None)  # st.selectbox创建下拉选择框，用一个 selected_file 对象接收用户选择（默认为 index=0 即最新的那个文件）

        # 构造当前选中的完整路径，用 current_file_path 对象接收
        if selected_file:
            current_file_path = os.path.join(c.HISTORY_DIR, selected_file)  # os.path.join方法用于拼接完整路径
        else: 
            current_file_path = os.path.join(c.HISTORY_DIR, "chat_history.json")  # 如果文件夹内还没json聊天文件，比如 all_files =[] ，就用默认的
        # 🌟将局部变量挂载到全局 session_state，让 main.py 能读取到
        st.session_state.current_file_path = current_file_path 
        # 存档加载逻辑，核心判定条件：  
        #   1. 文件切换： session_state 里存的文件名 和 当前选的不一样，说明用户刚切了存档
        #   2. 第一次初始化：session里还没初始化过meta ()
        # 这行 IF 语句是在做“防抖”和“状态判定”
        if (
            "current_file" not in st.session_state or          # 情况1：程序刚启动，还没存过文件名
            st.session_state.current_file != selected_file or  # 情况2：用户刚才点下拉框换了文件
            "current_meta" not in st.session_state             # 情况3：元数据意外丢失（防御性编程）
        ):  # 只有满足上面条件，才会去读 current_file_path （这是昂贵的 IO 操作）
            meta, msgs = f.load_history(current_file_path) # 解包赋值：把返回的两个值分别给两个变量
            # 更新 Session 状态 (真正的后端数据)
            st.session_state.messages = msgs
            st.session_state.current_meta = meta # 这里给 current_meta 赋值了！
            st.session_state.current_file = selected_file
            # 更新 Session 状态 (前端 UI 组件的状态)：强制同步前端 UI 组件的状态，直接修改 key 对应的 Session State，这会强制输入框显示新的值
            st.session_state.ui_prompt = meta.get("system_prompt", c.DEFAULT_SYSTEM_PROMPT)
            st.session_state.ui_temperature = float(meta.get("temperature", 1.0))
            # 更新模型显示，这个稍微麻烦点，要确保模型在列表里
            loaded_model = meta.get("model", c.MODEL_NAME_LIST[0])
            if loaded_model not in c.MODEL_NAME_LIST:
                loaded_model = c.MODEL_NAME_LIST[0]
            st.session_state.ui_model = loaded_model

            st.toast(f"已加载存档: {selected_file}")



        # ============ 系统提示词与模型 ============
        st.subheader("🧠 系统提示词与模型 (跟随存档)")

        system_prompt = st.text_area("系统提示词", height=150, key="ui_prompt")  # 这就是双向绑定，即时更新 session_state 里的 ui_prompt
        selected_model = st.selectbox("选择模型", c.MODEL_NAME_LIST, key="ui_model") # 每次你修改st.selectbox的内容，脚本重跑，selected_model 变量就会拿到session里最新的值
        
        
        
        # 🛠️ 其他设置
        with st.expander("💎 Gemini 3 高级特性", expanded=True):
            # A. 思考等级 (Thinking Level)
            thinking_option = st.select_slider(
                "🤔 思考强度 (Thinking Level)",
                options=["Low (快)", "Medium (平衡)", "High (深思)"],
                value="Medium (平衡)",
                help="High 模式会消耗更多 Token 进行深度推理"
            )
            # 映射表：UI显示 -> API参数值
            thinking_map = {
                "Low (快)": "low", 
                "Medium (平衡)": "medium", 
                "High (深思)": "high"
            }
            
            # B. Google Search 开关
            use_search = st.toggle("🌍 启用 Google 联网 (Search)", value=False)
            
            # C. 安全限制开关
            disable_safety = st.toggle("☠️ 解除安全审查 (Block None)", value=False)

        # 4. 参数打包 (存入 Session 供 main.py 读取)
        # 注意：一定要把这些新参数存进去，main.py 才能拿到！
        st.session_state.gemini_params = {
            "thinking_level": thinking_map[thinking_option],
            "use_search": use_search,
            "disable_safety": disable_safety
        }

        # 实时更新 session_state 中的 Meta (以便后续保存)
        # 当用户在网页上修改输入框时，上面的 key 变量会自动变，我们只需要把它存回 current_meta
        st.session_state.current_meta = {
            "system_prompt": system_prompt,  # 这里取到的就是 key="ui_prompt" 的最新值
            "model": selected_model,
            # 把高级参数也存进存档，这样下次加载存档时能恢复
            "gemini_config": st.session_state.gemini_params 
        }
        st.markdown("---")




        # ============ 归档功能的正确写法 (Callback) ============

        def archive_current_chat(curr_path):
            # 定义回调函数：这个函数会在点击按钮后、页面重绘前执行
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            archive_filename = f"chat_history_{timestamp}.json"
            archive_path = os.path.join(c.HISTORY_DIR, archive_filename)
            
            # A. 保存归档
            if len(st.session_state.messages) > 0:
                # 使用当前的 meta 和 messages 保存
                f.save_history(st.session_state.current_meta, st.session_state.messages, archive_path)
                # 重命名旧文件 (如果存在)
                if os.path.exists(curr_path):
                    os.rename(curr_path, archive_path)  # 如果不是原名，这里我们简单处理：重命名当前文件
                st.toast(f"✅ 已归档: {archive_filename}")
            
            # B. 重置内存数据
            st.session_state.messages = []  # 清空消息列表
            st.session_state.current_meta = c.DEFAULT_SETTINGS  # 恢复默认设置
            
            # C. 【关键】重置 UI 组件绑定的变量
            # 因为是在回调里修改，此时页面还没开始重绘，所以是合法的！
            st.session_state.ui_prompt = c.DEFAULT_SYSTEM_PROMPT
            st.session_state.ui_temperature = 1.0
            st.session_state.ui_model = c.MODEL_NAME_LIST[0]

            # D. 创建新文件
            new_default_path = os.path.join(c.HISTORY_DIR, "chat_history.json")
            f.save_history(c.DEFAULT_SETTINGS, [], new_default_path)
        
        # 渲染按钮，绑定回调
        # Callback 回调写法 = 先改票，再上车。
        # Streamlit 的机制规定，凡是触发了 callback，脚本执行完 callback 后会自动 Rerun 一遍脚本
        # args=(current_file_path,) 用于把当前的路径传给回调函数
        st.button("💾 归档并开启新对话", on_click=archive_current_chat, args=(current_file_path,))  # 执行回调函数内的修改逻辑时输入框还没画，内存里的数据被成功修改了

        # ============ 归档功能的错误写法 (禁止使用) ============
        # 在按钮的 if 块里修改 Session State，会违反 Streamlit 的执行模型，导致报错
        # if st.button("💾 归档并开启新对话"):  # 当你点击“归档”按钮时，Streamlit 立刻从第 1 行开始 重新运行整个脚本

        #     timestamp = time.strftime("%Y%m%d_%H%M%S")
        #     archive_filename = f"chat_history_{timestamp}.json"
        #     archive_path = os.path.join(c.HISTORY_DIR, archive_filename)
            
        #     # 保存旧文件 (带上当前的配置)
        #     if len(st.session_state.messages) > 0:
        #         save_history(st.session_state.current_meta, st.session_state.messages, archive_path)
        #         if os.path.exists(current_file_path):
        #              os.rename(current_file_path, archive_path)  # 如果不是原名，这里我们简单处理：重命名当前文件
        #         st.toast(f"✅ 已归档: {archive_filename}")
            
        #     # 重置内存
        #     st.session_state.messages = []
        #     st.session_state.current_meta = DEFAULT_SETTINGS # 恢复默认设置
        #     # 同时重置 UI 组件显示
        #     st.session_state.ui_prompt = DEFAULT_SYSTEM_PROMPT  # 由于脚本运行顺序，所以上面已经渲染出了这个输入框和里面的值，你试图修改一个在当前这一轮运行中，已经被画在屏幕上的组件所绑定的变量。这是“先斩后奏”，Streamlit 不允许。
        #     st.session_state.ui_temperature = 1.0
        #     st.session_state.ui_model = MODEL_NAME_LIST[0]

        #     # 写入一个新的默认文件
        #     new_default_path = os.path.join(c.HISTORY_DIR, "chat_history.json")
        #     save_history(DEFAULT_SETTINGS, [], new_default_path)
            
        #     st.rerun()

