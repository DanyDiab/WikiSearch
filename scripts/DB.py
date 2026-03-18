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

def create_table(name: str):
    query = f"CREATE TABLE IF NOT EXISTS {name} (DOC_ID INTEGER NOT NULL, WORD_COUNT INTEGER NOT NULL)"
    db.executeQuery(query)

def drop_Table(name: str):
    query = f"DROP TABLE IF EXISTS {name}"
    db.executeQuery(query)

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

drop_Table(docLengthTable)
create_table(docLengthTable)

picklePath = PicklePaths / "document_lengths.pkl"
insertAllValues(docLengthTable,picklePath)

# res = selectValuesFromID(docLengthTable, 27097632)


# for val in res:
#     print(val)


    # 470