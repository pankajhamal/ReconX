"""Endpoints for running reconciliation and reading its results."""

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ReconciliationBatch, ReconciliationResult
from app.schemas.reconciliation import BatchOut, ResultOut
from app.services.analytics import summarize
from app.services.reconciliation import run_batch

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])

REPORT_COLUMNS = list(ResultOut.model_fields)


def get_batch(db, batch_id):
    """Load a batch or answer 404."""
    batch = db.get(ReconciliationBatch, batch_id)
    if batch is None:
        raise HTTPException(404, f"Batch {batch_id} not found")
    return batch


@router.post("/run")
def run(db: Session = Depends(get_db)):
    """Reconcile all uploaded transactions and save the results as a new batch."""
    batch = run_batch(db)
    if batch is None:
        raise HTTPException(400, "No transactions uploaded yet")
    return summarize(batch)


@router.get("/batches", response_model=list[BatchOut])
def list_batches(db: Session = Depends(get_db)):
    """All reconciliation runs, newest first."""
    return db.scalars(select(ReconciliationBatch).order_by(ReconciliationBatch.id.desc())).all()


@router.get("/batches/{batch_id}/results", response_model=list[ResultOut])
def list_results(batch_id: int,
                 reference: str | None = None,
                 category: str | None = None,
                 payment_outcome: str | None = None,
                 transaction_date: date | None = None,
                 db: Session = Depends(get_db)):
    """Results of one batch. Every filter is optional."""
    get_batch(db, batch_id)
    query = select(ReconciliationResult).where(ReconciliationResult.batch_id == batch_id)

    if reference:
        query = query.where(ReconciliationResult.reference.icontains(reference))
    if category:
        # "AMOUNT_MISMATCH" also finds "AMOUNT_MISMATCH;STATUS_MISMATCH".
        query = query.where(ReconciliationResult.category.contains(category))
    if payment_outcome:
        query = query.where(ReconciliationResult.payment_outcome == payment_outcome)
    if transaction_date:
        query = query.where(func.date(ReconciliationResult.transaction_date) == transaction_date)

    return db.scalars(query.order_by(ReconciliationResult.reference)).all()


@router.get("/batches/{batch_id}/summary")
def get_summary(batch_id: int, db: Session = Depends(get_db)):
    """Totals and chart data for the dashboard."""
    return summarize(get_batch(db, batch_id))


@router.get("/batches/{batch_id}/report")
def download_report(batch_id: int, db: Session = Depends(get_db)):
    """Download all results of one batch as a CSV file."""
    batch = get_batch(db, batch_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(REPORT_COLUMNS)
    for result in sorted(batch.results, key=lambda r: r.reference):
        writer.writerow([getattr(result, column) for column in REPORT_COLUMNS])

    filename = f"reconciliation_batch_{batch_id}.csv"
    return Response(output.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})
