
# 引入 pydantic 库。
# 原理：这是一个基于 Python "类型提示" (Type Hints) 的数据验证库。
# 它可以看作是一个“序列化/反序列化”引擎。
from pydantic import BaseModel
from typing import List, Optional

# 定义数据模型：FastAPI 最强的地方在于它用 Pydantic 库来强制检查数据格式。我们先定义一下，“Py转Txt”这个功能需要传什么参数进来。

# 定义一个类，继承自 BaseModel。
# 【408 联想】：
# 这就像在 C 语言中定义一个 struct（结构体）。
# struct BatchConvertRequest {
#     char** source_paths;  // 字符串数组
#     char* target_path;    // 字符串指针（可能为 NULL）
# };
# 这就是我们定义的“快递单”格式
# 前端发来的请求必须符合这个格式，否则 FastAPI 直接拒收
class BatchConvertRequest(BaseModel):
    # ---------------------------------------------------------
    # 字段定义：source_paths
    # 类型：List[str]
    # ---------------------------------------------------------
    # 【底层原理】：
    # 当网络发来一个 JSON：{"source_paths": ["/home/a", "/home/b"]}
    # 1. Pydantic 会在堆内存(Heap)中开辟空间。
    # 2. 它检查 JSON 里的值是不是数组，数组里是不是字符串。
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