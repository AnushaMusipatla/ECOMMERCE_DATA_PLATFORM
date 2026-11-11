"""Tests for validation rules and edge cases."""
import pytest
from src.validate import validate_customers, validate_orders

C={"customer_id":"C1","customer_name":"Ada","city":"Pune","registration_date":"2024-01-01"}
O={"order_id":"O1","customer_id":"C1","product_id":"P1","quantity":"2","unit_price":"1.25","event_timestamp":"2025-02-01T00:00:00Z"}

def test_valid_and_empty():
    assert len(validate_customers([C])[0]) == 1
    assert validate_customers([]) == ([], [])

@pytest.mark.parametrize("field,value,reason", [("quantity","-1","quantity"),("quantity","bad","invalid"),("unit_price","0","unit_price"),("event_timestamp","bad","invalid"),("customer_id","C404","customer reference")])
def test_bad_orders(field,value,reason):
    assert reason in validate_orders([{**O,field:value}], {"C1"})[1][0][1]

def test_duplicate_ids():
    assert validate_orders([O,O], {"C1"})[1][0][1] == "duplicate order_id"
    assert validate_customers([C,C])[1][0][1] == "duplicate customer_id"

def test_schema_change_fails_visibly():
    with pytest.raises(ValueError, match="Unexpected orders schema"):
        validate_orders([{**O,"unexpected":"x"}], {"C1"})

def test_late_event_is_valid():
    assert len(validate_orders([{**O,"event_timestamp":"2020-01-01T00:00:00Z"}], {"C1"})[0]) == 1

def test_missing_and_negative_price_are_rejected():
    rows = [{**O, "quantity": ""}, {**O, "order_id": "O2", "unit_price": "-1.00"}]
    valid, rejected = validate_orders(rows, {"C1"})
    assert not valid
    assert len(rejected) == 2
