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
    }
