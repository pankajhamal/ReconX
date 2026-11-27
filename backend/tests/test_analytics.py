from datetime import datetime

from app.models import ReconciliationBatch, ReconciliationResult
from app.services.analytics import amount_at_risk, summarize


def result(category, outcome, internal=None, provider=None):
    difference = provider - internal if internal and provider else None
    return ReconciliationResult(category=category, payment_outcome=outcome,
                                internal_amount=internal, provider_amount=provider,
                                amount_difference=difference,
                                transaction_date=datetime(2026, 11, 25, 10, 0))


def test_amount_at_risk():
    assert amount_at_risk(result("MATCHED", "SUCCESS", 500000, 500000)) == 0
    assert amount_at_risk(result("AMOUNT_MISMATCH", "NEEDS_INVESTIGATION", 500000, 450000)) == 50000
    assert amount_at_risk(result("STATUS_MISMATCH", "NEEDS_INVESTIGATION", 500000, 500000)) == 500000
    assert amount_at_risk(result("MISSING_INTERNAL", "NEEDS_INVESTIGATION", None, 300000)) == 300000


def test_summarize():
    batch = ReconciliationBatch(id=1, internal_count=4, provider_count=4)
    batch.results = [
        result("MATCHED", "SUCCESS", 500000, 500000),
        result("MATCHED", "FAILED", 200000, 200000),
        result("PENDING", "PENDING", 100000, 100000),
        result("AMOUNT_MISMATCH;STATUS_MISMATCH", "NEEDS_INVESTIGATION", 500000, 450000),
    ]

    summary = summarize(batch)

    assert summary["matched"] == 2
    assert summary["pending"] == 1
    assert summary["discrepancies"] == 1
    assert summary["failed_payments"] == 1
    # The two-flag result counts once in each category.
    assert summary["by_category"]["AMOUNT_MISMATCH"]["count"] == 1
    assert summary["by_category"]["STATUS_MISMATCH"]["count"] == 1
    assert summary["by_date"]["2026-11-25"]["count"] == 4
