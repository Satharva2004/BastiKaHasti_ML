"""HTTP routes for CSV cleaning and download."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.cleaning_service import build_frontend_summary, run_cleaning_pipeline
from app.schemas.api import CleaningApiResponse


router = APIRouter(prefix="/api/v1", tags=["cleaning"])

BASE_STORAGE_DIR = Path("storage")
UPLOAD_DIR = BASE_STORAGE_DIR / "uploads"
CLEANED_DIR = BASE_STORAGE_DIR / "cleaned"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/clean-csv", response_model=CleaningApiResponse)
async def clean_csv(file: UploadFile = File(...)) -> CleaningApiResponse:
    """Accept a CSV upload, clean it, and return frontend-friendly metadata."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported.")

    file_id = uuid4().hex
    uploaded_path = UPLOAD_DIR / f"{file_id}_{Path(file.filename).name}"
    cleaned_name = f"{uploaded_path.stem}_cleaned.csv"
    cleaned_path = CLEANED_DIR / cleaned_name

    uploaded_path.write_bytes(await file.read())

    result = run_cleaning_pipeline(str(uploaded_path), str(cleaned_path))
    frontend_summary = build_frontend_summary(result["dataframe"])

    return CleaningApiResponse(
        file_id=file_id,
        filename=file.filename,
        cleaned_filename=cleaned_name,
        download_url=f"/api/v1/clean-csv/{file_id}/download",
        row_count=frontend_summary["row_count"],
        column_count=frontend_summary["column_count"],
        columns=frontend_summary["columns"],
        quality_metrics=frontend_summary["quality_metrics"],
        distributions=frontend_summary["distributions"],
        timestamp_range=frontend_summary["timestamp_range"],
        preview=frontend_summary["preview"],
    )


@router.get("/clean-csv/{file_id}/download")
async def download_cleaned_csv(file_id: str) -> FileResponse:
    """Download the cleaned CSV generated for a previous upload."""
    matched_files = list(CLEANED_DIR.glob(f"{file_id}_*_cleaned.csv"))
    if not matched_files:
        raise HTTPException(status_code=404, detail="Cleaned CSV not found.")

    cleaned_path = matched_files[0]
    return FileResponse(
        path=cleaned_path,
        media_type="text/csv",
        filename=cleaned_path.name,
    )
