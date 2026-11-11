"""Run a small reproducible generation and pipeline demo."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.data_generator import generate
from src.config import INCOMING
from src.pipeline import run_pipeline
from src.report import print_reports


def main() -> None:
    generate(INCOMING, size=100, seed=42)
    run_pipeline()
    print_reports()


if __name__ == "__main__":
    main()
