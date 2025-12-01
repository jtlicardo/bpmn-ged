"""
Compute the average similarity from a CSV file.

Usage:
    python src/average_similarity.py path/to/file.csv [--column similarity]
"""

import argparse
import csv
from pathlib import Path
from typing import Iterable


def read_column(rows: Iterable[dict], column: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        if column not in row:
            raise ValueError(f"Column '{column}' not found in CSV headers: {list(row.keys())}")
        try:
            values.append(float(row[column]))
        except ValueError as exc:
            raise ValueError(f"Could not parse '{row[column]}' in column '{column}' as float") from exc
    return values


def compute_average(values: list[float]) -> float:
    if not values:
        raise ValueError("No rows found to compute average")
    return sum(values) / len(values)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute average similarity from CSV.")
    parser.add_argument("csv_path", type=Path, help="Path to the CSV file (must have a header row).")
    parser.add_argument(
        "--column",
        default="similarity",
        help="Name of the column to average (default: similarity).",
    )
    args = parser.parse_args()

    with args.csv_path.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        values = read_column(reader, args.column)

    average = compute_average(values)
    print(f"Average {args.column}: {average:.5f} (from {len(values)} rows)")


if __name__ == "__main__":
    main()
