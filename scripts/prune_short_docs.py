import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "wiki.db"
MIN_LENGTH_EXCLUSIVE = 10


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    short_doc_count = cur.execute(
        """
        SELECT COUNT(*)
        FROM DOC_LENGTHS
        WHERE page_length < ?
        """,
        (MIN_LENGTH_EXCLUSIVE,),
    ).fetchone()[0]

    print(f"Docs with page_length < {MIN_LENGTH_EXCLUSIVE}: {short_doc_count}")

    cur.execute("BEGIN")

    # Delete postings for short docs first so the inverted index no longer references them.
    cur.execute(
        """
        DELETE FROM INVERTED_INDEX
        WHERE doc_id IN (
            SELECT doc_id
            FROM DOC_LENGTHS
            WHERE page_length < ?
        )
        """,
        (MIN_LENGTH_EXCLUSIVE,),
    )

    # Remove links where a short doc is either the source or destination.
    cur.execute(
        """
        DELETE FROM LINKS
        WHERE doc_id IN (
            SELECT doc_id
            FROM DOC_LENGTHS
            WHERE page_length < ?
        )
        OR link_id IN (
            SELECT doc_id
            FROM DOC_LENGTHS
            WHERE page_length < ?
        )
        """,
        (MIN_LENGTH_EXCLUSIVE, MIN_LENGTH_EXCLUSIVE),
    )

    cur.execute(
        """
        DELETE FROM DOCUMENTS
        WHERE doc_id IN (
            SELECT doc_id
            FROM DOC_LENGTHS
            WHERE page_length < ?
        )
        """,
        (MIN_LENGTH_EXCLUSIVE,),
    )

    cur.execute(
        """
        DELETE FROM DOC_LENGTHS
        WHERE page_length < ?
        """,
        (MIN_LENGTH_EXCLUSIVE,),
    )

    # Clean up unused terms after the posting deletions.
    cur.execute(
        """
        DELETE FROM TERMS
        WHERE term_id NOT IN (
            SELECT DISTINCT term_id
            FROM INVERTED_INDEX
        )
        """
    )

    conn.commit()

    remaining_docs = cur.execute("SELECT COUNT(*) FROM DOCUMENTS").fetchone()[0]
    remaining_postings = cur.execute("SELECT COUNT(*) FROM INVERTED_INDEX").fetchone()[0]
    remaining_terms = cur.execute("SELECT COUNT(*) FROM TERMS").fetchone()[0]

    print(f"Remaining documents: {remaining_docs}")
    print(f"Remaining postings: {remaining_postings}")
    print(f"Remaining terms: {remaining_terms}")

    conn.close()


if __name__ == "__main__":
    main()
