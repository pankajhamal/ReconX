"""Shapes of the reconciliation API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    internal_count: int
    provider_count: int


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference: str
    internal_transaction_id: str | None
    provider_transaction_id: str | None
    internal_amount: int | None
    provider_amount: int | None
    amount_difference: int | None
    internal_status: str | None
    provider_status: str | None
    transaction_date: datetime | None
    category: str
    payment_outcome: str
