import copy
from typing import TypedDict, AnyStr, Any


class ImportGraphState(TypedDict):

    # 12个属性
    # 任务标识 -> context_state -> task_id
    task_id:str

    # 标记文件类型
    is_md_read_enabled:bool #是不是md
    is_pdf_read_enabled:bool #是不是pdf

    # 存储对应类型的文件地址
    md_path:str #专门存储md文件地址
    pdf_path:str #专门存储pdf文件地址

    # 文件数据内容
    md_content:str # md的文本内容 后续用于切割
    item_name:str # 文件唯一标识
    file_title:str  # 文件名 去掉后缀名 xx.txt->xx

    # 切片后的数据
    chunks:list[dict[str,Any]] # 切片内容 content item_name title。。。{content:x,item_name:x}
    embeddings_content:list[dict[str,Any]] # 装生成向量的切片内容 稠密和稀疏


# 定义一个对象模版 赋予少量的默认值
graph_default_state:ImportGraphState = {
    "task_id": "",
    "is_md_read_enabled": False,
    "is_pdf_read_enabled": False,
    "md_path": "",
    "pdf_path": "",
    "md_content": "",
    "item_name": "",
    "file_title": "",
    "chunks": [],
    "embeddings_content": []
}

def create_default_state(**kwargs)->ImportGraphState:
    """快速创建一个指定属性的state对象，并返回新的对象"""
    # **kwargs -> 动态 -> key=value传递参数 -> 要求key = 属性名 ->kwargs 字典
    new_state: ImportGraphState = copy.deepcopy(graph_default_state)
    new_state.update(kwargs)
    return new_state


def get_default_state()->ImportGraphState:
    """快速返回模版对象，不修改属性，返回的都是新的对象"""
    new_state:ImportGraphState = copy.deepcopy(graph_default_state)
    return new_state
