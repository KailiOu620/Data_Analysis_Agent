"""Upload storage, field inspection and report-generation orchestration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pandas as pd

from backend.api.schemas import AnalysisRequest
from backend.tools.common import read_dataframe
from backend.tools.report import generate_word_report

ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


class AnalysisService:
    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.upload_dir = self.project_root / "data" / "uploads"
        self.report_dir = self.project_root / "outputs" / "reports"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_uuid(value: str, label: str) -> str:
        try:
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError(f"{label} 格式无效。") from exc

    def save_upload(self, filename: str, content: bytes) -> dict[str, Any]:
        suffix = Path(filename or "").suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise ValueError("仅支持 CSV、XLSX 和 XLS 文件。")
        if not content:
            raise ValueError("上传文件为空。")
        if len(content) > MAX_UPLOAD_BYTES:
            raise ValueError("文件不能超过 25 MB。")

        upload_id = str(uuid4())
        target = self.upload_dir / f"{upload_id}{suffix}"
        target.write_bytes(content)
        try:
            frame = read_dataframe(str(target))
        except Exception:
            target.unlink(missing_ok=True)
            raise

        preview = frame.head(5).where(pd.notna(frame.head(5)), None)
        return {
            "upload_id": upload_id,
            "filename": Path(filename).name,
            "row_count": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "columns": [str(column) for column in frame.columns],
            "dtypes": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
            "preview": json.loads(preview.to_json(orient="records", force_ascii=False, date_format="iso")),
        }

    def find_upload(self, upload_id: str) -> Path:
        safe_id = self._validate_uuid(upload_id, "upload_id")
        matches = [path for path in self.upload_dir.glob(f"{safe_id}.*") if path.suffix.lower() in ALLOWED_SUFFIXES]
        if len(matches) != 1:
            raise FileNotFoundError("找不到上传文件，请重新上传。")
        return matches[0]

    def generate_report(self, request: AnalysisRequest) -> dict[str, Any]:
        source = self.find_upload(request.upload_id)
        frame = read_dataframe(str(source))
        available = {str(column) for column in frame.columns}
        mappings = request.model_dump(exclude={"upload_id", "company_name", "use_llm_interpretation"})
        invalid = [value for value in mappings.values() if value and value not in available]
        if invalid:
            raise ValueError(f"字段不存在：{', '.join(invalid)}")
        numeric_mappings = {
            "销售额": request.sales_column,
            "利润": request.profit_column,
            "数量": request.quantity_column,
            "广告投入": request.advertising_column,
        }
        for label, column in numeric_mappings.items():
            if not column:
                continue
            valid_count = int(pd.to_numeric(frame[column], errors="coerce").notna().sum())
            if valid_count == 0:
                raise ValueError(
                    f"{label}字段“{column}”没有可识别的数值，请检查字段映射或原始数据格式。"
                )

        job_id = str(uuid4())
        target_dir = self.report_dir / job_id
        target_dir.mkdir(parents=True, exist_ok=True)
        report_path = target_dir / "business_analysis_report.docx"
        result = generate_word_report.invoke({
            "file_path": str(source),
            "output_path": str(report_path),
            "company_name": request.company_name,
            **mappings,
            "use_llm_interpretation": request.use_llm_interpretation,
        })
        return {
            "job_id": job_id,
            "summary": result["summary"],
            "report_filename": report_path.name,
            "download_url": f"/api/v1/reports/{job_id}/download",
            "llm_interpretation_count": result["llm_interpretation_count"],
            "warnings": result["llm_interpretation_errors"],
        }

    def find_report(self, job_id: str) -> Path:
        safe_id = self._validate_uuid(job_id, "job_id")
        path = self.report_dir / safe_id / "business_analysis_report.docx"
        if not path.is_file():
            raise FileNotFoundError("报告不存在或尚未生成完成。")
        return path
