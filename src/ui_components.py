
import os
import time
import streamlit as st

# 自己的库
import src.constants as const
import src.storage_module as storage
import src.toolbox_logic as toolbox


# 所有ui组件的定义
# 用于收集侧边栏的所有ui参数的逻辑, 以及用户输入框的参数收集
# 每个ui参数绑定一个回调函数, 每次参数变动时，都会触发回调函数：同步更新内存，即前端UI


def user_input():
    # 创建两列，左边放个小的回形针按钮，右边留空
    col_upload, col_space = st.columns([1, 8]) 


    with col_upload:
        # 变成一个气泡菜单，图标是回形针
        with st.popover("📎", help="上传图片"):
            uploaded_file = st.file_uploader("选择图片", type=["png", "jpg", "jpeg"], key="img_uploader")

    # st.chat_input 类似于 input()，但它同时构建了整个 Web 的交互循环
    if user_input := st.chat_input("Shift+Enter 换行...输入你的问题..."):  
        storage.debug_log(f"用户输入了: {user_input[:20]}...")

        # # --- 渲染用户输入进对话框 ---
        # with st.chat_message("user"):
        #     st.markdown(user_input)
        # st.session_state.messages.append({"role": "user", "content": user_input})  # 同时append进内存

        # 1. 构造基础消息
        new_msg = {"role": "user", "content": []}
        
        # 2. 如果有图，模式切换为 List
        if uploaded_file:
            storage.debug_log("检测到图片上传，正在转码...")
            base64_img = storage.encode_image_to_base64(uploaded_file)
            # 写入图片
            new_msg["content"].append({
                "type": "image_url",
                "image_url": {"url": base64_img}
            })
            # 写入文本 (必须显式 append)
            new_msg["content"].append({
                "type": "text", 
                "text": user_input
            })

        else:  # 如果没图，保持纯文本字符串 (兼容旧模式)
            new_msg["content"] = user_input 

        # 兼容性处理：如果没图，有些模型库可能喜欢纯字符串，但 OpenAI 官方库支持 List[dict]
        # 如果为了保险，可以判断：
        if not uploaded_file:
            new_msg["content"] = user_input # 回退到纯字符串模式，最安全

        # 4. 消息追加到内存 session 并显示
        st.session_state.messages.append(new_msg)
        storage.debug_log("消息已存入内存 Session...")
        # st.rerun() # 强制刷新，脚本会重新从第1行执行























# ======================== 侧边栏配置 (改版) =========================
def render_sidebar(current_mode):
    """
    根据 current_mode (chat 或 tools) 渲染不同的侧边栏
    """

    with st.sidebar:  # [侧边栏容器] with 语句创建了一个上下文环境，里面的组件渲染在 <aside> 侧边栏里
        
        st.header("⚙️控制台")

        if current_mode == "chat":  # 路径设置放哪里都行，或者只放在 chat 里
            st.caption("当前模式：AI 对话")
        # ============= 存档路径管理 (无需改代码即可修改) ==============
            # 创建一个下拉菜单
            with st.expander("📁 存档路径管理", expanded=False):  
                current_dir = storage.get_history_dir() # 获取当前存储路径
                # 给输入框的值绑定一个key，用户修改时会自动更新 session_state 里这个 key 的值
                st.text_input("数据存储路径", value=current_dir, key="ui_file_path") 
                # 当用户点击“更新路径”按钮时
                if st.button("更新路径"):  
                    storage.save_app_config(st.session_state.ui_file_path)  # IO: 将用户输入的路径保存到配置文件
                    st.success("路径已更新，正在刷新...")
                    time.sleep(1)
                    st.rerun() 

            # =================== 存档切换 ===================
            st.header("📂 存档与记忆")

            # 扫描文件夹，all_files对象接收并排序
            all_files = [x for x in os.listdir(current_dir) if x.endswith('.json')]
            all_files.sort(key=lambda x: os.path.getmtime(os.path.join(current_dir, x)), reverse=True)

            # 动态计算 default_index
            # 目的：让下拉框即使在 rerun 后，也默认选中当前 Session 里的那个文件
            default_index = 0
            if "file_path" in st.session_state and st.session_state.file_path:
                current_filename = os.path.basename(st.session_state.file_path)
                if current_filename in all_files:
                    default_index = all_files.index(current_filename)

            # 3. 渲染下拉框 (传入动态计算的 index)
            selected_file = st.selectbox(
                "选择存档", 
                all_files, 
                index=default_index if all_files else None,
                key="file_selector" # 建议加个 key，虽然不是必须，但利于调试
            )

            # 构造完整路径，用 current_file_path 对象接收
            if selected_file:
                current_file_path = os.path.join(current_dir, selected_file)  # os.path.join方法用于拼接完整路径
            else: 
                current_file_path = os.path.join(current_dir, const.DEFAULT_HISTORY_FILE_NAME)  # 如果文件夹内还没json聊天文件，比如 all_files =[] ，就用默认的
            
            # =================== 存档发生切换的加载逻辑 (防抖) ===================
            # 使用 session_state 里的标记位
            # 先判断需不需要加载当前文件的meta和消息列表

            # --- 切换存档前的自动保存 ---
            # 如果 session 里存的路径(旧) != 下拉框选的路径(新)
            if (
                "file_path" in st.session_state and 
                st.session_state.file_path != current_file_path and 
                "meta" in st.session_state
            ):
                # 1. 自动保存旧档案 (Auto-Save)
                storage.save_history()
                # 此时硬盘里的旧文件已经更新了参数和聊天记录

            # --- 加载新存档逻辑 ---
            if (
                "file_path" not in st.session_state or                   # 情况1：程序刚启动，还没存过文件名
                st.session_state.file_path != current_file_path or  # 情况2：用户刚才点下拉框换了文件
                "meta" not in st.session_state                          # 情况3：元数据意外丢失（防御性编程）
            ):  # 需要加载，进入加载逻辑
                # 读 current_file_path （IO 操作）
                meta, msgs = storage.load_history(current_file_path)
                st.session_state.messages = msgs  # 全部更新进后端 Session_state (真正的数据)
                st.session_state.meta = meta  
                st.session_state.file_path  = current_file_path

                # 同步 UI 状态
                st.session_state.ui_prompt = meta.get("system_prompt", const.DEFAULT_SYSTEM_PROMPT)  # 更新系统提示词显示
                st.session_state.ui_model = meta.get("model", const.MODEL_NAME_LIST[0])  # 更新模型显示
                st.session_state.ui_history_len = int(meta.get("history_len", 10))  # 更新历史长度显示
                st.session_state.gemini_params = meta.get("gemini_config", {})  # 恢复 Gemini 高级配置

                st.toast(f"已加载存档: {selected_file}")
                time.sleep(0.1)
                st.rerun()


            # ============ 侧边栏所有参数 ============

            st.subheader("🧠 参数")
            # 提示：现在只改内存，不会卡顿
            st.caption("Settings auto-save on switch.")

            # 1. System Prompt (绑定回调)
            st.text_area(
                "System Prompt", 
                height=150, 
                key="ui_prompt",   # 给 session_state 里更新的东西一个key, 以便后续能读取
                on_change=storage.sync_ui_to_meta  # 绑定回调函数
            )
            
            # 2. Model
            selected_model = st.selectbox(
                "Model", 
                const.MODEL_NAME_LIST, 
                key="ui_model",
                on_change=storage.sync_ui_to_meta
            )
            
            # 3. History Len (绑定回调)
            history_len = st.slider(
                "Memory Window (Rounds)", 
                min_value=1, 
                max_value=99, 
                value=st.session_state.get("ui_history_len", 10), 
                step=1, 
                key="ui_history_len",
                on_change=storage.sync_ui_to_meta
            )

            # 4. Gemini 3 Features
            with st.expander("💎 Gemini 3 Advanced", expanded=True):
                saved_params = st.session_state.get("gemini_params", {})  # 获取之前的设置 (默认 high)
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
                    on_change=storage.sync_ui_to_meta # 绑定回调
                )

                # Google Search
                use_search = st.toggle("🌐 启用 Google Search", value=False)
                st.session_state.gemini_params["use_search"] = use_search

            # 更新内存里的 gemini_params
            current_thinking_ui = st.session_state.get("ui_thinking", "High")
            st.session_state.gemini_params = {  
                "thinking_level": current_thinking_ui.lower() # High -> high
            }

            # 这一步是为了确保即便没有触发on_change，meta也是最新的
            st.session_state.meta.update({
                "system_prompt": st.session_state.ui_prompt,
                "model": selected_model,
                "gemini_config": st.session_state.gemini_params,
                "history_len": history_len
            })


            # ========== 保存配置按钮 ===========
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                # 手动保存配置按钮
                if st.button("💾 保存参数", use_container_width=True):
                    storage.save_history()
            
            with col2:
                # 归档功能按钮
                # 参数：args=(current_file_path,)这里的 args 必须是 Iterable (可迭代对象)用于把当前的路径传给回调函数
                st.button("💾 归档并开启新对话", on_click=storage.archive_current_chat, args=(current_file_path,), use_container_width=True)

        elif current_mode == "tools":
            st.caption("当前模式：开发者工具箱")
            st.info("在这里配置工具箱的全局参数")
            
        
            # 这里以后可以放工具箱的通用设置，比如 "默认导出路径" 的修改框
























# 增加一个 render_toolbox 函数，负责渲染工具箱的界面。
def render_toolbox():
    """渲染工具箱 Tab 的界面"""
    st.header("🛠️ 开发者工具箱")
    
    tool_option = st.radio("选择工具", 
        [
            "Py 转 Txt (批量)", 
            "其他工具..."
        ], 
        horizontal=True
    )
    st.markdown("---")
    
    
    if tool_option == "Py 转 Txt (批量)":
        st.subheader("批量源码转换")
        st.info(f"功能：读取 `constants.py` 中配置的 {len(const.SOURCE_CODE_DIRS)} 个路径，批量转换。")


        # 1. 显示配置列表 (只读，让用户确认)
        with st.expander("查看配置的源文件夹列表", expanded=True):
            st.json(const.SOURCE_CODE_DIRS)
            # st.info(f"当前源路径:{const.SOURCE_CODE_DIRS}")

        # 2. 输出路径选择
        target_dir = st.text_input("📂 输出目标汇总路径:", value=const.DEFAULT_EXPORT_DIR)
        
        # 3. 执行按钮
        if st.button("🚀 开始批量转换", type="primary"):
            if not const.SOURCE_CODE_DIRS:
                st.warning("请先在 `constants.py` 中配置 SOURCE_CODE_DIRS！")
            else:
                with st.spinner("正在疯狂转换中..."):
                    # 调用新写的批量逻辑
                    success, msg = toolbox.batch_convert_py_to_txt(const.SOURCE_CODE_DIRS, target_dir)
                    if success:
                        st.success("转换完成！")
                        st.text_area("执行日志", value=msg, height=400)
                    else:
                        st.error(msg)


