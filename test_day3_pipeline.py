"""Day 3 离线端到端验收：统计、图表、异常和 Word 报告。"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from docx import Document
from backend.tools import (analyze_correlation, analyze_time_trend, calculate_business_kpis,
    descriptive_statistics, detect_zscore_anomalies, generate_business_charts, generate_word_report)


def make_sample(path: Path) -> Path:
    count = 60; advertising = np.arange(count, dtype=float) * 10 + 100
    sales = 1000 + advertising * 20; sales[30] += 30000
    frame = pd.DataFrame({"Order Date": pd.date_range("2021-01-01", periods=count, freq="MS"),
        "Order ID": [f"O{i:04d}" for i in range(count)], "Region": ["East","West","South"] * 20,
        "Sales": sales, "Profit": sales * .18, "Quantity": (np.arange(count) % 8) + 1,
        "Advertising": advertising})
    frame.to_csv(path, index=False, encoding="utf-8-sig"); return path


def run_pipeline(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True); data = make_sample(output_dir / "day3_sample.csv")
    desc = descriptive_statistics.invoke({"file_path":str(data), "columns":["Sales","Profit"]})
    kpi = calculate_business_kpis.invoke({"file_path":str(data), "sales_column":"Sales", "profit_column":"Profit",
        "quantity_column":"Quantity", "order_id_column":"Order ID"})
    trend = analyze_time_trend.invoke({"file_path":str(data), "date_column":"Order Date", "value_column":"Sales", "frequency":"month"})
    corr = analyze_correlation.invoke({"file_path":str(data), "x_column":"Advertising", "y_column":"Sales"})
    anomaly = detect_zscore_anomalies.invoke({"file_path":str(data), "value_column":"Sales", "date_column":"Order Date", "threshold":3.0})
    charts = generate_business_charts.invoke({"file_path":str(data), "output_dir":str(output_dir / "charts"),
        "date_column":"Order Date", "sales_column":"Sales", "group_column":"Region",
        "x_column":"Advertising", "y_column":"Sales"})
    report_path = output_dir / "day3_business_report.docx"
    report = generate_word_report.invoke({"file_path":str(data), "output_path":str(report_path), "company_name":"Day 3 Test Company",
        "date_column":"Order Date", "sales_column":"Sales", "profit_column":"Profit", "quantity_column":"Quantity",
        "order_id_column":"Order ID", "group_column":"Region", "advertising_column":"Advertising",
        "use_llm_interpretation":False})
    assert "Sales" in desc["statistics"]; assert kpi["total_sales"] > 0; assert len(trend["periods"]) == 60
    assert corr["pearson_r"] > 0.5; assert anomaly["anomaly_count"] >= 1; assert len(charts["charts"]) == 4
    assert report_path.exists() and report_path.stat().st_size > 20000
    doc = Document(report_path); assert len(doc.inline_shapes) >= 4
    assert any("管理建议" in p.text for p in doc.paragraphs)
    return {"report":report, "correlation":corr, "anomaly":anomaly, "charts":charts}


def test_day3_end_to_end(tmp_path: Path) -> None:
    run_pipeline(tmp_path)


if __name__ == "__main__":
    result = run_pipeline(Path("tests") / "day3_output")
    print("DAY 3 PIPELINE PASSED")
    print(f"Report: {result['report']['report_path']}")
    print(f"Pearson r: {result['correlation']['pearson_r']}")
    print(f"Anomalies: {result['anomaly']['anomaly_count']}")
