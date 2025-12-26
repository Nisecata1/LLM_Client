
import os
import time
import streamlit as st

# 自己的库
import src.constants as const
import src.storage_functions as storagef


# ======================== 侧边栏配置 =========================
def render_sidebar():
    with st.sidebar:  # [侧边栏容器] with 语句创建了一个上下文环境，里面的组件渲染在 <aside> 侧边栏里
        st.header("⚙️设置面板")

        # ============= 路径管理 (无需改代码即可修改) ==============
        with st.expander("📁 存储路径设置", expanded=False):  # 创建一个下拉菜单
            current_dir = storagef.get_history_dir() # 获取当前存储路径，该函数会确保路径有效
            # 创建new_path对象接收用户输入，默认值为当前路径
            new_path = st.text_input("数据存储路径", value=current_dir)

            if st.button("更新路径"):  # 当用户点击“更新路径”按钮时
                storagef.save_app_config(new_path)  # 将用户输入的新路径保存到配置文件
                st.success("路径已更新，正在刷新...")
                time.sleep(1)
                st.rerun() 

        # =================== 存档切换 ===================
        st.header("📂 存档与记忆")

        # 扫描文件夹，列出所有json文件并排序，用一个列表对象 all_files 存起来
        all_files = [x for x in os.listdir(current_dir) if x.endswith('.json')]
        all_files.sort(key=lambda x: os.path.getmtime(os.path.join(current_dir, x)), reverse=True)
        # st.selectbox创建下拉选择框，用一个 selected_file 对象接收用户选择（默认为 index=0 即最新的那个文件）
        selected_file = st.selectbox("选择存档", all_files, index=0 if all_files else None)

        # 构造完整路径，用 current_file_path 对象接收
        if selected_file:
            current_file_path = os.path.join(current_dir, selected_file)  # os.path.join方法用于拼接完整路径
        else: 
            current_file_path = os.path.join(current_dir, const.DEFAULT_HISTORY_FILE_NAME)  # 如果文件夹内还没json聊天文件，比如 all_files =[] ，就用默认的
        
        st.session_state.file_path = current_file_path  # 将局部变量挂载到全局 session_state，让 main.py 能读取到
        
        # =================== 存档加载逻辑 (防抖) ===================
        # 🔍 优化：逻辑清晰化，使用 session_state 里的标记位
        # 核心判定条件：  
        #   1. 文件切换： session_state 里存的文件名 和 当前选的不一样，说明用户刚切了存档
        #   2. 第一次初始化：session里还没初始化过meta ()
        # 这行 IF 语句是在做“防抖”和“状态判定”
        if (
            "file_path" not in st.session_state or                   # 情况1：程序刚启动，还没存过文件名
            st.session_state.file_path != current_file_path or  # 情况2：用户刚才点下拉框换了文件
            "meta" not in st.session_state                          # 情况3：元数据意外丢失（防御性编程）
        ):  
            # 只有满足上面条件，才会去读 current_file_path （这是昂贵的 IO 操作）
            meta, msgs = storagef.load_history(current_file_path) # 解包赋值：把返回的两个值分别给两个变量
            # 更新后端 Session 状态 (真正的数据)
            st.session_state.messages = msgs
            st.session_state.meta = meta # 这里给 meta 赋值了！
            st.session_state.file_path  = current_file_path
            # 同步 UI：强制同步前端 UI 组件的状态，直接修改 key 对应的 Session State，这会强制输入框显示新的值
            st.session_state.ui_prompt = meta.get("system_prompt", const.DEFAULT_SYSTEM_PROMPT)
            # 更新模型显示，要确保模型在列表里
            loaded_model = meta.get("model", const.MODEL_NAME_LIST[0])
            st.session_state.ui_model = loaded_model if loaded_model in const.MODEL_NAME_LIST else const.MODEL_NAME_LIST[0]

            st.toast(f"已加载存档: {selected_file}")



        # ============ 系统提示词与模型板块 ============
        st.subheader("🧠 模型参数")

        system_prompt = st.text_area("系统提示词", height=150, key="ui_prompt")  # 双向绑定：即赋值给变量，也更新 session_state 里的 ui_prompt
        selected_model = st.selectbox("选择模型", const.MODEL_NAME_LIST, key="ui_model") # 每次你修改 st.selectbox 的内容，脚本重跑，selected_model 变量就会拿到session里最新的值
        
        # 🛠️ 其他设置
        with st.expander("💎 Gemini 3 高级特性", expanded=True):
            # A. 思考等级 (Thinking Level)
            thinking_option = st.select_slider(
                "🤔 思考强度 (Thinking Level)",
                options=["Low (快)", "Medium (平衡)", "High (深思)"],
                value="High (深思)",
                help="High 模式会消耗更多 Token 进行深度推理"
            )
            # 映射表：UI显示 -> API参数值
            thinking_map = {
                "Low (快)": "low", 
                "Medium (平衡)": "medium", 
                "High (深思)": "high"
            }
            

        # ================ 参数打包 (存入 Session 供 main.py 读取) ================
        # 一定要把这些新参数存进去，main.py 才能拿到
        st.session_state.gemini_params = {"thinking_level": thinking_map[thinking_option]}

        # 实时更新 session_state 中的 Meta (以便后续保存)
        # 当用户在网页上修改输入框时，上面的 key 变量会自动变，我们只需要把它存回 current_meta
        st.session_state.meta = {
            "system_prompt": system_prompt,  # 这里取到的就是 key="ui_prompt" 的最新值
            "model": selected_model,
            # 把高级参数也存进存档，这样下次加载存档时能恢复
            "gemini_config": st.session_state.gemini_params 
        }
        st.markdown("---")

        # ============ 归档功能 (Callback) ============
        # Callback 回调写法 = 先改票，再上车。Streamlit 机制规定凡是触发了 callback ，脚本执行完 callback 后会自动 Rerun 一遍脚本
        # 参数：args=(current_file_path,), 标注：这里的 args 必须是 Iterable (可迭代对象)用于把当前的路径传给回调函数
        st.button("💾 归档并开启新对话", on_click=storagef.archive_current_chat, args=(current_file_path,)) 



