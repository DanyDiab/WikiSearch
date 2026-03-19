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
    query = f"CREATE TABLE IF NOT EXISTS {name} ({fields})"
    db.executeQuery(query)
    print(f"created {name}")

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


def insertAllValues(table: str, picklePath: str, fields: tuple):
    insert_query = f"""INSERT INTO {table} (
        {fields[0]},
        {fields[1]}
    ) VALUES (?, ?)"""

    chunkSize = 100_000
    data = extractPickle(picklePath)
    for i, (key, value) in enumerate(data.items()):
        db.executeQuery(query=insert_query, params=(key, value))
        if i % chunkSize == 0 and i != 0:
            db.connection.commit()
            print(f"Commited {i}\r", end="")
    db.connection.commit()
    print(f"insert complete into {table}")


def insertAllValuesArray(table: str, picklePath: str, fields: tuple):
    insert_query = f"""INSERT INTO {table} (
    {fields[0]},
    {fields[1]}
    ) VALUES (?, ?)"""

    chunkSize = 100_000
    data = extractPickle(picklePath)
    counter = 0
    for key, values in data.items():
        for value in values:
            db.executeQuery(query=insert_query, params=(key, value))
            if counter % chunkSize == 0 and counter != 0:
                db.connection.commit()
                print(f"Commited {counter}\r", end="")
            counter+=1
    
    db.connection.commit()
    print(f"insert complete into {table}")


# this clears the database, like garbage collection, use after dropping tables or other big changes removing elements
def vacuumDatabase():
    query = "VACUUM"
    db.executeQuery(query)
    print("Database vacuumed")

def dropAllTables():
    drop_Table(documentsTable)
    drop_Table(docLengthTable)
    drop_Table(linkTable)
    vacuumDatabase()

def createTablesAndInsertValues():
    docID = "DOC_ID"
    title = "TITLE"
    wordCount = "WORD_COUNT"
    sourceDocId = "SOURCE_DOC_ID"
    targetDocId = "TARGET_DOC_ID"
    create_table(documentsTable, f"{title} TEXT, {docID} INTEGER PRIMARY KEY NOT NULL")
    docMapPickle = PicklePaths / "doc_map.pkl"
    insertAllValues(documentsTable,docMapPickle, (title,docID))
    
    create_table(docLengthTable, f"{docID} INTEGER PRIMARY KEY NOT NULL, {wordCount} INTEGER NOT NULL")
    docLengthPickle = PicklePaths / "document_lengths.pkl"
    insertAllValues(docLengthTable,docLengthPickle, (docID,wordCount))

    create_table(linkTable, f"{sourceDocId} INTEGER NOT NULL, {targetDocId} INTEGER NOT NULL, PRIMARY KEY ({sourceDocId}, {targetDocId})")
    linkPickle = PicklePaths / "link_graph.pkl"
    insertAllValuesArray(linkTable,linkPickle, (sourceDocId, targetDocId))




def printCoolStats():
        # query = """SELECT 
    #     AVG(link_count) AS avg_outbound_links,
    #     MAX(link_count) AS max_outbound_links
    # FROM (
    #     SELECT SOURCE_DOC_ID, COUNT(TARGET_DOC_ID) AS link_count 
    #     FROM LINKS 
    #     GROUP BY SOURCE_DOC_ID
    # );"""
    # res = db.executeQuery(query=query)
    # print(res)
    outboundQuery = """SELECT 
        d.TITLE, 
        COUNT(l.TARGET_DOC_ID) AS link_count
    FROM LINKS l
    JOIN DOCUMENTS d ON l.SOURCE_DOC_ID = d.DOC_ID
    GROUP BY l.SOURCE_DOC_ID
    ORDER BY link_count DESC
    LIMIT 10;"""

    res = db.executeQuery(query=outboundQuery)

    print("articles pointing the most other articles")
    for val in res:
        print(val)


    inBoundQuery = """SELECT 
        d.TITLE, 
        top_links.inbound_link_count
    FROM (
        SELECT TARGET_DOC_ID, COUNT(SOURCE_DOC_ID) AS inbound_link_count
        FROM LINKS
        GROUP BY TARGET_DOC_ID
        ORDER BY inbound_link_count DESC
        LIMIT 10
    ) AS top_links
    JOIN DOCUMENTS d ON top_links.TARGET_DOC_ID = d.DOC_ID;"""

    res = db.executeQuery(query=inBoundQuery)

    print("top hubs")
    for val in res:
        print(val)


# dropAllTables()
# createTablesAndInsertValues()


# NOTE
# When Building document table, the doc ID is 2nd
# When Building Doc Length table, the doc ID is 1st
# 470