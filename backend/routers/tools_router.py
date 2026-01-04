# 后端的路由逻辑
from fastapi import APIRouter
from backend.schemas import BatchConvertRequest, SearchRequest, ChatRequest
from backend.core import toolbox_logic  # 直接复用你现有的逻辑代码！
from backend.core import model_tools_call_functions as tools
from backend.core import chat_engine


# 实例化一个路由器对象。
# 你可以把它理解为交换机里的“路由表”片段，负责记录 URL -> 函数 的映射关系。
router = APIRouter()

# =================================================================
# 定义接口：POST 请求
# 并存入router对象
# =================================================================
# 【计算机网络层面解释】：
# @router.post: 监听 HTTP 协议的 POST 方法。
# URL路径: "/convert/py-to-txt"
# 为什么用 POST？因为我们要“上传”数据（路径列表）给服务器，这符合 HTTP 语义。
# 如果是 GET，参数通常挂在 URL 后面，长度受限且不安全。
@router.post("/convert/py-to-txt")
    # 函数定义：这是真正的“业务处理逻辑”。
    # “依赖注入”：request: BatchConvertRequest
    # FastAPI 会在调用这个函数前，先读取 TCP Buffer 中的 HTTP Body 数据，塞进 BatchConvertRequest里
    # 用 schemas 中定义的 BatchConvertRequest 模板解析好，再传给这个函数。
    # BatchConvertRequest 这个类就像是一个 “安检门”。它立在函数的入口处，所有进来的数据必须经过它的扫描。
    # 如果数据不合格，直接踢走；如果合格，它就把数据整理得整整齐齐，交给 run_conversion 函数内部的逻辑去处理
def run_conversion(request: BatchConvertRequest):
    """
    接收前端发来的路径列表，调用本地的转换函数。
    """

    # 1. 从注入的对象中取出数据
    sources = request.source_paths
    target = request.target_path
    
    # 2. 调用你原本写好的逻辑函数
    # 压栈调用：此时 CPU 的 PC (Program Counter) 指针跳转到 toolbox_logic.py 的代码段执行。
    # 这是一个典型的函数调用过程：保存现场 -> 跳转 -> 执行 -> 恢复现场。
    # [IO 操作警告]：这个函数内部涉及磁盘 IO (glob, shutil.copy)。
    # 在操作系统看来，这会让当前线程从“运行态”短暂切换到“阻塞态”，等待 DMA 把磁盘数据搬到内存。
    bool, msg = toolbox_logic.batch_convert_py_to_txt(sources, target)
    # 注意：toolbox_logic.batch_convert_py_to_txt 返回的是 (bool, str)
    
    # 3. 构建响应：返回 JSON 结果给前端
    # 将结果打包成字典。FastAPI 稍后会把这个字典序列化成 JSON 字节流，
    # 写入 TCP Socket 的发送缓冲区 (Send Buffer)。
    return {
        "status": bool,
        "message": msg,
        "processed_paths": sources
    }

@router.get("/time")
def get_time():
    """获取系统当前时间"""
    return {"time": tools.get_current_time()}

@router.post("/search")
def run_search(request: SearchRequest):
    """执行模拟联网搜索"""
    result = tools.web_search(request.query)
    return {"result": result}

@router.post("/chat")
def run_chat(request: ChatRequest):
    """
    执行完整的对话逻辑。
    [极简架构]：后端不再依赖请求中的 model/params，而是内部自取。
    """
    engine = chat_engine.get_chat_engine()
    
    # 转换为 dict 列表，符合 chat_engine 接口
    messages_dict = [m.model_dump() for m in request.messages]
    
    # 注意：这里不再传入 request.model 等，由 run_chat 内部加载本地活跃存档配置
    result = engine.run_chat(messages=messages_dict)
    return result
