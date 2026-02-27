"""Run the Phase 1 pipeline from the command line."""

import argparse
import logging
from pathlib import Path

from .pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)

# Default DB path must match Phase 2 API (phase1_data_pipeline/restaurants.db)
DEFAULT_DB = Path(__file__).resolve().parent / "restaurants.db"


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1: Load Zomato data and populate restaurant store.")
    parser.add_argument("--db", default=None, help=f"SQLite database path (default: {DEFAULT_DB})")
    parser.add_argument("--max-rows", type=int, default=None, help="Limit rows to load (default: all)")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear table before insert (append)")
    parser.add_argument("--cache-dir", default=None, help="Hugging Face cache directory (default: use HF_HOME or ~/.cache)")
    args = parser.parse_args()

    result = run_pipeline(
        db_path=args.db or DEFAULT_DB,
        max_rows=args.max_rows,
        clear_before=not args.no_clear,
        cache_dir=args.cache_dir,
    )
    print("Pipeline result:", result)


if __name__ == "__main__":
    main()
