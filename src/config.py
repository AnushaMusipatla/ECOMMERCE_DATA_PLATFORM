"""Central paths and settings for local pipeline execution."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
INCOMING = DATA / "incoming"
RAW = DATA / "raw"
VALIDATED = DATA / "validated"
CURATED = DATA / "curated"
REJECTS = DATA / "rejects"
OUTPUT = DATA / "output"
DB_DIR = ROOT / "database"
DB_PATH = DB_DIR / "ecommerce.db"
LOG_DIR = ROOT / "logs"
REPORT_DIR = ROOT / "reports"
METADATA_DIR = ROOT / "metadata"

DIRECTORIES = (INCOMING, RAW, VALIDATED, CURATED, REJECTS, OUTPUT,
               DB_DIR, LOG_DIR, REPORT_DIR, METADATA_DIR)


def ensure_directories() -> None:
    """Create the platform's local working directories."""
    for path in DIRECTORIES:
        path.mkdir(parents=True, exist_ok=True)
