import uvicorn
from fastapi import FastAPI
# 导入刚才写好的路由模块（相当于把子模块的代码加载进内存）
from tools_router import router as tools_router


# Socket 绑定与事件循环：这是程序的入口。在 408 计算机网络 (传输层) 和 操作系统 (进程管理) 中，这里发生了最多的事情。

# 初始化 App 对象: 这就像是创建了一个“服务器进程”的主控制块 (PCB 的概念延伸)。
app = FastAPI(title="我的 AI 工具箱后端")

# 路由注册：注册刚才写的路由。
# 原理：把 tools_router 里的路由表，合并到主路由表中。
# prefix="/api/tools": 这是一个命名空间。
# 以后访问必须加这个前缀，类似于文件系统的目录层级。
app.include_router(tools_router, prefix="/api/tools", tags=["工具箱"])


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