"""Request and response contracts exposed by the web API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    upload_id: str
    company_name: str = Field(default="示例企业", min_length=1, max_length=80)
    sales_column: str
    date_column: str | None = None
    profit_column: str | None = None
    quantity_column: str | None = None
    order_id_column: str | None = None
    group_column: str | None = None
    advertising_column: str | None = None
    use_llm_interpretation: bool = True


class AnalysisResponse(BaseModel):
    job_id: str
    summary_title: str = "总结分析"
    summary: str
    word_output_label: str = "Word文件输出如下"
    report_filename: str
    download_url: str
    llm_interpretation_count: int
    warnings: list[str] = Field(default_factory=list)
