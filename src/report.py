"""Execute the packaged business SQL reports against the analytical database."""

import sqlite3
from contextlib import closing
from pathlib import Path

from src.config import DB_PATH, ROOT

REPORTS = {
    "total_revenue": "SELECT ROUND(SUM(total_amount),2) FROM fact_orders",
    "total_orders": "SELECT COUNT(*) FROM fact_orders",
    "total_quantity": "SELECT SUM(quantity) FROM fact_orders",
    "revenue_by_customer": "SELECT c.customer_id,c.customer_name,ROUND(SUM(f.total_amount),2) revenue FROM fact_orders f JOIN dim_customers c USING(customer_key) GROUP BY c.customer_id ORDER BY revenue DESC",
    "revenue_by_city": "SELECT c.city,ROUND(SUM(f.total_amount),2) revenue FROM fact_orders f JOIN dim_customers c USING(customer_key) GROUP BY c.city ORDER BY revenue DESC",
    "top_customers": "SELECT c.customer_id,c.customer_name,ROUND(SUM(f.total_amount),2) revenue FROM fact_orders f JOIN dim_customers c USING(customer_key) GROUP BY c.customer_id ORDER BY revenue DESC LIMIT 5",
    "daily_revenue": "SELECT substr(event_timestamp,1,10),ROUND(SUM(total_amount),2) FROM fact_orders GROUP BY 1 ORDER BY 1",
    "orders_by_city": "SELECT c.city,COUNT(*) FROM fact_orders f JOIN dim_customers c USING(customer_key) GROUP BY c.city ORDER BY 2 DESC",
    "rejections_by_reason": "SELECT rejection_reason,COUNT(*) FROM rejected_records GROUP BY rejection_reason ORDER BY 2 DESC",
    "pipeline_history": "SELECT run_id,start_time,end_time,duration_seconds,orders_input_count,valid_count,rejected_count,loaded_count,pipeline_status,error_message FROM pipeline_runs ORDER BY start_time DESC",
}


def print_reports(db_path: Path = DB_PATH) -> None:
    with closing(sqlite3.connect(db_path)) as conn:
        for title, query in REPORTS.items():
            print(f"\n{title.replace('_', ' ').title()}")
            rows = conn.execute(query).fetchall()
            display_rows = rows[:20] if title == "revenue_by_customer" else rows
            for row in display_rows:
                print("  " + " | ".join("NULL" if value is None else str(value) for value in row))
            if len(display_rows) < len(rows):
                print(f"  ... {len(rows) - len(display_rows)} more rows are available in the exported analytics JSON")


def export_reports(db_path: Path, output: Path) -> None:
    """Write report results as a JSON artifact."""
    import json
    results = {}
    with closing(sqlite3.connect(db_path)) as conn:
        for title, query in REPORTS.items():
            results[title] = conn.execute(query).fetchall()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
