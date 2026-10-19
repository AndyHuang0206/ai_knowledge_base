from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime


# --------------------------
# 1. state_schema：全局状态（整个图共享、持久化）
# --------------------------
class GraphState(TypedDict):
    query: str
    answer: str
    step: int


# --------------------------
# 2. context_schema：运行时上下文（不可变、单次调用、不持久化）
# --------------------------
class RunContext(TypedDict):
    user_id: str
    debug: bool


# --------------------------
# 3. input_schema：图的入口格式（invoke时传的结构）
# --------------------------
class GraphInput(TypedDict):
    query: str


# --------------------------
# 4. output_schema：图的出口格式（invoke返回的结构）
# --------------------------
class GraphOutput(TypedDict):
    answer: str


# --------------------------
# 节点函数（纯函数，无装饰器）
# --------------------------
def process_node(state: GraphState, runtime: Runtime[RunContext]) -> GraphState:
    # 用全局 state
    # 注意：step 不在 GraphInput 里，图入口不会写入它，所以首次执行时 state 中没有这个 key。
    # TypedDict 只是类型标注，运行时就是普通 dict —— 缺 key 直接 KeyError，必须自己兜底。
    current_step = state.get("step", 0)
    print("当前 step:", current_step)
    # 用临时 context（不进 state）
    if runtime.context["debug"]:
        print("debug 模式：用户ID", runtime.context["user_id"])
    # 更新 state
    return {
        "answer": f"回复：{state['query']}",
        "step": current_step + 1
    }


# --------------------------
# 核心：创建 StateGraph 时直接传 4 个 schema（不用装饰器）
# --------------------------
builder = StateGraph(
    state_schema=GraphState,      # 全局状态
    context_schema=RunContext,    # 临时上下文
    input_schema=GraphInput,      # 图输入
    output_schema=GraphOutput     # 图输出
)

# 添加节点、边
builder.add_node("process", process_node)
builder.add_edge(START, "process")
builder.add_edge("process", END)

# 编译图
graph = builder.compile()


# --------------------------
# 调用（严格按 input_schema，返回按 output_schema）
# --------------------------
result = graph.invoke(
    input={"query": "什么是 LangGraph？"},  # 匹配 GraphInput
    context={"user_id": "u123", "debug": True}  # 匹配 RunContext
)

print("最终结果:", result)  # 只含 answer（匹配 GraphOutput）