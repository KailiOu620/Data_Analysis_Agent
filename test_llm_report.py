"""调用阿里云 Qwen 生成带图表解读的 Word 报告。"""
from pathlib import Path
from docx import Document
from backend.tools import generate_word_report
from test_day3_pipeline import make_sample


def main() -> None:
    output_dir = Path("tests") / "day3_llm_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = make_sample(output_dir / "day3_llm_sample.csv")
    report_path = output_dir / "day3_business_report_with_ai.docx"
    result = generate_word_report.invoke({
        "file_path": str(data_path),
        "output_path": str(report_path),
        "company_name": "Day 3 AI Test Company",
        "date_column": "Order Date",
        "sales_column": "Sales",
        "profit_column": "Profit",
        "quantity_column": "Quantity",
        "order_id_column": "Order ID",
        "group_column": "Region",
        "advertising_column": "Advertising",
        "use_llm_interpretation": True,
    })
    if result["llm_interpretation_errors"]:
        raise RuntimeError("AI 解读存在失败：" + " | ".join(result["llm_interpretation_errors"]))
    document = Document(report_path)
    ai_paragraphs = [p.text for p in document.paragraphs if p.text.startswith("AI 解读：")]
    assert len(ai_paragraphs) >= 5, f"AI 解读数量不足：{len(ai_paragraphs)}"
    assert all(len(text) >= 80 for text in ai_paragraphs), "存在过短的 AI 解读"
    print("LLM REPORT TEST PASSED")
    print(f"AI interpretations: {len(ai_paragraphs)}")
    print(f"Report: {report_path.resolve()}")


if __name__ == "__main__":
    main()
