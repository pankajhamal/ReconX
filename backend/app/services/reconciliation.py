"""
Reconciliation engine.

Compares internal transactions with provider transactions, matched on
`reference`, and returns one result per reference.

Each input row is a dict with at least:
    internal: transaction_id, reference, amount, currency, status
    provider: provider_id,    reference, amount, currency, status
Amounts are integers in paisa. Internal references are expected to be
unique (ingestion checks this before reconciliation runs).
"""

from sqlalchemy import select

from app.models import (InternalTransaction, ProviderTransaction,
                        ReconciliationBatch, ReconciliationResult)

# Reconciliation categories
MATCHED = "MATCHED"
PENDING = "PENDING"
AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
STATUS_MISMATCH = "STATUS_MISMATCH"
CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
MISSING_PROVIDER = "MISSING_PROVIDER"
MISSING_INTERNAL = "MISSING_INTERNAL"
DUPLICATE = "DUPLICATE"

# Payment outcome when the two systems disagree
NEEDS_INVESTIGATION = "NEEDS_INVESTIGATION"


def reconcile(internal_rows, provider_rows):
    """Reconcile two lists of transactions and return a list of results."""
    # Group provider rows by reference, so duplicates end up in one list.
    provider_by_reference = {}
    for row in provider_rows:
        provider_by_reference.setdefault(row["reference"], []).append(row)

    results = []

    # Every internal transaction gets a result.
    internal_references = set()
    for internal in internal_rows:
        reference = internal["reference"]
        internal_references.add(reference)
        matches = provider_by_reference.get(reference, [])
        results.append(compare(internal, matches))

    # Provider transactions that our system never recorded.
    for reference, matches in provider_by_reference.items():
        if reference not in internal_references:
            results.append(compare(None, matches))

    return results


def compare(internal, provider_matches):
    """Compare one internal record with its provider record(s)."""
    provider = provider_matches[0] if provider_matches else None
    flags = []

    if provider is None:
        flags.append(MISSING_PROVIDER)
    elif internal is None:
        flags.append(MISSING_INTERNAL)
    else:
        if len(provider_matches) > 1:
            flags.append(DUPLICATE)
        if internal["amount"] != provider["amount"]:
            flags.append(AMOUNT_MISMATCH)
        if internal["currency"] != provider["currency"]:
            flags.append(CURRENCY_MISMATCH)
        if internal["status"] != provider["status"]:
            flags.append(STATUS_MISMATCH)

    # Reconciliation status: what the two systems agree or disagree on.
    if flags:
        category = ";".join(flags)
        payment_outcome = NEEDS_INVESTIGATION
    elif internal["status"] == "PENDING":
        category = PENDING
        payment_outcome = "PENDING"
    else:
        category = MATCHED
        payment_outcome = internal["status"]  # SUCCESS or FAILED

    amount_difference = None
    if internal and provider:
        amount_difference = provider["amount"] - internal["amount"]

    # Use our own date when we have the record, otherwise the provider's.
    if internal:
        transaction_date = internal.get("created_at")
    else:
        transaction_date = provider.get("processed_at")

    return {
        "reference": (internal or provider)["reference"],
        "internal_id": internal["transaction_id"] if internal else None,
        "provider_id": provider["provider_id"] if provider else None,
        "internal_amount": internal["amount"] if internal else None,
        "provider_amount": provider["amount"] if provider else None,
        "internal_status": internal["status"] if internal else None,
        "provider_status": provider["status"] if provider else None,
        "flags": flags,
        "category": category,
        "payment_outcome": payment_outcome,
        "amount_difference": amount_difference,
        "transaction_date": transaction_date,
    }


def run_batch(db):
    """Reconcile every stored transaction and save the results as a new batch."""
    internal_rows = [
        {"transaction_id": t.transaction_id, "reference": t.reference, "amount": t.amount,
         "currency": t.currency, "status": t.status, "created_at": t.created_at}
        for t in db.scalars(select(InternalTransaction).order_by(InternalTransaction.id))
    ]
    provider_rows = [
        {"provider_id": t.provider_id, "reference": t.reference, "amount": t.amount,
         "currency": t.currency, "status": t.status, "processed_at": t.processed_at}
        for t in db.scalars(select(ProviderTransaction).order_by(ProviderTransaction.id))
    ]
    if not internal_rows and not provider_rows:
        return None  # nothing uploaded yet

    batch = ReconciliationBatch(internal_count=len(internal_rows),
                                provider_count=len(provider_rows))
    for result in reconcile(internal_rows, provider_rows):
        batch.results.append(ReconciliationResult(
            reference=result["reference"],
            internal_transaction_id=result["internal_id"],
            provider_transaction_id=result["provider_id"],
            internal_amount=result["internal_amount"],
            provider_amount=result["provider_amount"],
            amount_difference=result["amount_difference"],
            internal_status=result["internal_status"],
            provider_status=result["provider_status"],
            transaction_date=result["transaction_date"],
            category=result["category"],
            payment_outcome=result["payment_outcome"],
        ))

    db.add(batch)
    db.commit()
    return batch
