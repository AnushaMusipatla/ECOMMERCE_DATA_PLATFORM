"""Tests for database constraints, idempotency, and rollback."""
import sqlite3
import pytest
from src.load import connect,publish
from src.load import _customer_key

def run(r):
    return {"run_id":r,"start_time":"2025-01-01T00:00:00Z","end_time":"2025-01-01T00:00:01Z","duration_seconds":1,"orders_input_count":1,"customers_input_count":1,"valid_count":1,"rejected_count":0,"loaded_count":1,"pipeline_status":"SUCCESS","error_message":None}
C={"customer_id":"C1","customer_name":"Ada","city":"Pune","registration_date":"2024-01-01"}
O={"order_id":"O1","customer_id":"C1","product_id":"P1","quantity":1,"unit_price":"1.00","total_amount":"1.00","event_timestamp":"2025-01-01T00:00:00+00:00","source_file":"orders.csv"}

def test_idempotency_and_transaction_rollback(tmp_path):
    db=tmp_path/"db.sqlite"
    publish(db,run("r1"),[C],[O],[]); publish(db,run("r2"),[C],[O],[])
    conn=connect(db); assert conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0] == 1; conn.close()
    with pytest.raises(sqlite3.IntegrityError): publish(db,run("r3"),[{**C,"customer_id":"C2"}],[{**O,"order_id":"O2","customer_id":"missing"}],[])
    conn=connect(db)
    assert conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM dim_customers WHERE customer_id='C2'").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM pipeline_runs WHERE run_id='r3'").fetchone()[0] == 0
    conn.close()

def test_fk_enforced(tmp_path):
    conn=connect(tmp_path/"fk.sqlite")
    with pytest.raises(sqlite3.IntegrityError): conn.execute("INSERT INTO fact_orders(order_id,customer_key,product_id,quantity,unit_price,total_amount,event_timestamp,run_id) VALUES('O',999,'P',1,1,1,'x','r')")
    conn.close()

def test_customer_surrogate_key_is_deterministic():
    assert _customer_key("C1") == _customer_key("C1")
    assert _customer_key("C1") != _customer_key("C2")
