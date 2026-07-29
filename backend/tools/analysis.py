"""企业销售基础统计分析 Tool。"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
from langchain_core.tools import tool

from .common import read_dataframe, to_json_value


def _require_columns(dataframe: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"数据缺少分析所需字段：{', '.join(missing)}")


@tool
def analyze_sales(
    file_path: str,
    sales_column: str,
    profit_column: Optional[str] = None,
    group_column: Optional[str] = None,
    top_n: int = 5,
) -> Dict[str, Any]:
    """计算销售额、订单均值、利润与可选分组排名等经营指标。

    Args:
        file_path: 待分析的 CSV、XLSX 或 XLS 文件绝对路径。
        sales_column: 销售额字段名，必须与文件表头完全一致。
        profit_column: 利润字段名；没有利润字段时可以不传。
        group_column: 地区、品类或产品等分组字段名；不传则不做排名。
        top_n: 返回销售额最高的分组数量，范围为 1 到 20。
    """
    if not 1 <= top_n <= 20:
        raise ValueError("top_n 必须在 1 到 20 之间")

    dataframe = read_dataframe(file_path)
    requested = [sales_column]
    if profit_column:
        requested.append(profit_column)
    if group_column:
        requested.append(group_column)
    _require_columns(dataframe, requested)

    sales = pd.to_numeric(dataframe[sales_column], errors="coerce")
    valid_sales = sales.dropna()
    if valid_sales.empty:
        raise ValueError(f"字段 {sales_column} 中没有可用于计算的数值")

    result: Dict[str, Any] = {
        "valid_sales_rows": int(valid_sales.count()),
        "invalid_sales_rows": int(sales.isna().sum()),
        "total_sales": round(float(valid_sales.sum()), 2),
        "average_sales": round(float(valid_sales.mean()), 2),
        "median_sales": round(float(valid_sales.median()), 2),
        "sales_std": round(float(valid_sales.std(ddof=1)), 2) if len(valid_sales) > 1 else 0.0,
        "min_sales": round(float(valid_sales.min()), 2),
        "max_sales": round(float(valid_sales.max()), 2),
    }

    if profit_column:
        profit = pd.to_numeric(dataframe[profit_column], errors="coerce")
        total_profit = float(profit.dropna().sum())
        total_sales = float(valid_sales.sum())
        result["profit"] = {
            "total_profit": round(total_profit, 2),
            "profit_margin_percent": round(total_profit / total_sales * 100, 2) if total_sales else None,
            "loss_making_rows": int((profit < 0).sum()),
        }

    if group_column:
        grouped_frame = dataframe.assign(__sales=sales).dropna(subset=[group_column, "__sales"])
        ranking = (
            grouped_frame.groupby(group_column, dropna=False)["__sales"]
            .sum()
            .sort_values(ascending=False)
            .head(top_n)
        )
        result["top_groups_by_sales"] = [
            {"group": to_json_value(group), "sales": round(float(amount), 2)}
            for group, amount in ranking.items()
        ]

    return result
