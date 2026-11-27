"""
CSV ingestion: read an uploaded CSV, validate every row, and save it.

A file is accepted only if every row is valid. Otherwise nothing is saved
and the list of errors is returned, so the user can fix the file.
"""

import csv
import io
from datetime import datetime

from sqlalchemy import select

from app.models import InternalTransaction, ProviderTransaction

INTERNAL_COLUMNS = ["transaction_id", "reference", "amount", "currency",
                    "status", "payment_method", "created_at"]
PROVIDER_COLUMNS = ["provider_id", "reference", "amount", "currency",
                    "status", "processed_at"]
STATUSES = {"SUCCESS", "FAILED", "PENDING"}


def parse_internal_csv(text):
    """Validate an internal transactions CSV. Returns (rows, errors)."""
    return parse_csv(text, INTERNAL_COLUMNS, "transaction_id", "created_at",
                     unique_reference=True)


def parse_provider_csv(text):
    """Validate a provider transactions CSV. Returns (rows, errors).

    References may repeat here: duplicates are found by reconciliation.
    """
    return parse_csv(text, PROVIDER_COLUMNS, "provider_id", "processed_at",
                     unique_reference=False)


def parse_csv(text, columns, id_column, date_column, unique_reference):
    """Read CSV text and check each row. Returns (rows, errors)."""
    reader = csv.DictReader(io.StringIO(text))

    missing = [column for column in columns if column not in (reader.fieldnames or [])]
    if missing:
        return [], [f"Missing columns: {', '.join(missing)}"]

    rows = []
    errors = []
    seen_ids = set()
    seen_references = set()

    # Line 1 is the header, so data starts on line 2.
    for line, raw in enumerate(reader, start=2):
        row = {column: (raw[column] or "").strip() for column in columns}
        row_errors = validate_row(row, columns, date_column)

        if row[id_column] in seen_ids:
            row_errors.append(f"duplicate {id_column} '{row[id_column]}'")
        if unique_reference and row["reference"] in seen_references:
            row_errors.append(f"duplicate reference '{row['reference']}'")
        seen_ids.add(row[id_column])
        seen_references.add(row["reference"])

        if row_errors:
            errors.append(f"Line {line}: " + "; ".join(row_errors))
        else:
            row["amount"] = int(row["amount"])
            row[date_column] = datetime.fromisoformat(row[date_column])
            rows.append(row)

    if not rows and not errors:
        errors.append("The file has no data rows")

    return rows, errors


def validate_row(row, columns, date_column):
    """Return a list of problems with one row (empty if it is valid)."""
    errors = [f"{column} is empty" for column in columns if not row[column]]
    if errors:
        return errors

    if not row["amount"].isdigit() or int(row["amount"]) <= 0:
        errors.append(f"amount '{row['amount']}' must be a positive whole number of paisa")
    if len(row["currency"]) != 3 or not row["currency"].isupper():
        errors.append(f"currency '{row['currency']}' must be a 3-letter code like NPR")
    if row["status"] not in STATUSES:
        errors.append(f"status '{row['status']}' must be one of {sorted(STATUSES)}")
    try:
        datetime.fromisoformat(row[date_column])
    except ValueError:
        errors.append(f"{date_column} '{row[date_column]}' must look like 2026-11-25 10:30:00")

    return errors


def save_internal(db, rows):
    """Save internal rows. Rows already in the database are skipped."""
    existing = set(db.scalars(select(InternalTransaction.transaction_id)))
    new_rows = [row for row in rows if row["transaction_id"] not in existing]
    db.add_all(InternalTransaction(**row) for row in new_rows)
    db.commit()
    return len(new_rows)


def save_provider(db, rows):
    """Save provider rows. Rows already in the database are skipped."""
    existing = set(db.scalars(select(ProviderTransaction.provider_id)))
    new_rows = [row for row in rows if row["provider_id"] not in existing]
    db.add_all(ProviderTransaction(**row) for row in new_rows)
    db.commit()
    return len(new_rows)
