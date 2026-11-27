"""Endpoints for uploading the two transaction CSV files."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import ingestion

router = APIRouter(prefix="/uploads", tags=["uploads"])


async def read_text(file):
    """Read the uploaded file as text."""
    try:
        return (await file.read()).decode("utf-8-sig")  # -sig drops an Excel BOM
    except UnicodeDecodeError:
        raise HTTPException(400, {"errors": ["File must be a UTF-8 encoded CSV"]})


def save(db, rows, errors, save_function):
    """Reject the file if it has errors, otherwise replace the stored data with it."""
    if errors:
        raise HTTPException(400, {"errors": errors})
    save_function(db, rows)
    return {"rows_saved": len(rows)}


@router.post("/internal")
async def upload_internal(file: UploadFile, db: Session = Depends(get_db)):
    rows, errors = ingestion.parse_internal_csv(await read_text(file))
    return save(db, rows, errors, ingestion.save_internal)


@router.post("/provider")
async def upload_provider(file: UploadFile, db: Session = Depends(get_db)):
    rows, errors = ingestion.parse_provider_csv(await read_text(file))
    return save(db, rows, errors, ingestion.save_provider)
