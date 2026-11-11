"""Tests reconciliation checks."""
from src.load import connect
from src.reconcile import reconcile
from generator.data_generator import generate
from src.pipeline import run_pipeline

def test_empty_database(tmp_path):
    db=tmp_path/"empty.sqlite"; connect(db).close()
    assert all(reconcile(db)["assertions"].values())

def test_current_source_reconciliation(tmp_path):
    incoming = tmp_path / "incoming"
    orders, customers = generate(incoming, size=10, seed=7)
    db = tmp_path / "platform.sqlite"
    run_pipeline(orders, customers, db)
    result = reconcile(db, orders, customers)
    assert result["current_sources"]["source_orders"] == 16
    assert result["current_sources"]["duplicate_order_records"] == 1
    assert all(result["assertions"].values())
    assert result["reconciliation_status"] == "PASS"

def test_mismatched_current_source_is_reported(tmp_path):
    incoming = tmp_path / "incoming"
    orders, customers = generate(incoming, size=2, seed=8)
    db = tmp_path / "platform.sqlite"
    run_pipeline(orders, customers, db)
    lines = orders.read_text(encoding="utf-8").splitlines()
    columns = lines[1].split(",")
    columns[4] = "999999.99"
    lines[1] = ",".join(columns)
    orders.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = reconcile(db, orders, customers)
    assert result["reconciliation_status"] == "FAIL"
    assert not result["assertions"]["source_revenue_matches_target"]
