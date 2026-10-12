"""LangGraph：模型决策、专业分析 Tool 与模型总结循环。"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Literal
from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from backend.tools import (load_dataset, check_data_quality, descriptive_statistics,
    calculate_business_kpis, analyze_time_trend, analyze_correlation,
    detect_zscore_anomalies, generate_business_charts, generate_word_report)
from .prompts import SYSTEM_PROMPT
from .state import AnalysisAgentState

TOOLS = [load_dataset, check_data_quality, descriptive_statistics, calculate_business_kpis,
         analyze_time_trend, analyze_correlation, detect_zscore_anomalies,
         generate_business_charts, generate_word_report]


def build_agent(model: Any):
    #把tool的名称参数，描述告诉大模型
    model_with_tools = model.bind_tools(TOOLS)
    def llm_call(state: AnalysisAgentState) -> dict:
        response = model_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT.format(file_path=state["file_path"])), *state["messages"]])
        return {"messages": [response], "llm_calls": state.get("llm_calls", 0) + 1}
    def should_continue(state: AnalysisAgentState) -> Literal["tools", "end"]:
        return "tools" if getattr(state["messages"][-1], "tool_calls", None) else "end"
    builder = StateGraph(AnalysisAgentState); builder.add_node("llm_call", llm_call); builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "llm_call"); builder.add_conditional_edges("llm_call", should_continue, {"tools":"tools", "end":END})
    builder.add_edge("tools", "llm_call"); return builder.compile()


def save_mermaid_graph(agent: Any, output_path: str) -> Path:
    path = Path(output_path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(agent.get_graph(xray=True).draw_mermaid(), encoding="utf-8"); return path
