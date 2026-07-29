"""FastAPI entry point for upload, analysis and DOCX download."""
from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.api.schemas import AnalysisRequest, AnalysisResponse
from backend.services.analysis_service import AnalysisService

app = FastAPI(title="企业经营数据分析 Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8501", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
service = AnalysisService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/files/inspect")
async def inspect_file(file: UploadFile = File(...)) -> dict:
    try:
        return service.save_upload(file.filename or "upload", await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"无法读取数据文件：{exc}") from exc


@app.post("/api/v1/analysis", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    try:
        return AnalysisResponse(**service.generate_report(request))
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"报告生成失败：{type(exc).__name__}: {exc}") from exc


@app.get("/api/v1/reports/{job_id}/download")
def download_report(job_id: str) -> FileResponse:
    try:
        report = service.find_report(job_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(
        path=report,
        filename="business_analysis_report.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
