import traceback
from fastapi import APIRouter
from backend import schemas
from backend.core import toolbox_logic  # 直接复用你现有的逻辑代码！
from backend.core import model_tools_call_functions as tools
from backend.core import chat_engine
from backend.core import storage


# 实例化一个路由器对象。
# 你可以把它理解为交换机里的“路由表”片段，负责记录 URL -> 函数 的映射关系。
router = APIRouter()

# 把 /chat 这个路径放一个处理函数
@router.post("/chat")
def run_chat(request: schemas.ChatRequest):
    """
    执行完整的对话逻辑。
    [极简架构]：后端不再依赖请求中的 model/params，而是内部自取。
    """
    engine = chat_engine.get_chat_engine()
    
    # 转换为 dict 列表，符合 chat_engine 接口

    messages_dict = [m.model_dump() for m in request.messages]
    
    # model 等配置由 run_chat 内部通过本地活跃存档加载
    try:
        return engine.run_chat(messages=messages_dict)
    except Exception as e:
        details = traceback.format_exc()
        # 这里用 print 而不是 logging：保持项目当前风格，且便于你从启动脚本控制台直接看到栈信息
        print(details)
        return {"status": "error", "message": str(e), "details": details}
