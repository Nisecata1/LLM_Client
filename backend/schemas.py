
# 数据契约 (Pydantic)
# 类型安全：在多人协作或大型前端对接时，这套 Schema 就是“合同”。



# pydantic 库原理：这是一个基于 Python "类型提示" (Type Hints) 的数据验证库。
# 它可以看作是一个“序列化/反序列化”引擎。
# 定义数据模型：FastAPI 最强的地方在于它用 Pydantic 库来强制检查数据格式。
# 该检查方法封装在 Pydantic 的 BaseModel 类中
from pydantic import BaseModel  # 引入 BaseModel, 后续被继承到你的数据模型中
from typing import List, Optional, Union, Dict, Any  # 引入 Union, Dict, Any

# 【底层原理】：
# - `BaseModel` 内部实现了一套复杂的 `__init__` 和验证逻辑。
# - __元数据检测__：它会读取你定义的 `source_paths: List[str]` 这些“类型注解”。
# - __实例化即检测__：每当你尝试执行 `BatchConvertRequest(source_paths=...)` 时，它就会自动跑一遍检测。如果数据不对，它直接抛出异常，根本不需要你手动写 `if/else`。
class BatchConvertRequest(BaseModel):
    # 定义一个类，继承自 BaseModel: 就是在定义“Py转Txt”这个功能需要传的参数
    # 前端发来的请求必须符合这个类的格式，否则 FastAPI 直接拒收并返回原消息
    # Schema 类可共享: 如果多个功能如果参数结构相似/一致，绑定路由的时候可以共享
    # ---------------------------------------------------------
    # 当网络发来一个 JSON：{"source_paths": ["/home/a", "/home/b"]}并被塞进来
    # 1. Pydantic 会在堆内存(Heap)中开辟空间。反序列化这个json
    # 2. 利用 BaseModel 的方法，检查 JSON 里的值是不是数组，数组里是不是字符串。
    # 3. 如果是，它就构建一个 Python List 对象填进去。不是就报错（类型安全检查）。
    source_paths: List[str]  # 字段定义：source_paths；类型：List[str]字符串列表

    # ---------------------------------------------------------
    # 字段定义：target_path
    # 类型：Optional[str] = None
    # ---------------------------------------------------------
    # 【408 联想 - 数据结构】：
    # Optional 表示这个值可以存在，也可以是空（None/Null）。
    # "= None" 是默认值。如果网络包里没有这个字段，内存里这个变量就被初始化为 0x0 (空指针/None)。
    target_path: Optional[str] = None # 可选字符串，默认是 None


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str


class ChatMessage(BaseModel):
    """单条消息的规定格式"""
    role: str
    # content 字段：允许是 字符串 OR 字典列表
    content: Optional[Union[str, List[Dict[str, Any]]]] = None 

    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    """对话请求模型。极简架构：只传上下文消息，后端自取配置。"""
    messages: List[ChatMessage]
