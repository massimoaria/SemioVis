"""POST /api/report — Report generation."""

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.report_generator import generate_report

router = APIRouter()


class ReportRequest(BaseModel):
    image_id: str
    analysis_results: dict
    format: str = "pdf"


@router.post("/report")
async def create_report(req: ReportRequest):
    """Generate a PDF/DOCX/HTML report from analysis results."""
    output_path = await generate_report(
        image_id=req.image_id,
        results=req.analysis_results,
        format=req.format,
    )

    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "html": "text/html",
    }

    return FileResponse(
        path=str(output_path),
        media_type=media_types.get(req.format, "application/octet-stream"),
        filename=output_path.name,
    )
