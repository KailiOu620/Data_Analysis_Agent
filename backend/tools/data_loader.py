"""数据读取 Tool：让 Agent 先了解文件结构，而不是把整张表交给 LLM。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langchain_core.tools import tool

from .common import read_dataframe, to_json_value


@tool
def load_dataset(file_path: str, preview_rows: int = 2) -> Dict[str, Any]:
    """读取 CSV/Excel 数据集并返回结构摘要。

    Args:
        file_path: 待分析的 CSV、XLSX 或 XLS 文件绝对路径。
        preview_rows: 返回的预览行数，范围为 1 到 20。
    """
    if not 1 <= preview_rows <= 20:
        raise ValueError("preview_rows 必须在 1 到 20 之间")

    dataframe = read_dataframe(file_path)
    preview = [
        {str(key): to_json_value(value) for key, value in row.items()}
        for row in dataframe.head(preview_rows).to_dict(orient="records")
    ]
    return {
        "file_name": Path(file_path).name,
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "columns": [str(column) for column in dataframe.columns],
        "dtypes": {str(key): str(value) for key, value in dataframe.dtypes.items()},
        "preview": preview,
    }
