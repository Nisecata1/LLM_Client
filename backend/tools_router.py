

import sys
import os

# 进程空间的“动态链接”与“指令分发”
# 这个文件包含两个核心知识点：操作系统层面的文件路径/模块加载，以及 网络层面的 HTTP 协议处理。

# =================================================================
# 知识点：动态修改 sys.path
# =================================================================
# 【操作系统层面解释】：
# 当一个进程（Process）启动时，OS 会加载代码段、数据段。
# Python 解释器在运行时，维护了一个变量 sys.path，它是一个列表，
# 里面存着所有“库文件”的搜索路径（类似于 Linux 的 $PATH 环境变量，或者 ld.so.conf）。

# 问题：你的 `src` 文件夹在 `backend` 的上一级。默认情况下，Python 只能看到当前目录。
# 解决：我们需要手动把“上一级目录”加入到这个搜索列表中。

# 1. os.path.abspath(__file__): 获取当前代码文件在硬盘上的绝对路径 (e.g., /home/user/project/backend/tools_router.py)
# 2. os.path.dirname(...): 去掉文件名，拿到目录 (e.g., /home/user/project/backend)
# 3. os.path.dirname(...): 再去一次目录，拿到上一级 (e.g., /home/user/project) —— 这就是项目根目录！
# 4. sys.path.append(...): 把这个根目录的地址，压入 sys.path 列表的末尾。
# --- 骚操作：为了导入 src 里的模块，把上一级目录加入环境，这样python就能看到了 ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# -----------------------------------------------------------
# 只有执行了上面那行，下面这行 import 才能在文件系统中找到 `src` 文件夹。
from fastapi import APIRouter
from src import toolbox_logic  # 直接复用你现有的逻辑代码！
from backend.schemas import BatchConvertRequest

# 实例化一个路由器对象。
# 你可以把它理解为交换机里的“路由表”片段，负责记录 URL -> 函数 的映射关系。
router = APIRouter()

# =================================================================
# 定义接口：POST 请求
# =================================================================
# 【计算机网络层面解释】：
# @router.post: 监听 HTTP 协议的 POST 方法。
# URL路径: "/convert/py-to-txt"
# 为什么用 POST？因为我们要“上传”数据（路径列表）给服务器，这符合 HTTP 语义。
# 如果是 GET，参数通常挂在 URL 后面，长度受限且不安全。
@router.post("/convert/py-to-txt")

# 函数定义：这是真正的“业务处理指令”。
# request: BatchConvertRequest -> 这叫“依赖注入”。
# FastAPI 会在调用这个函数前，先读取 TCP Buffer 中的 HTTP Body 数据，
# 用刚才定义的 BatchConvertRequest 模板解析好，再传给这个函数。
def run_conversion(request: BatchConvertRequest):
    """
    接收前端发来的路径列表，调用本地的转换函数。
    """

    # 1. 内存寻址：从对象中取出数据
    # 从请求模型里把数据拿出来
    sources = request.source_paths
    target = request.target_path
    
    # 2. 调用你原本写好的逻辑函数
    # 压栈调用：此时 CPU 的 PC (Program Counter) 指针跳转到 toolbox_logic.py 的代码段执行。
    # 这是一个典型的函数调用过程：保存现场 -> 跳转 -> 执行 -> 恢复现场。
    # [IO 操作警告]：这个函数内部涉及磁盘 IO (glob, shutil.copy)。
    # 在操作系统看来，这会让当前线程从“运行态”短暂切换到“阻塞态”，等待 DMA 把磁盘数据搬到内存。
    # 注意：toolbox_logic.batch_convert_py_to_txt 返回的是 (bool, str)
    success, msg = toolbox_logic.batch_convert_py_to_txt(sources, target)
    
    # 3. 构建响应：返回 JSON 结果给前端
    # 将结果打包成字典。FastAPI 稍后会把这个字典序列化成 JSON 字节流，
    # 写入 TCP Socket 的发送缓冲区 (Send Buffer)。
    return {
        "status": "success" if success else "error",
        "message": msg,
        "processed_paths": sources
    }