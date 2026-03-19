import gc
import os
import pickle
import sqlite3

CWD = os.getcwd()
DATA_FOLDER = os.path.join(CWD, "data")
os.makedirs(DATA_FOLDER, exist_ok=True)

DB = os.path.join(DATA_FOLDER, "wiki.db")
BLOCK_DIR = os.path.join(CWD, "block_dir")


def open_pickle(path: str):
    with open(path, "rb") as p:
        return pickle.load(p)


def create_table(cursor, query):
    cursor.execute(query)



def drop_table(cursor, table_name):
    query = f"""
        DROP TABLE IF EXISTS {table_name};
    """
    insert_query(cursor, query)



def insert_query(cursor, query, args=None):
    cursor.execute(query, args or ())



def fetch_query(cursor, query, args=None):
    cursor.execute(query, args or ())
    return cursor.fetchall()



CRETE_TERMS_TABLE = """
CREATE TABLE TERMS (
    term_id INTEGER PRIMARY KEY,
    term TEXT NOT NULL UNIQUE
);
"""

CREATE_INVERTED_INDEX_TABLE = """
CREATE TABLE INVERTED_INDEX (
    term_id INTEGER,
    doc_id INTEGER,
    word_count INTEGER,
    PRIMARY KEY (term_id, doc_id)
)
"""


INSERT_TERM_QUERY = """
INSERT OR IGNORE INTO TERMS (term)
VALUES (?)
"""


SELECT_TERM_ID = """
SELECT term_id
FROM TERMS
WHERE term = ?
"""



INSERT_INVERTED_INDEX = """
INSERT OR REPLACE INTO INVERTED_INDEX (term_id, doc_id, word_count)
VALUES (?, ?, ?)
"""



if __name__ == '__main__':
    connection = sqlite3.connect(DB)
    cursor = connection.cursor()

    res = cursor.execute(
        """
        SELECT i.doc_id, i.word_count
        FROM INVERTED_INDEX i
        JOIN TERMS t on t.term_id = i.term_id
        WHERE t.term = 'cancer'
        ORDER BY i.doc_id
        """
    ).fetchall()
    print(res)
    print(len(res))
    # cursor.execute("PRAGMA journal_mode=WAL")
    # cursor.execute("PRAGMA synchronous=NORMAL")
    # cursor.execute("PRAGMA temp_store=MEMORY")

    # drop_table(cursor, "TERMS")
    # drop_table(cursor, "INVERTED_INDEX")

    # insert_query(cursor, CRETE_TERMS_TABLE)
    # insert_query(cursor, CREATE_INVERTED_INDEX_TABLE)
    # connection.commit()

    # files = sorted(os.listdir(BLOCK_DIR))
    # term_id_cache = {}
    # for i, f in enumerate(files):
    #     print(f"On file {i + 1}/{len(files)}")
    #     data = open_pickle(os.path.join(BLOCK_DIR, f))

    #     # Bulk insert unseen terms first; SQLite ignores terms that already exist.
    #     new_terms = [(term,) for term in data if term not in term_id_cache]
    #     if new_terms:
    #         cursor.executemany(INSERT_TERM_QUERY, new_terms)
    #         connection.commit()

    #     postings_batch = []
    #     for term in data:
    #         if term in term_id_cache:
    #             term_id = term_id_cache[term]
    #         else:
    #             res = fetch_query(cursor, SELECT_TERM_ID, (term, ))
    #             term_id = res[0][0]
    #             term_id_cache[term] = term_id

    #         for (doc_id, word_freq) in data[term]:
    #             postings_batch.append((term_id, doc_id, word_freq))

    #     if postings_batch:
    #         cursor.executemany(INSERT_INVERTED_INDEX, postings_batch)
    #     connection.commit()
    #     del data
    #     gc.collect()

    # cursor.execute("CREATE INDEX IF NOT EXISTS idx_terms_term ON TERMS(term)")
    # cursor.execute("CREATE INDEX IF NOT EXISTS idx_inverted_term_doc ON INVERTED_INDEX(term_id, doc_id)")
    # connection.commit()
    # connection.close()
