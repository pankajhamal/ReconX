from pathlib import Path

from app.services.ingestion import parse_internal_csv, parse_provider_csv
from app.services.reconciliation import reconcile
from data.generator import main as generate

HEADER = "transaction_id,reference,amount,currency,status,payment_method,created_at\n"
VALID_ROW = "INT-1,TXN-1,500000,NPR,SUCCESS,WALLET,2026-11-25 10:30:00\n"


def test_valid_file():
    rows, errors = parse_internal_csv(HEADER + VALID_ROW)
    assert errors == []
    assert rows[0]["amount"] == 500000  # converted to a number
    assert rows[0]["created_at"].year == 2026  # converted to a datetime


def test_missing_column():
    rows, errors = parse_internal_csv("transaction_id,reference\nINT-1,TXN-1\n")
    assert rows == []
    assert "Missing columns" in errors[0]


def test_empty_file():
    rows, errors = parse_internal_csv(HEADER)
    assert errors == ["The file has no data rows"]


def test_invalid_values():
    bad_row = "INT-1,TXN-1,50.5,npr,DONE,WALLET,yesterday\n"
    rows, errors = parse_internal_csv(HEADER + bad_row)
    assert rows == []
    assert errors[0].startswith("Line 2:")
    for field in ["amount", "currency", "status", "created_at"]:
        assert field in errors[0]


def test_empty_value():
    rows, errors = parse_internal_csv(HEADER + "INT-1,TXN-1,500000,NPR,SUCCESS,,2026-11-25 10:30:00\n")
    assert errors == ["Line 2: payment_method is empty"]


def test_duplicate_internal_reference_is_rejected():
    second = "INT-2,TXN-1,500000,NPR,SUCCESS,WALLET,2026-11-25 10:30:00\n"
    rows, errors = parse_internal_csv(HEADER + VALID_ROW + second)
    assert errors == ["Line 3: duplicate reference 'TXN-1'"]


def test_duplicate_provider_reference_is_allowed():
    header = "provider_id,reference,amount,currency,status,processed_at\n"
    first = "PRV-1,TXN-1,500000,NPR,SUCCESS,2026-11-25 10:30:05\n"
    second = "PRV-2,TXN-1,500000,NPR,SUCCESS,2026-11-25 10:30:05\n"
    rows, errors = parse_provider_csv(header + first + second)
    assert errors == []
    assert len(rows) == 2


def test_generated_files_are_valid():
    generate()
    folder = Path(__file__).parent.parent / "data" / "generated"

    internal, errors = parse_internal_csv((folder / "internal_transactions.csv").read_text())
    assert errors == []
    provider, errors = parse_provider_csv((folder / "provider_transactions.csv").read_text())
    assert errors == []

    assert len(internal) == 1000
    assert len(provider) == 1020
    assert len(reconcile(internal, provider)) == 1030
