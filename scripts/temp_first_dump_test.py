import time
from pathlib import Path

from download import build_dump_set
from get_wiki_content import formatElapsedTime, get_dump_file_tags

TEMP_DB_PATH = Path.cwd() / "database" / "temp_first_dump.db"


def main():
    dump_files = get_dump_file_tags()
    if not dump_files:
        raise RuntimeError("No dump files were found at the configured Wikimedia URL.")

    build_start = time.perf_counter()
    print(f"Building temp database at {TEMP_DB_PATH}")
    processed_documents = build_dump_set(dump_files[:1], TEMP_DB_PATH)
    print(
        f"Temp build completed for {processed_documents} documents in "
        f"{formatElapsedTime(time.perf_counter() - build_start)}"
    )


if __name__ == "__main__":
    main()
