import subprocess
import time
import sys
import os
import requests

def is_backend_running(url="http://127.0.0.1:8000/"):
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except:
        return False

def start_app():
    print("🚀 正在启动 AI 助手一键启动脚本...")
    
    # 1. 启动后端 (FastAPI)
    print("📡 正在启动后端服务 (FastAPI)...")
    backend_process = subprocess.Popen(
        [sys.executable, "backend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=os.environ.copy()
    )
    
    # 2. 等待后端就绪
    print("⏳ 等待后端服务就绪...")
    max_retries = 10
    retry_count = 0
    while not is_backend_running() and retry_count < max_retries:
        time.sleep(1)
        retry_count += 1
        print(f"  尝试连接后端 ({retry_count}/{max_retries})...")
    
    if not is_backend_running():
        print("❌ 后端启动超时，请检查 backend/main.py 是否有错。")
        backend_process.terminate()
        return

    print("✅ 后端服务已就绪！")

    # 3. 启动前端 (Streamlit)
    print("🎨 正在启动前端界面 (Streamlit)...")
    frontend_process = subprocess.Popen(
        ["streamlit", "run", "frontend/main.py"],
        env=os.environ.copy()
    )

    print("\n" + "="*40)
    print("🎉 应用已成功启动！")
    print("👉 前端地址: http://localhost:8501")
    print("👉 后端地址: http://127.0.0.1:8000")
    print("="*40 + "\n")
    print("提示: 按 Ctrl+C 可以同时关闭前后端。")

    try:
        # 持续运行，直到用户按下 Ctrl+C
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 正在关闭应用...")
    finally:
        frontend_process.terminate()
        backend_process.terminate()
        print("👋 再见！")

if __name__ == "__main__":
    start_app()
