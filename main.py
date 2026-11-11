"""Command-line interface for generating, running, reporting, and reconciling."""

import argparse
import json
import sqlite3
from pathlib import Path

from generator.data_generator import generate
from src.config import DB_PATH, INCOMING, OUTPUT, ensure_directories
from src.monitor import run_history
from src.pipeline import run_pipeline
from src.reconcile import reconcile
from src.report import export_reports, print_reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="generate optional data and run pipeline")
    run.add_argument("--orders", type=int, help="generate this many valid base orders before pipeline")
    run.add_argument("--seed", type=int, default=42)
    sub.add_parser("report", help="display analytical reports")
    sub.add_parser("status", help="display run history")
    sub.add_parser("reconcile", help="run source/target consistency checks")
    reset = sub.add_parser("reset", help="remove only the demo SQLite database")
    reset.add_argument("--confirm", action="store_true", help="confirm database deletion")
    args = parser.parse_args()
    ensure_directories()
    if args.command == "run":
        if args.orders is not None:
            generate(INCOMING, args.orders, args.seed)
        print(json.dumps(run_pipeline(), indent=2))
    elif args.command == "report":
        print_reports()
        export_reports(DB_PATH, OUTPUT / "analytics.json")
    elif args.command == "status":
        print(json.dumps(run_history(DB_PATH), indent=2))
    elif args.command == "reconcile":
        result = reconcile(DB_PATH, INCOMING / "orders.csv", INCOMING / "customers.csv")
        (OUTPUT / "reconciliation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        if result["reconciliation_status"] != "PASS":
            raise SystemExit(f"Reconciliation failed; see {OUTPUT / 'reconciliation.json'}")
    elif args.command == "reset":
        if not args.confirm:
            print(f"Dry run: would remove {DB_PATH}; pass --confirm to proceed.")
        elif DB_PATH.exists():
            DB_PATH.unlink()
            print(f"Removed demo database: {DB_PATH}")
        else:
            print("Demo database does not exist.")


if __name__ == "__main__":
    main()
