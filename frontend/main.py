# 启动入口 (Streamlit)

import os
import sys
import json
import streamlit as st  # 导入 Streamlit 库
# 导入自己的库
# 路径补丁：将项目根目录添加到 sys.path，让前端能找到 shared 和 frontend 自身，以便导入自己的模块
# 找当前文件所在目录的上级目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
if project_root not in sys.path:  # 如果 project_root 不在 sys.path 中，则添加
    sys.path.insert(0, project_root)
from shared import constants as const
from frontend.handlers import session_handler, chat_handler
from frontend.components import sidebar_ui, chat_ui, toolbox_ui


# =========================== 架构逻辑：MVC (Model-View-Controller) =====================================
# 在前端 Streamlit 中，而是直接通过读写内存的 st.session_state 跨文件/跨模块传递变量
# 组件内部使用 session_state 对象来获取和设置数据。
# 当页面刷新时，session_state 对象会保持不变，因此数据不会丢失。
# 后端另说
session_handler.debug_log("--- 🔄 页面刷新 (Rerun) ---")

# 页面基本配置
st.set_page_config(page_title="AI 助手 (Web版)", page_icon="🐱", layout="wide") # wide模式视野更好


# 初始化 Session State (委托给 Handler 处理)
if "init_done" not in st.session_state:
    session_handler.reset_session_state()

# 内存关键字初始化 (force=False 保证状态在 Rerun 间持久化)
session_handler.reset_session_state(False)



# # 将模式切换放侧边栏：模型聊天、工具箱界面
with st.sidebar:  
    app_mode = st.radio("功能导航", ["💬 AI 对话", "🛠️ 工具箱"], index=0)  # 使用 Radio 实现“页面路由”效果
    st.markdown("---")
# 根据选择的模式渲染侧边栏的参数区
session_handler.debug_log("即将渲染侧边栏")
sidebar_ui.render_sidebar(current_mode="chat" if app_mode == "💬 AI 对话" else "tools")  # 负责侧边栏的所有交互和参数收集（存内存）
session_handler.debug_log("渲染完成")

# ================= 主区域渲染 =================
if app_mode == "💬 AI 对话":
    st.title("🐱 AI Chat Assistant")
    chat_ui.chat_render()
    session_handler.debug_log("退出 main.chat_render 函数")

elif app_mode == "🛠️ 工具箱":
    toolbox_ui.render_toolbox()
