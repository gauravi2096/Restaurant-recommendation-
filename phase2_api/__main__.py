"""Run the Phase 2 API server."""

import argparse
import uvicorn
from pathlib import Path

# Load .env so GROQ_API_KEY is available for Phase 3 summary generation
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from .api import create_app

DEFAULT_DB = Path(__file__).resolve().parent.parent / "phase1_data_pipeline" / "restaurants.db"


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2: Restaurant Recommendation API")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--db", default=None, help=f"SQLite DB path (default: {DEFAULT_DB})")
    args = parser.parse_args()
    app = create_app(db_path=args.db or DEFAULT_DB)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
