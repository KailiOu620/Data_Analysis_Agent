"""不依赖 LM Studio 的 LangGraph 节点与路由测试。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from backend.agent.graph import build_agent, save_mermaid_graph


class DeterministicToolCallingModel:
    """确定性假模型：第一次调用工具，收到结果后返回最终回答。"""

    def bind_tools(self, tools: list[Any]) -> "DeterministicToolCallingModel":
        self.tool_names = {item.name for item in tools}
        return self

    def invoke(self, messages: list[Any]) -> AIMessage:
        if not any(isinstance(message, ToolMessage) for message in messages):
            assert "load_dataset" in self.tool_names
            system_content = str(messages[0].content)
            file_path = system_content.split("当前数据文件的绝对路径：", 1)[1].splitlines()[0]
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "load_dataset",
                        "args": {"file_path": file_path, "preview_rows": 2},
                        "id": "test-call-1",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(content="已读取数据文件，并完成结构检查。")


def _make_sales_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "sales.csv"
    pd.DataFrame({"Region": ["华东"], "Sales": [100]}).to_csv(
        file_path, index=False, encoding="utf-8-sig"
    )
    return file_path


def test_agent_executes_tool_and_returns_to_model(tmp_path: Path) -> None:
    """验证 START→llm_call→tools→llm_call→END 的完整路径。"""
    file_path = _make_sales_file(tmp_path)
    agent = build_agent(DeterministicToolCallingModel())

    result = agent.invoke(
        {
            "messages": [HumanMessage(content="读取这个文件")],
            "file_path": str(file_path.resolve()),
            "llm_calls": 0,
        }
    )

    assert result["llm_calls"] == 2
    assert any(isinstance(message, ToolMessage) for message in result["messages"])
    assert result["messages"][-1].content == "已读取数据文件，并完成结构检查。"


def test_graph_can_be_exported(tmp_path: Path) -> None:
    """验证图结构可以导出供项目展示。"""
    agent = build_agent(DeterministicToolCallingModel())
    output_path = save_mermaid_graph(agent, str(tmp_path / "graph.mmd"))
    graph_text = output_path.read_text(encoding="utf-8")
    assert "llm_call" in graph_text
    assert "tools" in graph_text
