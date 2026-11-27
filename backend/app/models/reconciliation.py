"""Tables for reconciliation runs and their results."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReconciliationBatch(Base):
    """One run of the reconciliation engine. Old batches are kept for auditing."""

    __tablename__ = "reconciliation_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    internal_count: Mapped[int]  # internal rows compared in this run
    provider_count: Mapped[int]  # provider rows compared (duplicates included)

    results: Mapped[list["ReconciliationResult"]] = relationship(back_populates="batch")


class ReconciliationResult(Base):
    """The outcome for one reference in one batch.

    Amounts and statuses are copied from the original records, so a batch
    still shows what was compared even if new data is imported later.
    """

    __tablename__ = "reconciliation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("reconciliation_batches.id"), index=True)
    reference: Mapped[str] = mapped_column(String(50), index=True)

    # Links to the original records (empty when a record is missing).
    internal_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("internal_transactions.transaction_id"))
    provider_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("provider_transactions.provider_id"))

    internal_amount: Mapped[int | None] = mapped_column(BigInteger)
    provider_amount: Mapped[int | None] = mapped_column(BigInteger)
    amount_difference: Mapped[int | None] = mapped_column(BigInteger)
    internal_status: Mapped[str | None] = mapped_column(String(20))
    provider_status: Mapped[str | None] = mapped_column(String(20))
    transaction_date: Mapped[datetime | None] = mapped_column(DateTime)

    # e.g. "MATCHED", "PENDING" or "AMOUNT_MISMATCH;STATUS_MISMATCH"
    category: Mapped[str] = mapped_column(String(100), index=True)
    payment_outcome: Mapped[str] = mapped_column(String(30), index=True)

    batch: Mapped[ReconciliationBatch] = relationship(back_populates="results")
