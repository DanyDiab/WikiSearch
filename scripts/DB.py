import json
import pickle
import sqlite3
from enum import IntEnum
import os
from pathlib import Path

baseDIR = Path(__file__).parent.parent
DATABASE_DIR = baseDIR / "databases"
wikiDBPath = DATABASE_DIR / "wiki.db"
PicklePaths =  baseDIR / "wikidump" / "data"

documentsTable = "DOCUMENTS"
docLengthTable = "DOC_LENGTHS"
linkTable = "LINKS"


def extractPickle(filePath: str):
    with open(filePath, "rb") as p:
        return pickle.load(p)

class Database:
    def __init__(self):
        self.connection = self.getConnection()
        self.cursor = self.connection.cursor()

    def getConnection(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(wikiDBPath)

    def executeQuery(self, query, params=()):
        res = self.cursor.execute(query, params)
        return res.fetchall()

db = Database()

def create_table(name: str, fields: str):
    query = f"CREATE TABLE IF NOT EXISTS {name} {fields} "
    db.executeQuery(query)

def drop_Table(name: str):
    query = f"DROP TABLE IF EXISTS {name}"
    db.executeQuery(query)
    db.connection.commit()
    print(f"Dropped {name}")

def selectValuesFromTitle(table: str, search: str):
    query = f"""
    SELECT * FROM {table} WHERE TITLE LIKE ?
    """
    search_term = f"%{search}%"
    return db.executeQuery(query,params=(search_term,))

def selectValuesFromID(table: str, id: int):
    query = f"SELECT * FROM {table} WHERE DOC_ID == ?"
    return db.executeQuery(query=query, params=(id,))

def showEntireTable(table: str):
    query = f"SELECT * FROM {table}"
    return db.executeQuery(query=query)

def showTablesInDatabase():
    query = "SELECT name FROM sqlite_master WHERE type='table'"
    return db.executeQuery(query)


def insertAllValues(table: str, picklePath: str):
    insert_query = f"""INSERT INTO {table} (
        DOC_ID,
        WORD_COUNT
    ) VALUES (?, ?)"""

    chunkSize = 100_000
    data = extractPickle(picklePath)
    for i, (key, value) in enumerate(data.items()):
        db.executeQuery(query=insert_query, params=(key, value))
        if i % chunkSize == 0 and i != 0:
            db.connection.commit()
            print(f"Commited {i}")

    db.connection.commit()

# this clears the database, like garbage collection, use after dropping tables or other big changes removing elements
def vacuumDatabase():
    query = "VACUUM"
    db.executeQuery(query)
    print("Database vacuumed")


def createTablesAndInsertValues():
    create_table(documentsTable, "(TITLE TEXT, DOC_ID INTEGER PRIMARY KEY NOT NULL)")
    docMapPickle = PicklePaths / "doc_map.pkl"
    insertAllValues(documentsTable,docMapPickle)

    create_table(docLengthTable, "(DOC_ID INTEGER PRIMARY KEY NOT NULL, WORD_COUNT INTEGER NOT NULL)")
    docLengthPickle = PicklePaths / "document_lengths.pkl"
    insertAllValues(docLengthTable,docLengthPickle)

    create_table(linkTable, "SOURCE_DOC_ID INTEGER NOT NULL, TARGET_DOC_ID INTEGER NOT NULL, PRIMARY KEY (SOURCE_DOC_ID, TARGET_DOC_ID)")
    linkPickle = PicklePaths / "link_graph.pkl"

# NOTE
# When Building document table, the doc ID is 2nd
# When Building Doc Length table, the doc ID is 1st








    # 470