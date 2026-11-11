"""Orchestrate ingestion, quality checks, transformation, and atomic publication."""

import csv
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.config import DB_PATH, INCOMING, REJECTS, VALIDATED, CURATED, OUTPUT, ensure_directories
from src.ingest import read_source
from src.load import connect, publish
from src.logger import get_logger
from src.transform import transform_orders
from src.validate import validate_customers, validate_orders


def run_pipeline(orders_path: Path = INCOMING / "orders.csv", customers_path: Path = INCOMING / "customers.csv",
                 db_path: Path = DB_PATH) -> dict:
    ensure_directories()
    demo_database = db_path.resolve() == DB_PATH.resolve()
    data_root = (DB_PATH.parent.parent / "data") if demo_database else db_path.parent / "data"
    raw_root = (DB_PATH.parent.parent / "data" / "raw") if demo_database else data_root / "raw"
    validated_root, reject_root = data_root / "validated", data_root / "rejects"
    curated_root, output_root = data_root / "curated", data_root / "output"
    for directory in (raw_root, validated_root, reject_root, curated_root, output_root):
        directory.mkdir(parents=True, exist_ok=True)
    logger = get_logger()
    run_id, started, start_clock = uuid.uuid4().hex, datetime.now(timezone.utc), time.perf_counter()
    timings = {}
    logger.info("run_id=%s pipeline started", run_id)
    orders_count = customers_count = valid_count = rejected_count = 0
    try:
        stage_clock = time.perf_counter()
        orders, order_file = read_source(orders_path, run_id, raw_root)
        customers, customer_file = read_source(customers_path, run_id, raw_root)
        timings["ingest_seconds"] = time.perf_counter() - stage_clock
        orders_count, customers_count = len(orders), len(customers)
        stage_clock = time.perf_counter()
        clean_customers, customer_rejects = validate_customers(customers)
        clean_orders, order_rejects = validate_orders(orders, {c["customer_id"] for c in clean_customers})
        timings["validation_seconds"] = time.perf_counter() - stage_clock
        valid_count, rejected_count = len(clean_orders), len(order_rejects) + len(customer_rejects)
        stamp = datetime.now(timezone.utc).isoformat()
        reject_rows = ([{"source_file": order_file, "rejected_at": stamp, "rejection_reason": why, "source_record": row} for row, why in order_rejects]
                       + [{"source_file": customer_file, "rejected_at": stamp, "rejection_reason": why, "source_record": row} for row, why in customer_rejects])
        run = {"run_id": run_id, "start_time": started.isoformat(), "end_time": stamp,
               "duration_seconds": time.perf_counter() - start_clock, "orders_input_count": orders_count,
               "customers_input_count": customers_count, "valid_count": valid_count, "rejected_count": rejected_count,
               "loaded_count": len(clean_orders), "pipeline_status": "SUCCESS", "error_message": None,
               "source_files": {"orders": order_file, "customers": customer_file}}
        stage_clock = time.perf_counter()
        curated = transform_orders(clean_orders)
        for row in curated: row["source_file"] = order_file
        timings["transformation_seconds"] = time.perf_counter() - stage_clock
        stage_clock = time.perf_counter()
        publish(db_path, run, clean_customers, curated, reject_rows, start_clock)
        timings["database_load_seconds"] = time.perf_counter() - stage_clock
        timings["total_seconds"] = time.perf_counter() - start_clock
        timings["records_per_second"] = orders_count / timings["total_seconds"] if timings["total_seconds"] else 0
        _write_csv(validated_root / f"customers_{run_id}.csv", clean_customers)
        _write_csv(validated_root / f"orders_{run_id}.csv", curated)
        _write_csv(curated_root / f"fact_orders_{run_id}.csv", curated)
        _write_csv(reject_root / f"rejected_{run_id}.csv", [dict(r["source_record"], source_file=r["source_file"], run_id=run_id, rejected_at=r["rejected_at"], rejection_reason=r["rejection_reason"]) for r in reject_rows])
        (output_root / f"run_{run_id}.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
        (output_root / f"performance_{run_id}.json").write_text(json.dumps(timings, indent=2), encoding="utf-8")
        logger.info("run_id=%s status=SUCCESS orders=%d valid=%d rejected=%d loaded=%d", run_id, orders_count, len(clean_orders), rejected_count, run["loaded_count"])
        return run
    except Exception as exc:
        # The failed run marker is recorded separately after the publishing transaction rolls back.
        ended = datetime.now(timezone.utc)
        failed = {"run_id": run_id, "start_time": started.isoformat(), "end_time": ended.isoformat(),
                  "duration_seconds": time.perf_counter() - start_clock, "orders_input_count": orders_count,
                  "customers_input_count": customers_count, "valid_count": valid_count, "rejected_count": rejected_count,
                  "loaded_count": 0, "pipeline_status": "FAILED", "error_message": str(exc)}
        conn = connect(db_path)
        try:
            with conn:
                conn.execute("INSERT OR IGNORE INTO pipeline_runs(run_id,start_time,end_time,duration_seconds,orders_input_count,customers_input_count,valid_count,rejected_count,loaded_count,pipeline_status,error_message) VALUES(?,?,?,?,?,?,?,?,?,?,?)", tuple(failed[k] for k in ("run_id", "start_time", "end_time", "duration_seconds", "orders_input_count", "customers_input_count", "valid_count", "rejected_count", "loaded_count", "pipeline_status", "error_message")))
        finally:
            conn.close()
        logger.exception("run_id=%s status=FAILED error=%s", run_id, exc)
        (output_root / f"run_{run_id}.json").write_text(json.dumps(failed, indent=2), encoding="utf-8")
        raise


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(dict.fromkeys(key for row in rows for key in row))
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
