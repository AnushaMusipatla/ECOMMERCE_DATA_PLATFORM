"""Compare source quality counts with the published analytical fact table."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from decimal import Decimal

import pandas as pd

from src.transform import transform_orders
from src.validate import validate_customers, validate_orders


def reconcile(db_path: Path, orders_path: Path | None = None,
              customers_path: Path | None = None) -> dict:
    """Reconcile published facts, optionally against the current independent CSV sources."""
    with closing(sqlite3.connect(db_path)) as conn:
        target = conn.execute("SELECT COUNT(*), COALESCE(SUM(total_amount),0), COUNT(DISTINCT order_id) FROM fact_orders").fetchone()
        runs = conn.execute("SELECT COUNT(*), COALESCE(SUM(orders_input_count),0), COALESCE(SUM(rejected_count),0), COALESCE(SUM(loaded_count),0) FROM pipeline_runs WHERE pipeline_status='SUCCESS'").fetchone()
        bad_refs = conn.execute("SELECT COUNT(*) FROM fact_orders f LEFT JOIN dim_customers c USING(customer_key) WHERE c.customer_key IS NULL").fetchone()[0]
        facts = {row[0]: Decimal(str(row[1])) for row in conn.execute("SELECT order_id,total_amount FROM fact_orders")}
    result = {"fact_orders": target[0], "fact_revenue": round(float(target[1]), 2), "distinct_order_ids": target[2],
              "successful_runs": runs[0], "source_orders_across_runs": runs[1], "rejected_across_runs": runs[2],
              "reported_loaded_count_across_runs": runs[3], "invalid_fact_customer_references": bad_refs,
              "assertions": {"fact_ids_unique": target[0] == target[2], "no_invalid_customer_refs": bad_refs == 0}}
    if orders_path is not None and customers_path is not None:
        customers_frame = pd.read_csv(customers_path, dtype=str, keep_default_na=False)
        orders_frame = pd.read_csv(orders_path, dtype=str, keep_default_na=False)
        clean_customers, customer_rejects = validate_customers(customers_frame.to_dict(orient="records"))
        clean_orders, order_rejects = validate_orders(orders_frame.to_dict(orient="records"),
                                                     {row["customer_id"] for row in clean_customers})
        transformed = transform_orders(clean_orders)
        source_ids = {row["order_id"] for row in transformed}
        missing_ids = source_ids - facts.keys()
        source_revenue = sum((Decimal(row["total_amount"]) for row in transformed), Decimal("0.00"))
        target_source_revenue = sum((facts[order_id] for order_id in source_ids if order_id in facts), Decimal("0.00"))
        result["current_sources"] = {
            "source_orders": len(orders_frame), "valid_orders": len(clean_orders),
            "rejected_orders": len(order_rejects), "rejected_customers": len(customer_rejects),
            "duplicate_order_records": sum("duplicate" in reason for _, reason in order_rejects),
            "duplicate_customer_records": sum("duplicate" in reason for _, reason in customer_rejects),
            "invalid_customer_reference_records": sum("customer reference" in reason for _, reason in order_rejects),
            "valid_source_revenue": round(float(source_revenue), 2),
            "loaded_source_revenue": round(float(target_source_revenue), 2),
            "distinct_valid_orders": len(source_ids), "loaded_orders": len(source_ids) - len(missing_ids),
            "missing_orders_in_target": len(missing_ids),
        }
        result["assertions"].update({
            "source_valid_orders_present": not missing_ids,
            "source_revenue_matches_target": source_revenue == target_source_revenue,
        })
    result["reconciliation_status"] = "PASS" if all(result["assertions"].values()) else "FAIL"
    return result
