
# 数据契约 (Pydantic)

# 定义 Schema -> 编写函数 -> 绑定路由
# 解耦（Decoupling）：
#   `schemas.py` 负责数据格式（协议），
#   `toolbox_logic.py` 负责具体业务（算法），
#   `tools_router.py` 负责对外分发（接口）。
#       这样你改算法时不需要动接口，换接口协议时不需要动算法。
# 类型安全：在多人协作或大型前端对接时，这套 Schema 就是“合同”。

# 引入 pydantic 库。
# 原理：这是一个基于 Python "类型提示" (Type Hints) 的数据验证库。
# 它可以看作是一个“序列化/反序列化”引擎。
from pydantic import BaseModel
from typing import List, Optional

# 定义数据模型：FastAPI 最强的地方在于它用 Pydantic 库来强制检查数据格式。
# 该方法封装在 Pydantic 的 BaseModel 类中

# 定义一个类，继承自 BaseModel: 就是在定义“Py转Txt”这个功能需要传的参数
# 这就像在 C 语言中定义一个 struct（结构体）
# struct BatchConvertRequest {
#     char** source_paths;  // 字符串数组
#     char* target_path;    // 字符串指针（可能为 NULL）
# };
# 这就是我们定义的“快递单”格式，前端发来的请求必须符合这个格式，否则 FastAPI 直接拒收
# 共享 Schema: 注意如果多个功能如果参数结构相似/一致，绑定路由的时候可以共享
class BatchConvertRequest(BaseModel):
    # ---------------------------------------------------------
    # 字段定义：source_paths
    # 类型：List[str]
    # ---------------------------------------------------------
    # 【底层原理】：
    # - `BaseModel` 内部实现了一套复杂的 `__init__` 和验证逻辑。
    # - __元数据检测__：它会读取你定义的 `source_paths: List[str]` 这些“类型注解”。
    # - __实例化即检测__：每当你尝试执行 `BatchConvertRequest(source_paths=...)` 时，它就会自动跑一遍检测。如果数据不对，它直接抛出异常，根本不需要你手动写 `if/else`。

    # 当网络发来一个 JSON：{"source_paths": ["/home/a", "/home/b"]}并被塞进来
    # 1. Pydantic 会在堆内存(Heap)中开辟空间。反序列化这个json
    # 2. 利用 BaseModel 的方法，检查 JSON 里的值是不是数组，数组里是不是字符串。
    # 3. 如果是，它就构建一个 Python List 对象填进去。
    # 4. 如果你传了 [1, 2, 3]，它会报错（类型安全检查）。
    source_paths: List[str]           # 必须是字符串列表

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
    """单条消息模型"""
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    """对话请求模型。极简架构：只传上下文消息，后端自取配置。"""
    messages: List[ChatMessage]
