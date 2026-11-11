"""Configure readable run-aware logging to console and a local file."""

import logging
from src.config import LOG_DIR, ensure_directories


def get_logger() -> logging.Logger:
    ensure_directories()
    logger = logging.getLogger("ecommerce_pipeline")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        for handler in (logging.StreamHandler(), logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8")):
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger
