import os
import sys
import uvicorn
from fastapi import FastAPI


# =================================================================
# 知识点：修改 sys.path
# =================================================================
# Python 解释器在运行时，维护了一个变量 sys.path，它是一个列表，
# 里面存着所有“库文件”的搜索路径（类似于 Linux 的 $PATH 环境变量，或者 ld.so.conf）。
# 问题：你的 `src` 文件夹在 `backend` 的上一级。默认情况下，Python 只能看到当前目录。
# 解决：我们需要手动把“上一级目录”加入到这个搜索列表中。
# 1. os.path.abspath(__file__): 获取当前代码文件在硬盘上的绝对路径 (e.g., /home/user/project/backend/tools_router.py)
# 2. os.path.dirname(...): 去掉文件名，拿到目录 (e.g., /home/user/project/backend)
# 3. os.path.dirname(...): 再去一次目录，拿到上一级 (e.g., /home/user/project) —— 这就是项目根目录！
# 4. sys.path.append(...): 把这个根目录的地址，压入 sys.path 列表的末尾。
# 将项目根目录加入 sys.path，否则后端找不到 'shared' 或 'backend' 模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# 导入路由模块（相当于把子模块的代码加载进内存）
from backend.routers import tools_router, chat_router

# 初始化 App 对象: 这就像是创建了一个“服务器进程”的主控制块 (PCB 的概念延伸)。
app = FastAPI(title="我的 AI 工具箱后端")

# 注册路由（路由聚合）
# 原理：有点像路由聚合，把多个路由表合并到主路由表中。
# 以后遇到"/api/tools"，给到 tools_router.router 处理。
# 以后遇到"/api/chat"，给到 chat_router.router 处理。
app.include_router(tools_router, prefix="/api/tools", tags=["工具箱"])
app.include_router(chat_router.router, prefix="/api/chat", tags=["聊天"]) 
# 它的意义在于命名空间隔离：防止冲突。
# 比如聊天模块也有个 `/status` 接口，工具模块也有个 `/status` 接口
# 加上前缀变成了 `/api/chat/status` 和 `/api/tools/status`，完美避开。

# 心跳检测接口
@app.get("/")  # 装饰器逻辑：给下面这个函数绑定一个 HTTP GET 路由，路径是 "/"
def health_check():
    return {"status": "running", "message": "后端活得好好的"}


# =================================================================
# 程序启动入口
# =================================================================
if __name__ == "__main__":
    # uvicorn.run 是一个非常重的操作，它启动了一个 ASGI 服务器。
    # 【408 联想 - 网络编程 Socket】：
    # 这一行代码底层执行了类似 C 语言 Socket 编程的以下步骤：
    
    # 1. socket(): 创建一个套接字文件描述符 (File Descriptor)。
    # 2. bind(): 将套接字绑定到 IP (127.0.0.1) 和 端口 (8000)。
    #    - 127.0.0.1 (Loopback): 只有本机能访问，数据包不走网卡，直接在内核协议栈回环。
    #    - 端口 8000: 在传输层标识这个进程。
    # 3. listen(): 开始监听端口，等待 TCP 三次握手。
    # 4. accept(): 阻塞等待，直到有客户端连接。
    
    # 同时，Uvicorn 启动了一个“事件循环” (Event Loop)。
    # 这是现代高并发的核心（IO 多路复用，Linux 下通常使用 epoll 系统调用）。
    # 它允许单线程同时处理成千上万个并发连接，而不是来一个连接开一个线程。
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
    # reload=True: 这是一个开发功能。
    # 主进程会 fork 一个子进程来运行服务，可以
    # 主进程会监听文件系统事件 (inotify)，一旦代码变动，就 kill 掉子进程并重新 fork 一个。
