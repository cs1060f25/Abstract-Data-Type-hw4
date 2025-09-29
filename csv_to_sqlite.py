#!/usr/bin/env python3
"""
csv_to_sqlite.py

Usage:
  python3 csv_to_sqlite.py data.db some_table.csv

Behavior:
- Creates (if not exists) a table named after the CSV filename (without extension).
- Assumes the CSV has a header row with valid SQL identifiers (no spaces or quotes).
- All columns are created as TEXT and rows are inserted via a transaction for performance.
- If the table already exists, rows will be appended on subsequent runs.

Notes:
- Column names are used as bare identifiers (no quoting) per assignment guidance.
- Table name is derived from the CSV filename and lightly sanitized to be a valid identifier.
Attribution:
- This file was authored with generative AI assistance (Cascade). The code was reviewed and edited.
"""

import argparse
import csv
import os
import re
import sqlite3
import sys
from typing import List


def sanitize_identifier(name: str) -> str:
    """Ensure a safe SQL identifier: letters, digits, underscore; cannot start with digit.
    If the input contains other characters, replace them with underscore and prefix underscore
    if the first character is a digit after transformation.
    """
    # Lowercase for consistency
    name = name.strip()
    # Replace invalid characters with underscore
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    # Ensure doesn't start with digit
    if not name:
        name = "table"
    if name[0].isdigit():
        name = f"_{name}"
    return name


def validate_columns(cols: List[str]) -> List[str]:
    """Validate that columns are valid SQL identifiers as per assignment.
    If a column is not valid, we sanitize it in a predictable way.
    """
    valid_cols = []
    for c in cols:
        c = c.strip()
        # As per assignment, these should already be valid; we still enforce conservatively.
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", c):
            valid_cols.append(c)
        else:
            valid_cols.append(sanitize_identifier(c))
    return valid_cols


def build_create_table_sql(table: str, columns: List[str]) -> str:
    cols_sql = ", ".join(f"{col} TEXT" for col in columns)
    return f"CREATE TABLE IF NOT EXISTS {table} ({cols_sql});"


def build_insert_sql(table: str, columns: List[str]) -> str:
    placeholders = ", ".join(["?"] * len(columns))
    cols_sql = ", ".join(columns)
    return f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders});"


def import_csv_to_sqlite(db_path: str, csv_path: str) -> None:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Derive table name from CSV filename (sans extension)
    table_name_raw = os.path.splitext(os.path.basename(csv_path))[0]
    table_name = sanitize_identifier(table_name_raw)

    # Open CSV and read header
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("CSV appears to be empty (no header row).")

        columns = validate_columns(header)

        # Prepare DB
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            # Create table if not exists
            create_sql = build_create_table_sql(table_name, columns)
            conn.execute(create_sql)

            insert_sql = build_insert_sql(table_name, columns)

            # Insert rows within a transaction for speed
            with conn:
                batch = []
                batch_size = 1000
                for row in reader:
                    # Ensure row length matches columns; pad/truncate if necessary
                    if len(row) < len(columns):
                        row = row + [None] * (len(columns) - len(row))
                    elif len(row) > len(columns):
                        row = row[: len(columns)]
                    batch.append(row)
                    if len(batch) >= batch_size:
                        conn.executemany(insert_sql, batch)
                        batch.clear()
                if batch:
                    conn.executemany(insert_sql, batch)
        finally:
            conn.close()

    print(f"Imported '{csv_path}' into '{db_path}' as table '{table_name}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a CSV into a SQLite database as TEXT columns.")
    parser.add_argument("db", help="Path to SQLite database file (will be created if not exists)")
    parser.add_argument("csv", help="Path to input CSV file with a header row of valid SQL identifiers")
    args = parser.parse_args()

    try:
        import_csv_to_sqlite(args.db, args.csv)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
