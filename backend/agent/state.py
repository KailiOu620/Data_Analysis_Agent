"""LangGraph 状态定义。"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AnalysisAgentState(TypedDict):
    """图中所有节点共享的最小状态。"""

    # add_messages 会追加并按消息 id 更新消息，避免节点覆盖历史记录。
    messages: Annotated[list[AnyMessage], add_messages]
    # 文件路径单独放在状态中，不依赖用户每次在问题中重复输入。
    file_path: str
    # 记录一次任务中模型节点的调用次数，便于测试和后续评估。
    llm_calls: int
