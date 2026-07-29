"""Z-score 异常检测 Tool。"""
from __future__ import annotations
from typing import Any
import pandas as pd
from scipy.stats import zscore
from langchain_core.tools import tool
from .common import read_dataframe
from .trend import FREQUENCIES


@tool
def detect_zscore_anomalies(file_path: str, value_column: str, date_column: str | None = None,
                            threshold: float = 3.0, frequency: str = "month") -> dict[str, Any]:
    """对原始记录或按时间聚合值执行 Z-score 异常检测，默认 |z|>3。"""
    if threshold <= 0:
        raise ValueError("threshold 必须大于 0")
    df = read_dataframe(file_path)
    if value_column not in df:
        raise ValueError(f"字段不存在：{value_column}")
    values = pd.to_numeric(df[value_column], errors="coerce")
    if date_column:
        if date_column not in df or frequency not in FREQUENCIES:
            raise ValueError("日期字段不存在或 frequency 不合法")
        dates = pd.to_datetime(df[date_column], errors="coerce")
        series = pd.DataFrame({"date": dates, "value": values}).dropna().set_index("date")["value"]
        series = series.resample(FREQUENCIES[frequency]).sum()
        labels = [i.strftime("%Y-%m-%d") for i in series.index]
    else:
        series = values.dropna()
        labels = [str(i) for i in series.index]
    if len(series) < 3 or float(series.std(ddof=0)) == 0:
        raise ValueError("有效样本不足或标准差为 0，无法检测异常")
    scores = zscore(series.to_numpy(dtype=float), ddof=0)
    anomalies = [{"label": label, "value": round(float(value), 2), "z_score": round(float(score), 4),
                  "direction": "高异常" if score > 0 else "低异常"}
                 for label, value, score in zip(labels, series, scores) if abs(float(score)) > threshold]
    return {"method": "Z-score", "threshold": threshold, "sample_size": int(len(series)),
            "anomaly_count": len(anomalies), "anomalies": anomalies}
