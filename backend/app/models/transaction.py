"""Tables for the imported transactions."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InternalTransaction(Base):
    """A transaction from our own payment system."""

    __tablename__ = "internal_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(50), unique=True)
    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    amount: Mapped[int] = mapped_column(BigInteger)  # in paisa
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(20))
    payment_method: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProviderTransaction(Base):
    """A transaction from the external payment provider's report.

    The reference is not unique here: the provider may report the same
    payment twice, and the reconciliation engine must be able to see that.
    """

    __tablename__ = "provider_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(50), unique=True)
    reference: Mapped[str] = mapped_column(String(50), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)  # in paisa
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(20))
    processed_at: Mapped[datetime] = mapped_column(DateTime)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
