"""企业经营 KPI Tool。"""
from __future__ import annotations
from typing import Any
import pandas as pd
from langchain_core.tools import tool
from .common import read_dataframe


@tool
def calculate_business_kpis(
    file_path: str,
    sales_column: str,
    profit_column: str | None = None,
    quantity_column: str | None = None,
    order_id_column: str | None = None,
) -> dict[str, Any]:
    """计算销售额、利润率、客单值、销量和亏损记录等 KPI。"""
    df = read_dataframe(file_path)
    required = [sales_column] + [c for c in (profit_column, quantity_column, order_id_column) if c]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"字段不存在：{', '.join(missing)}")
    sales = pd.to_numeric(df[sales_column], errors="coerce")
    total_sales = float(sales.sum())
    order_count = int(df[order_id_column].nunique()) if order_id_column else int(sales.count())
    result: dict[str, Any] = {
        "total_sales": round(total_sales, 2),
        "order_count": order_count,
        "average_order_value": round(total_sales / order_count, 2) if order_count else None,
    }
    if profit_column:
        profit = pd.to_numeric(df[profit_column], errors="coerce")
        total_profit = float(profit.sum())
        result.update({
            "total_profit": round(total_profit, 2),
            "profit_margin_percent": round(total_profit / total_sales * 100, 2) if total_sales else None,
            "loss_making_rows": int((profit < 0).sum()),
        })
    if quantity_column:
        quantity = pd.to_numeric(df[quantity_column], errors="coerce")
        result["total_quantity"] = round(float(quantity.sum()), 2)
    return result
