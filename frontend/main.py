# 启动入口 (Streamlit)

import os
import sys
import json
import streamlit as st  # 导入 Streamlit 库

# 路径补丁：将项目根目录添加到 sys.path，让前端能找到 shared 和 frontend 自身，以便导入自己的模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 找当前文件所在目录的上级目录
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# 自己的库
from shared import constants as const                      # 导入全局常量模块
from frontend.handlers import file_handler as file_handler # 导入文件操作函数模块
from frontend.components import sidebar_ui as ui           # 导入UI组件模块 (已迁移至 frontend 目录)
from handlers import chat_handler                     # 导入聊天逻辑模块


# =========================== 架构逻辑 =====================================
# MVC (Model-View-Controller) 
# streamlit 库使用 st.session_state 作为"数据总线"，在不同函数间传递数据，session_state 在内存里，存活于整个 Streamlit 会话期间。
# 在 Streamlit 中，跨文件/跨模块传递变量的最佳实践不是 return，而是直接读写 st.session_state。
# =========================================================================================

file_handler.debug_log("--- 🔄 页面刷新 (Rerun) ---")

# 前端程序入口(页面基本配置)
st.set_page_config(page_title="AI 助手 (Web版)", page_icon="🐱", layout="wide") # wide模式视野更好
# 内存关键字初始化 (force=False 保证状态在 Rerun 间持久化)
file_handler.reset_session_state(False)

# Sidebar 导航模型聊天和工具箱界面
with st.sidebar:  # 将模式切换放侧边栏
    app_mode = st.radio("功能导航", ["💬 AI 对话", "🛠️ 工具箱"], index=0)  # 使用 Radio 实现“页面路由”效果
    st.markdown("---")
# 根据选择的模式渲染侧边栏的参数区
ui.render_sidebar(current_mode="chat" if app_mode == "💬 AI 对话" else "tools")  # 负责侧边栏的所有交互和参数收集（存内存）

# ================= 主区域渲染 =================
if app_mode == "💬 AI 对话":
    st.title("🐱 AI Chat Assistant")
    
    # 渲染历史消息
    file_handler.debug_log(f"当前内存中有 {len(st.session_state.messages)} 条消息")
    file_handler.debug_log("开始渲染历史消息")
    chat_handler.render_history_timeline()
    file_handler.debug_log("渲染历史消息完成") 

    # 渲染输入区并准备接收user input
    file_handler.debug_log("正在等待用户输入")
    ui.user_input()  # 自动更新内存

    # 通过刚刚更新的内存内容，发送请求
    file_handler.debug_log("进入request_logic()逻辑")
    chat_handler.request_logic()

elif app_mode == "🛠️ 工具箱":
    ui.render_toolbox()
