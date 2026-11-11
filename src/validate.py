"""Schema, business-rule, uniqueness, and cross-source validation."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

CUSTOMER_COLUMNS = {"customer_id", "customer_name", "city", "registration_date"}
ORDER_COLUMNS = {"order_id", "customer_id", "product_id", "quantity", "unit_price", "event_timestamp"}


def _check_schema(rows: list[dict[str, Any]], expected: set[str], label: str) -> None:
    actual = set(rows[0]) if rows else expected
    missing, unexpected = expected - actual, actual - expected
    if missing or unexpected:
        raise ValueError(f"Unexpected {label} schema; missing={sorted(missing)}, unexpected={sorted(unexpected)}")


def validate_customers(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[tuple[dict[str, Any], str]]]:
    _check_schema(rows, CUSTOMER_COLUMNS, "customers")
    valid, rejected, seen = [], [], set()
    for row in rows:
        reason = ""
        cid = (row.get("customer_id") or "").strip()
        if not cid: reason = "missing customer_id"
        elif cid in seen: reason = "duplicate customer_id"
        elif not (row.get("customer_name") or "").strip(): reason = "missing customer_name"
        elif not (row.get("city") or "").strip(): reason = "missing city"
        else:
            try: date.fromisoformat(row["registration_date"].strip())
            except (ValueError, AttributeError): reason = "invalid registration_date"
        if reason: rejected.append((row, reason))
        else:
            seen.add(cid)
            valid.append({**row, "customer_id": cid, "customer_name": row["customer_name"].strip(),
                          "city": row["city"].strip(), "registration_date": row["registration_date"].strip()})
    return valid, rejected


def validate_orders(rows: list[dict[str, Any]], customer_ids: set[str]) -> tuple[list[dict[str, Any]], list[tuple[dict[str, Any], str]]]:
    _check_schema(rows, ORDER_COLUMNS, "orders")
    valid, rejected, seen = [], [], set()
    for row in rows:
        reason = ""
        oid, cid = (row.get("order_id") or "").strip(), (row.get("customer_id") or "").strip()
        if not oid: reason = "missing order_id"
        elif oid in seen: reason = "duplicate order_id"
        elif not cid: reason = "missing customer_id"
        elif cid not in customer_ids: reason = "invalid customer reference"
        elif not (row.get("product_id") or "").strip(): reason = "missing product_id"
        else:
            try:
                quantity = int(row["quantity"])
                price = Decimal(row["unit_price"])
                timestamp = datetime.fromisoformat(row["event_timestamp"].replace("Z", "+00:00"))
                if quantity <= 0: reason = "quantity must be greater than zero"
                elif not price.is_finite() or price <= 0: reason = "unit_price must be positive"
            except (ValueError, TypeError, InvalidOperation, AttributeError):
                reason = "invalid quantity, unit_price, or event_timestamp"
        if reason: rejected.append((row, reason))
        else:
            seen.add(oid)
            valid.append({**row, "order_id": oid, "customer_id": cid, "product_id": row["product_id"].strip(),
                          "quantity": quantity, "unit_price": price, "event_timestamp": timestamp.isoformat()})
    return valid, rejected
