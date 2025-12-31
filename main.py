import os
import json
import streamlit as st      # Web 版需要用到 Streamlit库的方法, 搞清楚在干什么就行

# 自己的库
import src.constants as const               # 导入全局常量模块
import src.storage_module as storage        # 导入文件操作函数模块
import src.ui_components as ui              # 导入UI组件模块
import src.chat_logic as chat_logic         # 导入聊天逻辑模块
import src.model_tools_call_functions as tools    # 导入函数工具调用模块


# ===================================架构逻辑===============================================
#  MVC (Model-View-Controller) 
# 使用 st.session_state 作为“数据总线”，在不同函数间传递数据，session_state 在内存里，存活于整个 Streamlit 会话期间。
# 在 Streamlit 中，跨文件/跨模块传递变量的最佳实践不是 return，而是直接读写 st.session_state。
# =========================================================================================


storage.debug_log("--- 🔄 页面刷新 (Rerun) ---")

# 程序入口(页面基本配置)
st.set_page_config(page_title="AI 助手 (Web版)", page_icon="🐱", layout="wide") # wide模式视野更好
# 初始化
chat_logic.init_session()
chat_logic.initial_client()

# ================= 架构：使用 Sidebar 导航ai聊天tab和工具箱tab =================
# 解决 Tab 滚动消失问题：把模式切换放到侧边栏最上方
with st.sidebar:
    app_mode = st.radio("功能导航", ["💬 AI 对话", "🛠️ 工具箱"], index=0)  # 使用 Radio 实现“页面路由”效果
    st.markdown("---")

# 根据选择的模式渲染侧边栏的参数区
ui.render_sidebar(current_mode="chat" if app_mode == "💬 AI 对话" else "tools")  # 负责侧边栏的所有交互和参数收集（存内存）


# ================= 主区域渲染 =================
if app_mode == "💬 AI 对话":
    st.title("🐱 AI Chat Assistant")
    
    # 渲染历史消息
    storage.debug_log(f"当前内存中有 {len(st.session_state.messages)} 条消息")
    storage.debug_log("开始渲染历史消息")
    chat_logic.render_history_timeline()
    storage.debug_log("渲染历史消息完成")   


    # 用户输入，并更新内存内容
    # 渲染输入区 (现在因为有 init_session，它一定会有值)
    storage.debug_log("正在等待用户输入")
    ui.user_input()

    # 通过刚刚更新的内存内容，发送请求
    storage.debug_log("进入request_logic()逻辑")
    chat_logic.request_logic()

elif app_mode == "🛠️ 工具箱":
    ui.render_toolbox()


