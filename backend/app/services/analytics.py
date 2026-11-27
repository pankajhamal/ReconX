"""Summary numbers for the dashboard, calculated from one batch's results."""


def amount_at_risk(result):
    """How much money (in paisa) a discrepancy puts in question.

    - Only the amount differs: the difference.
    - Anything else (missing record, wrong status, duplicate...): the full amount.
    """
    if result.category in ("MATCHED", "PENDING"):
        return 0
    if result.category == "AMOUNT_MISMATCH":
        return abs(result.amount_difference)
    return result.internal_amount or result.provider_amount


def summarize(batch):
    """Build the summary for one batch."""
    results = batch.results
    discrepancies = [r for r in results if r.category not in ("MATCHED", "PENDING")]

    # Count each flag separately: "AMOUNT_MISMATCH;STATUS_MISMATCH" counts once
    # for each, so the category totals can add up to more than the discrepancies.
    by_category = {}
    for result in discrepancies:
        for flag in result.category.split(";"):
            entry = by_category.setdefault(flag, {"count": 0, "amount_at_risk": 0})
            entry["count"] += 1
            entry["amount_at_risk"] += amount_at_risk(result)

    by_payment_outcome = {}
    for result in results:
        outcome = result.payment_outcome
        by_payment_outcome[outcome] = by_payment_outcome.get(outcome, 0) + 1

    by_date = {}
    for result in results:
        if result.transaction_date is None:
            continue
        day = result.transaction_date.date().isoformat()
        entry = by_date.setdefault(day, {"count": 0, "amount": 0})
        entry["count"] += 1
        entry["amount"] += result.internal_amount or result.provider_amount

    return {
        "batch_id": batch.id,
        "created_at": batch.created_at,
        "internal_transactions": batch.internal_count,
        "provider_transactions": batch.provider_count,
        "matched": sum(1 for r in results if r.category == "MATCHED"),
        "pending": sum(1 for r in results if r.category == "PENDING"),
        "discrepancies": len(discrepancies),
        "failed_payments": by_payment_outcome.get("FAILED", 0),
        "total_amount_at_risk": sum(amount_at_risk(r) for r in discrepancies),
        "by_category": by_category,
        "by_payment_outcome": by_payment_outcome,
        "by_date": dict(sorted(by_date.items())),
    }
