import math
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATABASE_DIR = BASE_DIR / "database"
WIKI_DB = DATABASE_DIR / "wiki.db"

DOCUMENTS_TABLE = "DOCUMENTS"
DOC_LENGTH_TABLE = "DOC_LENGTHS"
LINKS_TABLE = "LINKS"
INVERTED_INDEX_TABLE = "INVERTED_INDEX"
TERMS_TABLE = "TERMS"
RAW_LINKS_TABLE = "RAW_LINKS"

PRAGMAS = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA foreign_keys=OFF",
)
SQLITE_VARIABLE_LIMIT = 900


class Database:
    def __init__(self, db_path: Path = WIKI_DB):
        self.db_path = db_path
        self.connection = self._connect()
        self.connection.create_function("log", 1, self._safe_log)
        self.cursor = self.connection.cursor()

    def _connect(self) -> sqlite3.Connection:
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        for pragma in PRAGMAS:
            connection.execute(pragma)
        return connection

    @staticmethod
    def _safe_log(value: float) -> float:
        if value <= 0:
            return 0.0
        return math.log(value)

    def close(self):
        self.connection.close()

    def commit(self):
        self.connection.commit()

    def execute_query(self, query: str, params=()):
        result = self.cursor.execute(query, params)
        return result.fetchall()

    def execute_many(self, query: str, data):
        self.cursor.executemany(query, data)

    def drop_table(self, table_name: str):
        self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

    def reset_database(self):
        for table_name in (
            LINKS_TABLE,
            RAW_LINKS_TABLE,
            INVERTED_INDEX_TABLE,
            TERMS_TABLE,
            DOC_LENGTH_TABLE,
            DOCUMENTS_TABLE,
        ):
            self.drop_table(table_name)
        self.connection.commit()
        self.connection.execute("VACUUM")

    def create_schema(self):
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DOCUMENTS_TABLE} (
                doc_id INTEGER PRIMARY KEY NOT NULL,
                page_name TEXT NOT NULL
            )
            """
        )
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DOC_LENGTH_TABLE} (
                doc_id INTEGER PRIMARY KEY NOT NULL,
                page_length INTEGER NOT NULL
            )
            """
        )
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TERMS_TABLE} (
                term_id INTEGER PRIMARY KEY,
                term TEXT NOT NULL UNIQUE
            )
            """
        )
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {INVERTED_INDEX_TABLE} (
                term_id INTEGER NOT NULL,
                doc_id INTEGER NOT NULL,
                word_count INTEGER NOT NULL,
                tf_idf REAL,
                PRIMARY KEY (term_id, doc_id)
            )
            """
        )
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {RAW_LINKS_TABLE} (
                doc_id INTEGER NOT NULL,
                target_title TEXT NOT NULL
            )
            """
        )
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {LINKS_TABLE} (
                doc_id INTEGER NOT NULL,
                link_id INTEGER NOT NULL
            )
            """
        )
        self.connection.commit()

    def insert_documents(self, documents: list[tuple[int, str]]):
        if not documents:
            return
        self.execute_many(
            f"INSERT OR REPLACE INTO {DOCUMENTS_TABLE} (doc_id, page_name) VALUES (?, ?)",
            documents,
        )

    def insert_doc_lengths(self, doc_lengths: list[tuple[int, int]]):
        if not doc_lengths:
            return
        self.execute_many(
            f"INSERT OR REPLACE INTO {DOC_LENGTH_TABLE} (doc_id, page_length) VALUES (?, ?)",
            doc_lengths,
        )

    def ensure_terms(self, terms: list[str]):
        if not terms:
            return
        for start in range(0, len(terms), SQLITE_VARIABLE_LIMIT):
            chunk = terms[start:start + SQLITE_VARIABLE_LIMIT]
            self.execute_many(
                f"INSERT OR IGNORE INTO {TERMS_TABLE} (term) VALUES (?)",
                [(term,) for term in chunk],
            )

    def fetch_term_ids(self, terms: list[str]) -> dict[str, int]:
        if not terms:
            return {}

        term_ids = {}
        for start in range(0, len(terms), SQLITE_VARIABLE_LIMIT):
            chunk = terms[start:start + SQLITE_VARIABLE_LIMIT]
            placeholders = ",".join("?" for _ in chunk)
            rows = self.execute_query(
                f"SELECT term, term_id FROM {TERMS_TABLE} WHERE term IN ({placeholders})",
                tuple(chunk),
            )
            term_ids.update({term: term_id for term, term_id in rows})

        return term_ids

    def insert_postings(self, postings: list[tuple[int, int, int]]):
        if not postings:
            return
        self.execute_many(
            f"""
            INSERT INTO {INVERTED_INDEX_TABLE} (term_id, doc_id, word_count)
            VALUES (?, ?, ?)
            ON CONFLICT(term_id, doc_id)
            DO UPDATE SET word_count = excluded.word_count
            """,
            postings,
        )

    def insert_raw_links(self, raw_links: list[tuple[int, str]]):
        if not raw_links:
            return
        self.execute_many(
            f"INSERT INTO {RAW_LINKS_TABLE} (doc_id, target_title) VALUES (?, ?)",
            raw_links,
        )

    def create_indexes(self):
        statements = (
            f"CREATE INDEX IF NOT EXISTS idx_documents_page_name ON {DOCUMENTS_TABLE}(page_name)",
            f"CREATE INDEX IF NOT EXISTS idx_doc_lengths_doc_id ON {DOC_LENGTH_TABLE}(doc_id)",
            f"CREATE UNIQUE INDEX IF NOT EXISTS idx_terms_term ON {TERMS_TABLE}(term)",
            f"CREATE INDEX IF NOT EXISTS idx_inverted_term_doc ON {INVERTED_INDEX_TABLE}(term_id, doc_id)",
            f"CREATE INDEX IF NOT EXISTS idx_inverted_doc_id ON {INVERTED_INDEX_TABLE}(doc_id)",
            f"CREATE INDEX IF NOT EXISTS idx_links_doc_id ON {LINKS_TABLE}(doc_id)",
            f"CREATE INDEX IF NOT EXISTS idx_links_link_id ON {LINKS_TABLE}(link_id)",
            f"CREATE INDEX IF NOT EXISTS idx_raw_links_target_title ON {RAW_LINKS_TABLE}(target_title)",
        )
        for statement in statements:
            self.cursor.execute(statement)
        self.connection.commit()

    def resolve_links(self):
        self.cursor.execute(f"DELETE FROM {LINKS_TABLE}")
        self.cursor.execute(
            f"""
            INSERT INTO {LINKS_TABLE} (doc_id, link_id)
            SELECT DISTINCT rl.doc_id, d.doc_id
            FROM {RAW_LINKS_TABLE} rl
            JOIN {DOCUMENTS_TABLE} d
                ON d.page_name = rl.target_title
            WHERE rl.doc_id != d.doc_id
            """
        )
        self.connection.commit()

    def calculate_tfidf(self):
        total_docs_row = self.cursor.execute(
            f"SELECT COUNT(*) FROM {DOC_LENGTH_TABLE}"
        ).fetchone()
        total_docs = total_docs_row[0] if total_docs_row else 0
        if total_docs == 0:
            return

        self.cursor.execute(
            f"""
            WITH term_document_frequency AS (
                SELECT term_id, COUNT(*) AS doc_frequency
                FROM {INVERTED_INDEX_TABLE}
                GROUP BY term_id
            )
            UPDATE {INVERTED_INDEX_TABLE}
            SET tf_idf = (
                CAST(word_count AS REAL) / NULLIF(
                    (SELECT page_length
                     FROM {DOC_LENGTH_TABLE}
                     WHERE doc_id = {INVERTED_INDEX_TABLE}.doc_id),
                    0
                )
            ) * log(
                CAST(? AS REAL) / (
                    SELECT doc_frequency
                    FROM term_document_frequency
                    WHERE term_id = {INVERTED_INDEX_TABLE}.term_id
                )
            )
            """,
            (total_docs,),
        )
        self.connection.commit()

    def finalize_database(self):
        self.create_indexes()
        self.resolve_links()
        self.calculate_tfidf()
        self.drop_table(RAW_LINKS_TABLE)
        self.connection.commit()


def get_database() -> Database:
    return Database()
