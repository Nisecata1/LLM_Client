
import os
import time
import streamlit as st

# 自己的库
import src.constants as const
import src.app_base_functions as storagef


# 全靠回调，每个ui参数绑定一个回调函数
# 每次参数变动时，都会触发回调函数：同步更新ui并写回磁盘



# ======================== 侧边栏配置 =========================
def render_sidebar():
    with st.sidebar:  # [侧边栏容器] with 语句创建了一个上下文环境，里面的组件渲染在 <aside> 侧边栏里
        st.header("⚙️设置面板")

        # ============= 路径管理 (无需改代码即可修改) ==============

        # 创建一个下拉菜单
        with st.expander("📁 存储路径设置", expanded=False):  
            current_dir = storagef.get_history_dir() # 获取当前存储路径
            # 给输入框的值绑定一个key，用户修改时会自动更新 session_state 里这个 key 的值
            st.text_input("数据存储路径", value=current_dir, key="ui_file_path") 
            # 当用户点击“更新路径”按钮时
            if st.button("更新路径"):  
                storagef.save_app_config(st.session_state.ui_file_path)  # IO: 将用户输入的路径保存到配置文件
                st.success("路径已更新，正在刷新...")
                time.sleep(1)
                st.rerun() 

        # =================== 存档切换 ===================
        st.header("📂 存档与记忆")

        # 扫描文件夹，列出所有json文件并排序，用一个列表对象 all_files 存起来
        all_files = [x for x in os.listdir(current_dir) if x.endswith('.json')]
        all_files.sort(key=lambda x: os.path.getmtime(os.path.join(current_dir, x)), reverse=True)
        # st.selectbox 创建下拉选择框，用一个 selected_file 对象接收用户选择（默认为 index=0 即最新的那个文件）
        selected_file = st.selectbox("选择存档", all_files, index=0 if all_files else None)

        # 构造完整路径，用 current_file_path 对象接收
        if selected_file:
            current_file_path = os.path.join(current_dir, selected_file)  # os.path.join方法用于拼接完整路径
        else: 
            current_file_path = os.path.join(current_dir, const.DEFAULT_HISTORY_FILE_NAME)  # 如果文件夹内还没json聊天文件，比如 all_files =[] ，就用默认的
        
        
        # =================== 存档加载逻辑 (防抖) ===================
        # 使用 session_state 里的标记位
        # 先判断需不需要加载当前文件的meta和消息列表
        if (
            "file_path" not in st.session_state or                   # 情况1：程序刚启动，还没存过文件名
            st.session_state.file_path != current_file_path or  # 情况2：用户刚才点下拉框换了文件
            "meta" not in st.session_state                          # 情况3：元数据意外丢失（防御性编程）
        ):  # 需要加载，进入加载逻辑
            # 更新内存中的文件路径标记
            st.session_state.file_path = current_file_path
            # 读 current_file_path （IO 操作）重要
            meta, msgs = storagef.load_history(current_file_path)

            # 全部更新进后端 Session_state (真正的数据)
            st.session_state.messages = msgs
            st.session_state.meta = meta  
            st.session_state.file_path  = current_file_path

            # 同步前端 UI
            st.session_state.ui_prompt = meta.get("system_prompt", const.DEFAULT_SYSTEM_PROMPT)  # 更新系统提示词显示
            st.session_state.ui_model = meta.get("model", const.MODEL_NAME_LIST[0])  # 更新模型显示
            st.session_state.ui_history_len = int(meta.get("history_len", 10))  # 更新历史长度显示
            st.session_state.gemini_params = meta.get("gemini_config", {})  # 恢复 Gemini 高级配置

            st.toast(f"已加载存档: {selected_file}")
            time.sleep(0.1)
            st.rerun()

        # =======================================
        # ============ 侧边栏所有参数 ============
        # =======================================

        st.subheader("🧠 参数")

        # 1. System Prompt (绑定回调)
        st.text_area(
            "System Prompt", 
            height=150, 
            key="ui_prompt",   # 给 session_state 里更新的东西一个key, 以便后续能读取
            on_change=storagef.on_param_change 
        )
        
        # 2. Model
        selected_model = st.selectbox(
            "Model", 
            const.MODEL_NAME_LIST, 
            key="ui_model",
            on_change=storagef.on_param_change
        )
        
        # 3. History Len (绑定回调)
        history_len = st.slider(
            "Memory Window (Rounds)", 
            min_value=1, 
            max_value=99, 
            value=st.session_state.get("ui_history_len", 10), 
            step=1, 
            key="ui_history_len",
            on_change=storagef.on_param_change
        )


        # 4. Gemini 3 Features (简化版)
        with st.expander("💎 Gemini 3 Advanced", expanded=True):
            # 获取之前的设置 (默认 high)
            saved_params = st.session_state.get("gemini_params", {})
            saved_val = saved_params.get("thinking_level", "high") 
            
            # 简单转换: "high" -> "High" 用于显示
            default_ui_val = saved_val.capitalize() 
            if default_ui_val not in ["Low", "Medium", "High"]: 
                default_ui_val = "High"

            st.select_slider(
                "Thinking Level",
                options=["Low", "Medium", "High"], # 纯英文，简单明了
                value=default_ui_val,
                key="ui_thinking", # 绑定 Key
                on_change=storagef.on_param_change # 绑定回调
            )

        # 更新内存里的 gemini_params
        current_thinking_ui = st.session_state.get("ui_thinking", "High")
        st.session_state.gemini_params = {  
            "thinking_level": current_thinking_ui.lower() # High -> high
        }

        st.markdown("---")

        # 归档功能 (Callback)
        # Callback 回调写法 = 先改票，再上车。Streamlit 机制规定凡是触发了 callback ，脚本执行完 callback 后会自动 Rerun 一遍脚本
        # 参数：args=(current_file_path,), 标注：这里的 args 必须是 Iterable (可迭代对象)用于把当前的路径传给回调函数
        st.button("💾 归档并开启新对话", on_click=storagef.archive_current_chat, args=(current_file_path,)) 



