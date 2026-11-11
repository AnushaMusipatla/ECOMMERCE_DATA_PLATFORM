"""Generate reproducible orders and customers from independent source systems."""

import argparse
import csv
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from src.config import INCOMING, ensure_directories

CUSTOMER_FIELDS = ("customer_id", "customer_name", "city", "registration_date")
ORDER_FIELDS = ("order_id", "customer_id", "product_id", "quantity", "unit_price", "event_timestamp")


def generate(output_dir: Path = INCOMING, size: int = 100, seed: int = 42,
             include_edge_cases: bool = True) -> tuple[Path, Path]:
    """Write separate source schemas; orders only reference customers by ID."""
    output_dir.mkdir(parents=True, exist_ok=True)
    customers_path, orders_path = output_dir / "customers.csv", output_dir / "orders.csv"
    cities = ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Pune"]
    # A fixed customer ID pool and one RNG per row make smaller runs exact prefixes
    # of larger runs. This makes --orders N safe for reproducible append demos.
    customer_pool_size = 10_000
    referenced_customers = set(range(1, 11))
    with orders_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ORDER_FIELDS)
        writer.writeheader()
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        generated_orders = []
        for i in range(size):
            rng = random.Random((seed << 32) ^ i)
            customer_number = rng.randint(1, customer_pool_size)
            referenced_customers.add(customer_number)
            when = base + timedelta(minutes=rng.randrange(0, 525600))
            row = {"order_id": f"O{i + 1:09d}",
                   "customer_id": f"C{customer_number:06d}",
                   "product_id": f"P{rng.randrange(1, 101):04d}",
                   "quantity": rng.randint(1, 5),
                   "unit_price": f"{rng.randint(100, 20000) / 100:.2f}",
                   "event_timestamp": when.isoformat()}
            generated_orders.append(row)
            writer.writerow(row)
        if include_edge_cases:
            # Deliberate quality cases exercise each major validation branch.
            edge_cases = [
                {"order_id": "O_INVALID_QTY", "customer_id": "C000001", "product_id": "P0001",
                 "quantity": "-2", "unit_price": "12.50", "event_timestamp": base.isoformat()},
                {"order_id": "O_INVALID_CUSTOMER", "customer_id": "C999999", "product_id": "P0002",
                 "quantity": "1", "unit_price": "3.25", "event_timestamp": base.isoformat()},
                {"order_id": "O_INVALID_TIME", "customer_id": "C000001", "product_id": "P0003",
                 "quantity": "1", "unit_price": "5.00", "event_timestamp": "not-a-timestamp"},
                {"order_id": "O_INVALID_PRICE", "customer_id": "C000001", "product_id": "P0004",
                 "quantity": "1", "unit_price": "-0.01", "event_timestamp": base.isoformat()},
                {"order_id": "O_MISSING_QUANTITY", "customer_id": "C000001", "product_id": "P0005",
                 "quantity": "", "unit_price": "5.00", "event_timestamp": base.isoformat()},
            ]
            writer.writerows(edge_cases)
            duplicate = generated_orders[0] if generated_orders else {
                "order_id": "O_DUPLICATE", "customer_id": "C000001", "product_id": "P0001",
                "quantity": "1", "unit_price": "1.00", "event_timestamp": base.isoformat()}
            writer.writerow(duplicate)
    if size >= customer_pool_size:
        referenced_customers.update(range(1, customer_pool_size + 1))
    with customers_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CUSTOMER_FIELDS)
        writer.writeheader()
        for customer_number in sorted(referenced_customers):
            writer.writerow({"customer_id": f"C{customer_number:06d}",
                             "customer_name": f"Customer {customer_number:06d}",
                             "city": cities[(customer_number - 1) % len(cities)],
                             "registration_date": (date(2022, 1, 1) + timedelta(days=(customer_number - 1) % 1000)).isoformat()})
        if include_edge_cases:
            # Repeated natural keys and invalid attributes exercise customer validation.
            writer.writerow({"customer_id": "C000001", "customer_name": "Duplicate Customer",
                             "city": "Pune", "registration_date": "2022-01-01"})
            writer.writerow({"customer_id": "C_MISSING_NAME", "customer_name": "",
                             "city": "Pune", "registration_date": "2022-01-01"})
            writer.writerow({"customer_id": "C_INVALID_DATE", "customer_name": "Invalid Date",
                             "city": "Delhi", "registration_date": "not-a-date"})
    return orders_path, customers_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=100, help="number of base orders (supports 100,000+)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=INCOMING)
    parser.add_argument("--clean", action="store_true", help="omit deliberate invalid edge cases")
    args = parser.parse_args()
    if args.size < 0:
        parser.error("--size must be zero or greater")
    ensure_directories()
    orders, customers = generate(args.output_dir, args.size, args.seed, not args.clean)
    print(f"Generated customers: {customers} ({sum(1 for _ in customers.open(encoding='utf-8')) - 1} rows)")
    print(f"Generated orders: {orders} ({sum(1 for _ in orders.open(encoding='utf-8')) - 1} rows)")


if __name__ == "__main__":
    main()
