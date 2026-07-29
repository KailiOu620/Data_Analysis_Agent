"""经营分析图表生成 Tool。"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from langchain_core.tools import tool
from .common import read_dataframe


def _save(fig, path: Path) -> str:
    fig.tight_layout(); fig.savefig(path, dpi=160, bbox_inches="tight"); plt.close(fig)
    return str(path.resolve())


@tool
def generate_business_charts(file_path: str, output_dir: str, date_column: str | None = None,
                             sales_column: str | None = None, group_column: str | None = None,
                             x_column: str | None = None, y_column: str | None = None) -> dict[str, Any]:
    """按已提供字段生成趋势图、分组柱状图、散点图和箱线图。"""
    df = read_dataframe(file_path); out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    charts: dict[str, str] = {}
    if date_column and sales_column:
        dates = pd.to_datetime(df[date_column], errors="coerce"); values = pd.to_numeric(df[sales_column], errors="coerce")
        trend = pd.DataFrame({"date": dates, "value": values}).dropna().set_index("date")["value"].resample("ME").sum()
        fig, ax = plt.subplots(figsize=(8, 4.2)); ax.plot(trend.index, trend.values, marker="o", color="#2E74B5")
        ax.set(title=f"{sales_column} Trend", xlabel="Period", ylabel=sales_column); ax.grid(alpha=.25)
        charts["trend"] = _save(fig, out / "sales_trend.png")
        fig, ax = plt.subplots(figsize=(7, 3.8)); ax.boxplot(trend.values, vert=True); ax.set(title=f"{sales_column} Monthly Boxplot", ylabel=sales_column)
        charts["boxplot"] = _save(fig, out / "sales_boxplot.png")
    if group_column and sales_column:
        grouped = df.assign(_v=pd.to_numeric(df[sales_column], errors="coerce")).groupby(group_column)["_v"].sum().nlargest(10)
        fig, ax = plt.subplots(figsize=(8, 4.5)); grouped.sort_values().plot.barh(ax=ax, color="#4C9F70")
        ax.set(title=f"{sales_column} by {group_column}", xlabel=sales_column, ylabel=group_column)
        charts["group"] = _save(fig, out / "group_sales.png")
    if x_column and y_column:
        x = pd.to_numeric(df[x_column], errors="coerce"); y = pd.to_numeric(df[y_column], errors="coerce"); valid = x.notna() & y.notna()
        fig, ax = plt.subplots(figsize=(6.8, 4.5)); ax.scatter(x[valid], y[valid], alpha=.65, color="#D97706")
        ax.set(title=f"{y_column} vs {x_column}", xlabel=x_column, ylabel=y_column); ax.grid(alpha=.2)
        charts["scatter"] = _save(fig, out / "correlation_scatter.png")
    if not charts:
        raise ValueError("至少提供一组可绘图字段")
    return {"charts": charts}
