"""HTTP routes for CSV cleaning, scoring, and artifact download."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.cleaning_service import build_frontend_summary, run_cleaning_pipeline
from app.model.train_model import train
from app.schemas.api import CleaningApiResponse, PredictApiResponse


router = APIRouter(prefix="/api/v1", tags=["cleaning"])

BASE_STORAGE_DIR = Path("storage")
UPLOAD_DIR = BASE_STORAGE_DIR / "uploads"
CLEANED_DIR = BASE_STORAGE_DIR / "cleaned"
PREDICTIONS_DIR = BASE_STORAGE_DIR / "predictions"
REPORTS_DIR = BASE_STORAGE_DIR / "reports"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_DIR.mkdir(parents=True, exist_ok=True)
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _build_dataset_summary(dataframe: pd.DataFrame) -> dict[str, object]:
    """Create frontend-friendly dataset summary metrics."""
    numeric_columns = dataframe.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_columns = [column for column in dataframe.columns if column not in numeric_columns]
    clean_amount = pd.to_numeric(dataframe.get("clean_amount"), errors="coerce")

    return {
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "duplicate_row_count": int(dataframe.duplicated().sum()),
        "missing_value_count": int(dataframe.isna().sum().sum()),
        "missing_by_column": {column: int(count) for column, count in dataframe.isna().sum().items() if int(count) > 0},
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "top_cities": dataframe["canonical_city"].value_counts().head(10).to_dict() if "canonical_city" in dataframe.columns else {},
        "top_merchant_cities": dataframe["merchant_canonical_city"].value_counts().head(10).to_dict() if "merchant_canonical_city" in dataframe.columns else {},
        "top_device_types": dataframe["device_type"].value_counts().head(10).to_dict() if "device_type" in dataframe.columns else {},
        "amount_summary": {
            "min": float(clean_amount.min()) if clean_amount.notna().any() else 0.0,
            "max": float(clean_amount.max()) if clean_amount.notna().any() else 0.0,
            "mean": float(clean_amount.mean()) if clean_amount.notna().any() else 0.0,
            "median": float(clean_amount.median()) if clean_amount.notna().any() else 0.0,
            "p95": float(clean_amount.quantile(0.95)) if clean_amount.notna().any() else 0.0,
            "p99": float(clean_amount.quantile(0.99)) if clean_amount.notna().any() else 0.0,
        },
    }


def _build_pattern_summary(dataframe: pd.DataFrame) -> dict[str, int]:
    """Summarize active fraud-pattern columns."""
    pattern_columns = [column for column in dataframe.columns if column.startswith("pattern_")]
    return {column: int(pd.to_numeric(dataframe[column], errors="coerce").fillna(0).sum()) for column in pattern_columns}


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
        cleaning_actions=frontend_summary["cleaning_actions"],
        distributions=frontend_summary["distributions"],
        timestamp_range=frontend_summary["timestamp_range"],
        preview=frontend_summary["preview"],
    )


@router.post("/predict-csv", response_model=PredictApiResponse)
async def predict_csv(file: UploadFile = File(...)) -> PredictApiResponse:
    """Accept a CSV upload, clean it, train/score models, and return artifact links."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported.")

    file_id = uuid4().hex
    uploaded_path = UPLOAD_DIR / f"{file_id}_{Path(file.filename).name}"
    uploaded_path.write_bytes(await file.read())

    training_result = train(str(uploaded_path), artifact_prefix=file_id)
    cleaned_path = Path(training_result["cleaned_csv_path"])
    cleaned_dataframe = pd.read_csv(cleaned_path, low_memory=False)
    frontend_summary = build_frontend_summary(cleaned_dataframe)
    dataset_summary = _build_dataset_summary(cleaned_dataframe)
    pattern_summary = _build_pattern_summary(cleaned_dataframe)

    models = []
    for model_result in training_result["models"]:
        model_name = model_result["model_name"]
        models.append(
            {
                **model_result,
                "predictions_download_url": f"/api/v1/predict-csv/{file_id}/download/{model_name}/predictions",
                "threshold_report_download_url": f"/api/v1/predict-csv/{file_id}/download/{model_name}/thresholds",
            }
        )

    return PredictApiResponse(
        file_id=file_id,
        filename=file.filename,
        cleaned_filename=cleaned_path.name,
        cleaned_download_url=f"/api/v1/predict-csv/{file_id}/download/cleaned",
        dataset_summary=dataset_summary,
        row_count=frontend_summary["row_count"],
        column_count=frontend_summary["column_count"],
        columns=frontend_summary["columns"],
        target_column=training_result["target_column"],
        label_mode=training_result["label_mode"],
        timing=training_result["timing"],
        quality_metrics=frontend_summary["quality_metrics"],
        cleaning_actions=frontend_summary["cleaning_actions"],
        distributions=frontend_summary["distributions"],
        pattern_summary=pattern_summary,
        top_risky_transactions=models[1]["top_risky_transactions"] if len(models) > 1 else models[0]["top_risky_transactions"],
        timestamp_range=frontend_summary["timestamp_range"],
        preview=frontend_summary["preview"],
        models=models,
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


@router.get("/predict-csv/{file_id}/download/cleaned")
async def download_scored_cleaned_csv(file_id: str) -> FileResponse:
    """Download the cleaned CSV generated for a scored upload."""
    matched_files = list(CLEANED_DIR.glob(f"{file_id}_cleaned_*.csv"))
    if not matched_files:
        raise HTTPException(status_code=404, detail="Cleaned CSV not found.")

    cleaned_path = matched_files[0]
    return FileResponse(path=cleaned_path, media_type="text/csv", filename=cleaned_path.name)


@router.get("/predict-csv/{file_id}/download/{model_name}/predictions")
async def download_predictions_csv(file_id: str, model_name: str) -> FileResponse:
    """Download model predictions for a scored upload."""
    predictions_path = PREDICTIONS_DIR / f"{file_id}_{model_name}_predictions.csv"
    if not predictions_path.exists():
        raise HTTPException(status_code=404, detail="Predictions CSV not found.")

    return FileResponse(path=predictions_path, media_type="text/csv", filename=predictions_path.name)


@router.get("/predict-csv/{file_id}/download/{model_name}/thresholds")
async def download_threshold_report(file_id: str, model_name: str) -> FileResponse:
    """Download threshold report for a scored upload."""
    report_path = REPORTS_DIR / f"{file_id}_{model_name}_thresholds.csv"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Threshold report not found.")

    return FileResponse(path=report_path, media_type="text/csv", filename=report_path.name)
