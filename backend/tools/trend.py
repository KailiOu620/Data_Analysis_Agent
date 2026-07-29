"""时间趋势分析 Tool。"""
from __future__ import annotations
from typing import Any
import pandas as pd
from langchain_core.tools import tool
from .common import read_dataframe

FREQUENCIES = {"month": "ME", "quarter": "QE", "year": "YE"}


@tool
def analyze_time_trend(file_path: str, date_column: str, value_column: str, frequency: str = "month") -> dict[str, Any]:
    """按月、季度或年度聚合指标，计算环比变化与趋势方向。"""
    if frequency not in FREQUENCIES:
        raise ValueError("frequency 只能是 month、quarter 或 year")
    df = read_dataframe(file_path)
    if date_column not in df or value_column not in df:
        raise ValueError("日期字段或指标字段不存在")
    dates = pd.to_datetime(df[date_column], errors="coerce")
    values = pd.to_numeric(df[value_column], errors="coerce")
    series = pd.DataFrame({"date": dates, "value": values}).dropna().set_index("date")["value"]
    grouped = series.resample(FREQUENCIES[frequency]).sum()
    if grouped.empty:
        raise ValueError("没有可用于趋势分析的数据")
    growth = grouped.pct_change(fill_method=None) * 100
    periods = [{"period": i.strftime("%Y-%m-%d"), "value": round(float(v), 2),
                "growth_percent": None if pd.isna(growth.loc[i]) else round(float(growth.loc[i]), 2)}
               for i, v in grouped.items()]
    first, last = float(grouped.iloc[0]), float(grouped.iloc[-1])
    overall = (last / first - 1) * 100 if first else None
    return {
        "frequency": frequency,
        "periods": periods,
        "overall_growth_percent": None if overall is None else round(overall, 2),
        "direction": "上升" if last > first else "下降" if last < first else "持平",
        "peak_period": grouped.idxmax().strftime("%Y-%m-%d"),
        "peak_value": round(float(grouped.max()), 2),
        "lowest_period": grouped.idxmin().strftime("%Y-%m-%d"),
        "lowest_value": round(float(grouped.min()), 2),
    }
