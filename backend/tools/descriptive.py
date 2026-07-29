"""描述统计 Tool。"""
from __future__ import annotations
from typing import Any
import pandas as pd
from langchain_core.tools import tool
from .common import read_dataframe


@tool
def descriptive_statistics(file_path: str, columns: list[str] | None = None) -> dict[str, Any]:
    """计算数值字段的样本量、均值、中位数、标准差、四分位数及极值。"""
    df = read_dataframe(file_path)
    selected = columns or [str(c) for c in df.select_dtypes(include="number").columns]
    missing = [c for c in selected if c not in df.columns]
    if missing:
        raise ValueError(f"字段不存在：{', '.join(missing)}")
    result: dict[str, Any] = {}
    for column in selected:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if values.empty:
            continue
        result[column] = {
            "count": int(values.count()),
            "mean": round(float(values.mean()), 4),
            "median": round(float(values.median()), 4),
            "std": round(float(values.std(ddof=1)), 4) if len(values) > 1 else 0.0,
            "min": round(float(values.min()), 4),
            "q1": round(float(values.quantile(0.25)), 4),
            "q3": round(float(values.quantile(0.75)), 4),
            "max": round(float(values.max()), 4),
            "missing_count": int(df[column].isna().sum()),
        }
    return {"row_count": int(len(df)), "statistics": result}
