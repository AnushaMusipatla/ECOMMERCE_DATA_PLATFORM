"""Read independent CSV sources and preserve byte-for-byte raw copies."""

import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import RAW

SOURCE_COLUMNS = {
    "orders.csv": {"order_id", "customer_id", "product_id", "quantity", "unit_price", "event_timestamp"},
    "customers.csv": {"customer_id", "customer_name", "city", "registration_date"},
}


def read_source(path: Path, run_id: str, raw_dir: Path = RAW) -> tuple[list[dict[str, str]], str]:
    """Read a CSV as strings and retain the original file under the run ID."""
    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {path}")
    destination = raw_dir / run_id
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination / path.name)
    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"CSV has no header: {path}") from exc
    expected = SOURCE_COLUMNS.get(path.name)
    actual = set(frame.columns)
    if expected is not None and actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(f"Unexpected {path.name} schema; missing={missing}, unexpected={unexpected}")
    return frame.to_dict(orient="records"), path.name
