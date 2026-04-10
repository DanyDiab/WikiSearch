import argparse
from pathlib import Path

from HITS import main as run_hits_query
from db import set_default_db_path


def parse_args():
    parser = argparse.ArgumentParser(description="Run TF-IDF + HITS against a selected SQLite database.")
    parser.add_argument(
        "--db",
        default="database/wiki.db",
        help="Path to the SQLite database file to query. Defaults to database/wiki.db.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    set_default_db_path(Path(args.db))
    run_hits_query()
