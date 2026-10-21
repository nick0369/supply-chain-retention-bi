import argparse
import json
import logging
import os
from pathlib import Path

from operations.pipeline import run


def main():
    parser = argparse.ArgumentParser(description="Build operational BI from historical DataCo records")
    parser.add_argument("command", choices=["build"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source", type=Path, help="Optional local DataCo CSV or compatible incremental batch")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--as-of", help="Customer snapshot date (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="Reapply a batch even when its checksum is known")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        result = run(args.root.resolve(), args.source, args.database_url, args.as_of, args.force)
        print(json.dumps(result, indent=2))
    except Exception:
        logging.getLogger(__name__).exception("Build failed; inspect validation before retrying")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
