"""Tests full pipeline reruns and invalid customer quarantine."""
import sqlite3
import pytest
from src.pipeline import run_pipeline

def test_rerun_and_invalid_reference(sample_sources,tmp_path):
    orders,customers=sample_sources; db=tmp_path/"pipeline.sqlite"
    first=run_pipeline(orders,customers,db); second=run_pipeline(orders,customers,db)
    assert first["loaded_count"] == 1 and second["loaded_count"] == 0
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM pipeline_runs WHERE pipeline_status='SUCCESS'").fetchone()[0] == 2
    text=orders.read_text(encoding="utf-8").replace("C1,P1","MISSING,P1")
    orders.write_text(text,encoding="utf-8")
    run=run_pipeline(orders,customers,db)
    assert run["rejected_count"] == 1

def test_additional_new_order_is_appended(sample_sources,tmp_path):
    orders,customers=sample_sources; db=tmp_path/"append.sqlite"
    run_pipeline(orders,customers,db)
    with orders.open("a",encoding="utf-8") as handle:
        handle.write("O2,C1,P2,1,2.00,2025-02-02T00:00:00Z\n")
    run_pipeline(orders,customers,db)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0] == 2

def test_missing_input_records_failed_run(tmp_path):
    db = tmp_path / "failed.sqlite"
    with pytest.raises(FileNotFoundError):
        run_pipeline(tmp_path / "missing-orders.csv", tmp_path / "missing-customers.csv", db)
    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT pipeline_status,error_message FROM pipeline_runs").fetchone()
    assert row[0] == "FAILED" and "Source file not found" in row[1]
