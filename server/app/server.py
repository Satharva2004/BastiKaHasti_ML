"""FastAPI application for transactional CSV cleaning."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as cleaning_router


app = FastAPI(
    title="Fraud Data Cleaning API",
    version="1.0.0",
    description="Upload transactional CSV files, normalize them, and download model-ready cleaned data.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://basti-ka-hasti-ml-t9kk.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.head("/health")
async def health_check() -> dict[str, str]:
    """Simple health endpoint for hosting and monitoring."""
    return {"status": "ok"}


app.include_router(cleaning_router)
