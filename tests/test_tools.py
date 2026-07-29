"""Day 1 工具的最小可运行测试。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.tools import analyze_sales, check_data_quality, load_dataset


def _make_sample_file(tmp_path: Path) -> Path:
    data = pd.DataFrame(
        {
            "Order_ID": ["A001", "A002", "A003", "A003", "A005"],
            "Region": ["华东", "华南", "华东", "华东", "华北"],
            "Sales": [100.0, 200.0, 300.0, 300.0, 5000.0],
            "Profit": [20.0, 30.0, -10.0, -10.0, None],
        }
    )
    file_path = tmp_path / "sample_sales.csv"
    data.to_csv(file_path, index=False, encoding="utf-8-sig")
    return file_path


def test_load_dataset(tmp_path: Path) -> None:
    file_path = _make_sample_file(tmp_path)
    result = load_dataset.invoke({"file_path": str(file_path), "preview_rows": 2})
    assert result["row_count"] == 5
    assert result["columns"] == ["Order_ID", "Region", "Sales", "Profit"]
    assert len(result["preview"]) == 2


def test_check_data_quality(tmp_path: Path) -> None:
    file_path = _make_sample_file(tmp_path)
    result = check_data_quality.invoke({"file_path": str(file_path)})
    assert result["duplicate_rows"] == 1
    assert result["columns"]["Profit"]["missing_count"] == 1
    assert result["numeric_outliers_iqr"]["Sales"]["count"] == 1


def test_analyze_sales(tmp_path: Path) -> None:
    file_path = _make_sample_file(tmp_path)
    result = analyze_sales.invoke(
        {
            "file_path": str(file_path),
            "sales_column": "Sales",
            "profit_column": "Profit",
            "group_column": "Region",
            "top_n": 2,
        }
    )
    assert result["total_sales"] == 5900.0
    assert result["profit"]["total_profit"] == 30.0
    assert result["top_groups_by_sales"][0] == {"group": "华北", "sales": 5000.0}
