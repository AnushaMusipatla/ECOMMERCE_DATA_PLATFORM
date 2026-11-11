"""Publish dimensions, facts, rejects, and run metadata in SQLite transactions."""

import json
import hashlib
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import DB_PATH, ROOT


def _customer_key(customer_id: str) -> int:
    """Map a natural key to a stable, positive 63-bit SQLite integer key."""
    digest = hashlib.sha256(customer_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript((ROOT / "database" / "schema.sql").read_text(encoding="utf-8"))
    return conn


def publish(path: Path, run: dict[str, Any], customers: list[dict[str, Any]],
            orders: list[dict[str, Any]], rejects: list[dict[str, str]],
            started_clock: float | None = None) -> None:
    """Atomically upsert dimensions/facts and persist run and reject details."""
    conn = connect(path)
    try:
        with conn:
            conn.execute("INSERT INTO pipeline_runs(run_id,start_time,end_time,duration_seconds,orders_input_count,customers_input_count,valid_count,rejected_count,loaded_count,pipeline_status,error_message) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                         tuple(run[k] for k in ("run_id", "start_time", "end_time", "duration_seconds", "orders_input_count", "customers_input_count", "valid_count", "rejected_count", "loaded_count", "pipeline_status", "error_message")))
            for c in customers:
                conn.execute("INSERT INTO dim_customers(customer_key,customer_id,customer_name,city,registration_date) VALUES(?,?,?,?,?) ON CONFLICT(customer_id) DO UPDATE SET customer_name=excluded.customer_name,city=excluded.city,registration_date=excluded.registration_date",
                             (_customer_key(c["customer_id"]), c["customer_id"], c["customer_name"], c["city"], c["registration_date"]))
            fact_count_before = conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0]
            for o in orders:
                customer_key = conn.execute("SELECT customer_key FROM dim_customers WHERE customer_id=?", (o["customer_id"],)).fetchone()
                if customer_key is None:
                    raise sqlite3.IntegrityError(f"Customer dimension missing for {o['customer_id']}")
                conn.execute("INSERT INTO fact_orders(order_id,customer_key,product_id,quantity,unit_price,total_amount,event_timestamp,source_file,run_id) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(order_id) DO NOTHING",
                             (o["order_id"], customer_key[0], o["product_id"], o["quantity"], o["unit_price"], o["total_amount"], o["event_timestamp"], o["source_file"], run["run_id"]))
            run["loaded_count"] = conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0] - fact_count_before
            conn.execute("UPDATE pipeline_runs SET loaded_count=? WHERE run_id=?",
                         (run["loaded_count"], run["run_id"]))
            for r in rejects:
                conn.execute("INSERT INTO rejected_records(run_id,source_file,rejected_at,rejection_reason,source_record) VALUES(?,?,?,?,?)",
                             (run["run_id"], r["source_file"], r["rejected_at"], r["rejection_reason"], json.dumps(r["source_record"], sort_keys=True)))
            if started_clock is not None:
                run["duration_seconds"] = time.perf_counter() - started_clock
                run["end_time"] = datetime.now(timezone.utc).isoformat()
                conn.execute("UPDATE pipeline_runs SET duration_seconds=?,end_time=? WHERE run_id=?",
                             (run["duration_seconds"], run["end_time"], run["run_id"]))
    finally:
        conn.close()
