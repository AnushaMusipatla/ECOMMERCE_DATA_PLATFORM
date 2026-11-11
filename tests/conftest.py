"""Shared isolated fixtures for the test suite."""
import csv
import pytest

@pytest.fixture
def sample_sources(tmp_path):
    customers, orders = tmp_path / "customers.csv", tmp_path / "orders.csv"
    with customers.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["customer_id","customer_name","city","registration_date"]); w.writeheader(); w.writerow({"customer_id":"C1","customer_name":"Ada","city":"Pune","registration_date":"2024-01-01"})
    with orders.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["order_id","customer_id","product_id","quantity","unit_price","event_timestamp"]); w.writeheader(); w.writerow({"order_id":"O1","customer_id":"C1","product_id":"P1","quantity":"2","unit_price":"1.25","event_timestamp":"2025-02-01T00:00:00Z"})
    return orders, customers
