import os
import json
import streamlit as st      # Web 版需要用到 Streamlit库的方法, 搞清楚在干什么就行

# 自己的库
import src.constants as const               # 导入全局常量模块
import src.storage_module as storage   # 导入文件操作函数模块
import src.ui_components as ui              # 导入UI组件模块
import src.chat_logic as chat_logic      # 导入聊天逻辑模块
import src.tools_call_functions as tools    # 导入函数工具调用模块


# ===================================架构逻辑===============================================
# 使用 st.session_state 作为“数据总线”，在不同函数和组件间传递数据，他在内存里，存活于整个 Streamlit 会话期间。
# 在 Streamlit 中，跨文件/跨模块传递变量的最佳实践不是 return，而是直接读写 st.session_state。

# UI 模块 (ui_components) 负责采集参数（用户选了什么）。
# Session State 负责传输参数（数据总线）。
# Main 模块 负责消费参数（发送 API 请求）。
# 这种 MVC (Model-View-Controller) 的分离非常清晰。
# =========================================================================================


storage.debug_log("--- 🔄 页面刷新 (Rerun) ---")

# 页面基本配置
st.set_page_config(page_title="AI 助手 (Web版)", page_icon="🐱", layout="wide") # wide模式视野更好
st.title("🐱 AI Chat Assistant")

ui.render_sidebar()  # 负责侧边栏的所有交互逻辑和参数收集（存内存）

chat_logic.initial_client()

# 渲染历史消息
storage.debug_log(f"当前内存中有 {len(st.session_state.messages)} 条消息")
storage.debug_log("开始渲染历史消息")
chat_logic.render_history_timeline()
storage.debug_log("渲染历史消息完成")

# 用户输入，并更新内存内容
storage.debug_log("正在等待用户输入")
ui.user_input()

# 通过刚刚更新的内存内容，发送请求
storage.debug_log("进入request_logic()逻辑")
chat_logic.request_logic()


