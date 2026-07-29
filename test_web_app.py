"""End-to-end test for upload -> analysis -> DOCX download."""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
from docx import Document
from docx.oxml.ns import qn
from fastapi.testclient import TestClient

from backend.api.main import app


def sample_csv() -> bytes:
    dates = pd.date_range("2024-01-01", periods=36, freq="MS")
    frame = pd.DataFrame({
        "Order Date": dates,
        "Order ID": [f"ORD-{index:03d}" for index in range(36)],
        "Region": ["华东", "华南", "华北"] * 12,
        "Sales": [1000 + index * 35 + (index % 4) * 80 for index in range(36)],
        "Profit": [160 + index * 6 for index in range(36)],
        "Quantity": [2 + index % 5 for index in range(36)],
        "Advertising": [100 + index * 8 for index in range(36)],
    })
    return frame.to_csv(index=False).encode("utf-8-sig")


def test_upload_analyze_and_download() -> None:
    client = TestClient(app)
    upload = client.post(
        "/api/v1/files/inspect",
        files={"file": ("sample.csv", io.BytesIO(sample_csv()), "text/csv")},
    )
    assert upload.status_code == 200, upload.text
    info = upload.json()
    assert info["row_count"] == 36
    assert "Sales" in info["columns"]

    analysis = client.post("/api/v1/analysis", json={
        "upload_id": info["upload_id"],
        "company_name": "接口测试企业",
        "sales_column": "Sales",
        "date_column": "Order Date",
        "profit_column": "Profit",
        "quantity_column": "Quantity",
        "order_id_column": "Order ID",
        "group_column": "Region",
        "advertising_column": "Advertising",
        "use_llm_interpretation": False,
    })
    assert analysis.status_code == 200, analysis.text
    result = analysis.json()
    assert result["summary_title"] == "总结分析"
    assert result["word_output_label"] == "Word文件输出如下"
    assert result["summary"]

    download = client.get(result["download_url"])
    assert download.status_code == 200
    assert len(download.content) > 10_000
    assert download.content[:2] == b"PK"

    document = Document(io.BytesIO(download.content))
    normal = document.styles["Normal"]
    assert normal.font.size.pt == 12
    assert normal._element.rPr.rFonts.get(qn("w:eastAsia")) == "宋体"
    body_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "企业经营数据分析报告" in body_text
    assert "执行摘要" in body_text
    print("PASS: 上传、分析、Word 下载均成功；正文样式为宋体小四（12pt）。")


if __name__ == "__main__":
    test_upload_analyze_and_download()
