"""Convert accepted source values into deterministic analytical records."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def transform_orders(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calculate exact two-decimal totals from Decimal prices."""
    output = []
    for row in rows:
        price = Decimal(row["unit_price"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        output.append({**row, "unit_price": str(price),
                       "total_amount": str((price * row["quantity"]).quantize(Decimal("0.01")))})
    return output
