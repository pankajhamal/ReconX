from app.services.reconciliation import reconcile
from data.generator import build_records


def internal(reference="TXN-1", amount=500000, currency="NPR", status="SUCCESS"):
    return {"transaction_id": "INT-1", "reference": reference,
            "amount": amount, "currency": currency, "status": status}


def provider(reference="TXN-1", amount=500000, currency="NPR", status="SUCCESS"):
    return {"provider_id": "PRV-1", "reference": reference,
            "amount": amount, "currency": currency, "status": status}


def reconcile_one(internal_rows, provider_rows):
    """Reconcile and return the only result."""
    results = reconcile(internal_rows, provider_rows)
    assert len(results) == 1
    return results[0]


def test_matched_success():
    result = reconcile_one([internal()], [provider()])
    assert result["category"] == "MATCHED"
    assert result["payment_outcome"] == "SUCCESS"


def test_matched_failed_payment_is_still_failed():
    result = reconcile_one([internal(status="FAILED")], [provider(status="FAILED")])
    assert result["category"] == "MATCHED"
    assert result["payment_outcome"] == "FAILED"


def test_pending():
    result = reconcile_one([internal(status="PENDING")], [provider(status="PENDING")])
    assert result["category"] == "PENDING"
    assert result["payment_outcome"] == "PENDING"


def test_amount_mismatch():
    result = reconcile_one([internal()], [provider(amount=450000)])
    assert result["flags"] == ["AMOUNT_MISMATCH"]
    assert result["amount_difference"] == -50000
    assert result["payment_outcome"] == "NEEDS_INVESTIGATION"


def test_status_mismatch():
    result = reconcile_one([internal()], [provider(status="FAILED")])
    assert result["flags"] == ["STATUS_MISMATCH"]


def test_currency_mismatch():
    result = reconcile_one([internal()], [provider(currency="USD")])
    assert result["flags"] == ["CURRENCY_MISMATCH"]


def test_multiple_flags():
    result = reconcile_one([internal()], [provider(amount=450000, status="FAILED")])
    assert result["flags"] == ["AMOUNT_MISMATCH", "STATUS_MISMATCH"]
    assert result["category"] == "AMOUNT_MISMATCH;STATUS_MISMATCH"


def test_missing_provider():
    result = reconcile_one([internal()], [])
    assert result["flags"] == ["MISSING_PROVIDER"]
    assert result["provider_id"] is None


def test_missing_internal():
    result = reconcile_one([], [provider()])
    assert result["flags"] == ["MISSING_INTERNAL"]
    assert result["internal_id"] is None


def test_duplicate():
    result = reconcile_one([internal()], [provider(), provider()])
    assert result["flags"] == ["DUPLICATE"]


def test_generated_dataset_matches_ground_truth():
    internal_rows, provider_rows, truth = build_records()
    results = reconcile(internal_rows, provider_rows)

    expected = {row["reference"]: row["expected"] for row in truth}
    actual = {result["reference"]: result["category"] for result in results}
    assert actual == expected
