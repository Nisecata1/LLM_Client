
import os
import time
import streamlit as st

# 自己的库
import shared.constants as const
from backend.core import storage  # 导入 storage 模块
import frontend.handlers.session_handler as session_handler
import frontend.api_client as api
import frontend.handlers.chat_handler as ui





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
                with st.spinner("正在通过 API 调用后端服务..."):
                    # --- [架构演进]：不再直接调用本地函数，而是走网络请求 ---
                    client = api.get_api_client()
                    result = client.convert_py_to_txt(const.SOURCE_CODE_DIRS, target_dir)
                    
                    if result.get("status"):
                        st.success("转换完成！")
                        st.text_area("后端执行日志", value=result.get("message", ""), height=400)
                    else:
                        st.error(f"转换失败: {result.get('message', '未知错误')}")
                        if "details" in result:
                            with st.expander("查看错误详情"):
                                st.code(result["details"])
