"""Measure pipeline stages at 1k, 10k, and 100k order scales."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.data_generator import generate
from src.pipeline import run_pipeline
from src.reconcile import reconcile
from src.report import export_reports


def benchmark(sizes: list[int], seed: int = 42) -> list[dict]:
    """Run each size in an isolated temporary workspace and return measured timings."""
    measurements = []
    with tempfile.TemporaryDirectory(prefix="ecommerce-benchmark-") as temporary:
        root = Path(temporary)
        for size in sizes:
            case = root / str(size)
            incoming = case / "incoming"
            database = case / "ecommerce.db"
            generate(incoming, size=size, seed=seed)
            run = run_pipeline(incoming / "orders.csv", incoming / "customers.csv", database)
            performance_path = case / "data" / "output" / f"performance_{run['run_id']}.json"
            timings = json.loads(performance_path.read_text(encoding="utf-8"))
            export_reports(database, case / "analytics.json")
            reconciliation = reconcile(database, incoming / "orders.csv", incoming / "customers.csv")
            if reconciliation["reconciliation_status"] != "PASS":
                raise AssertionError(f"Benchmark reconciliation failed at size {size}: {reconciliation}")
            measurements.append({"base_orders": size, "input_rows": run["orders_input_count"], **timings})
            measurements[-1]["reconciliation_assertions"] = reconciliation["assertions"]
    return measurements


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[1000, 10000, 100000])
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if any(size < 0 for size in args.sizes):
        parser.error("all sizes must be zero or greater")
    print(json.dumps(benchmark(args.sizes, args.seed), indent=2))


if __name__ == "__main__":
    main()
