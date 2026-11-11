"""Tests for precise money transformation."""
from decimal import Decimal
from src.transform import transform_orders

def test_decimal_total():
    row={"quantity":3,"unit_price":Decimal("0.10")}
    assert transform_orders([row])[0]["total_amount"] == "0.30"
