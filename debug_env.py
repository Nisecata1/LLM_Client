import sys
import os
import datetime

def run_diagnostic():
    print("="*30)
    print("🚀 运行环境诊断...")
    print(f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查核心文件是否存在
    files_to_check = ["main.py", "backend/main.py", "requirements-minimal.txt"]
    print("\n📂 核心文件状态:")
    for f in files_to_check:
        status = "✅ 存在" if os.path.exists(f) else "❌ 缺失"
        print(f" - {f}: {status}")
    
    print("="*30)

if __name__ == "__main__":
    run_diagnostic()
