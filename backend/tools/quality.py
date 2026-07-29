"""数据质量检测 Tool。"""
from __future__ import annotations
from typing import Any
from langchain_core.tools import tool
from .common import read_dataframe


@tool
def check_data_quality(file_path: str) -> dict[str, Any]:
    """检查缺失值、重复行、字段类型和 IQR 数值异常。"""
    df = read_dataframe(file_path); rows = len(df); missing = df.isna().sum()
    columns = {str(c): {"dtype": str(df[c].dtype), "missing_count": int(missing[c]),
                        "missing_rate_percent": round(float(missing[c] / rows * 100), 2) if rows else 0.0,
                        "unique_count": int(df[c].nunique(dropna=True))} for c in df.columns}
    outliers: dict[str, Any] = {}
    for c in df.select_dtypes(include="number").columns:
        values = df[c].dropna()
        if values.empty: continue
        q1, q3 = values.quantile([.25, .75]); iqr = q3 - q1; lower = q1 - 1.5 * iqr; upper = q3 + 1.5 * iqr
        count = int(((values < lower) | (values > upper)).sum())
        if count:
            outliers[str(c)] = {"count": count, "rate_percent": round(count / len(values) * 100, 2),
                                "lower_bound": round(float(lower), 4), "upper_bound": round(float(upper), 4)}
    duplicates = int(df.duplicated().sum())
    return {"row_count": rows, "duplicate_rows": duplicates,
            "duplicate_rate_percent": round(duplicates / rows * 100, 2) if rows else 0.0,
            "columns": columns, "problem_columns": {c: v for c, v in columns.items() if v["missing_count"]},
            "numeric_outliers_iqr": outliers,
            "has_quality_issues": bool(duplicates or int(missing.sum()) or outliers)}
