"""Pearson 相关性分析 Tool。"""
from __future__ import annotations
from typing import Any
import pandas as pd
from scipy.stats import pearsonr
from langchain_core.tools import tool
from .common import read_dataframe


@tool
def analyze_correlation(file_path: str, x_column: str, y_column: str) -> dict[str, Any]:
    """计算两个数值字段的 Pearson r、p 值、方向和强度。相关不代表因果。"""
    df = read_dataframe(file_path)
    if x_column not in df or y_column not in df:
        raise ValueError("相关性分析字段不存在")
    pairs = pd.DataFrame({"x": pd.to_numeric(df[x_column], errors="coerce"),
                          "y": pd.to_numeric(df[y_column], errors="coerce")}).dropna()
    if len(pairs) < 3 or pairs["x"].nunique() < 2 or pairs["y"].nunique() < 2:
        raise ValueError("有效样本不足或字段为常量，无法计算 Pearson 相关")
    r, p = pearsonr(pairs["x"], pairs["y"])
    absolute = abs(float(r))
    strength = "弱" if absolute < 0.3 else "中等" if absolute < 0.7 else "强"
    return {"x_column": x_column, "y_column": y_column, "sample_size": int(len(pairs)),
            "pearson_r": round(float(r), 4), "p_value": round(float(p), 6),
            "direction": "正相关" if r > 0 else "负相关" if r < 0 else "无线性相关",
            "strength": strength, "statistically_significant_0_05": bool(p < 0.05),
            "warning": "相关性不等于因果关系。"}
