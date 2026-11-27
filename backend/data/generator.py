"""
Synthetic dataset generator for ReconX.

Creates fictional transactions for a made-up Nepal-based payment company:
  - internal_transactions.csv  (records from our own payment system)
  - provider_transactions.csv  (records from the external payment provider)
  - ground_truth.csv           (the expected reconciliation result per reference)

All amounts are stored in paisa (100 paisa = 1 NPR).

Run:  python data/generator.py
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "generated"
START_DATE = datetime(2026, 11, 20)
DAYS = 6
PAYMENT_METHODS = ["WALLET", "CARD", "BANK_TRANSFER"]

# How many internal transactions get each scenario (total = 1,000).
SCENARIOS = {
    "MATCHED": 700,
    "AMOUNT_MISMATCH": 100,
    "MISSING_PROVIDER": 50,
    "DUPLICATE": 40,
    "STATUS_MISMATCH": 40,
    "PENDING": 30,
    "CURRENCY_MISMATCH": 20,         # edge case
    "AMOUNT_AND_STATUS_MISMATCH": 20,  # edge case: two flags on one transaction
}

# Provider records that have no internal record at all.
MISSING_INTERNAL_COUNT = 30


def random_amount():
    """Random amount between NPR 500 and NPR 50,000, in paisa."""
    return random.randint(500, 50_000) * 100


def random_time():
    """Random timestamp within the simulated date range."""
    seconds = random.randint(0, DAYS * 24 * 60 * 60)
    return START_DATE + timedelta(seconds=seconds)


def provider_time(created_at):
    """The provider processes a payment a few seconds after we create it."""
    return created_at + timedelta(seconds=random.randint(1, 30))


def smaller_amount(amount):
    """A different amount (NPR 100 to 400 less) for amount mismatches."""
    return amount - random.randint(1, 4) * 10_000


def build_records():
    """Build internal records, provider records and ground truth."""
    random.seed(42)  # same output on every run

    internal = []
    provider = []
    truth = []

    # Put the scenarios in random order so they are mixed through the file.
    scenarios = []
    for name, count in SCENARIOS.items():
        scenarios += [name] * count
    random.shuffle(scenarios)

    for number, scenario in enumerate(scenarios, start=1001):
        reference = f"TXN-{number}"
        amount = random_amount()
        created_at = random_time()

        # Most payments succeed; some matched payments genuinely failed.
        status = "SUCCESS"
        if scenario == "MATCHED" and random.random() < 0.1:
            status = "FAILED"
        if scenario == "PENDING":
            status = "PENDING"

        internal.append({
            "transaction_id": f"INT-{number}",
            "reference": reference,
            "amount": amount,
            "currency": "NPR",
            "status": status,
            "payment_method": random.choice(PAYMENT_METHODS),
            "created_at": created_at,
        })

        # The provider's copy starts identical, then we change it per scenario.
        record = {
            "reference": reference,
            "amount": amount,
            "currency": "NPR",
            "status": status,
            "processed_at": provider_time(created_at),
        }
        expected = scenario

        if scenario == "AMOUNT_MISMATCH":
            record["amount"] = smaller_amount(amount)
        elif scenario == "STATUS_MISMATCH":
            record["status"] = "FAILED"
        elif scenario == "CURRENCY_MISMATCH":
            record["currency"] = "USD"
        elif scenario == "AMOUNT_AND_STATUS_MISMATCH":
            record["amount"] = smaller_amount(amount)
            record["status"] = "FAILED"
            expected = "AMOUNT_MISMATCH;STATUS_MISMATCH"

        if scenario == "MISSING_PROVIDER":
            pass  # the provider never reports it
        elif scenario == "DUPLICATE":
            provider.append(record)
            provider.append(dict(record))  # same record reported twice
        else:
            provider.append(record)

        truth.append({"reference": reference, "expected": expected})

    # Payments the provider processed but our system never recorded.
    for number in range(9001, 9001 + MISSING_INTERNAL_COUNT):
        reference = f"TXN-{number}"
        provider.append({
            "reference": reference,
            "amount": random_amount(),
            "currency": "NPR",
            "status": "SUCCESS",
            "processed_at": provider_time(random_time()),
        })
        truth.append({"reference": reference, "expected": "MISSING_INTERNAL"})

    # A provider report is ordered by processing time; give IDs in that order.
    provider.sort(key=lambda row: row["processed_at"])
    for number, record in enumerate(provider, start=2001):
        record["provider_id"] = f"PRV-{number}"

    return internal, provider, truth


def write_csv(filename, rows, columns):
    """Write rows (a list of dicts) to a CSV file in the output folder."""
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in columns})
    print(f"Wrote {len(rows):>5} rows to {path}")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    internal, provider, truth = build_records()

    write_csv("internal_transactions.csv", internal,
              ["transaction_id", "reference", "amount", "currency",
               "status", "payment_method", "created_at"])
    write_csv("provider_transactions.csv", provider,
              ["provider_id", "reference", "amount", "currency",
               "status", "processed_at"])
    write_csv("ground_truth.csv", truth, ["reference", "expected"])


if __name__ == "__main__":
    main()
