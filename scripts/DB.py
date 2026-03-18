import json
import pickle
import sqlite3
from enum import IntEnum

wikiDB = "wiki.db"
documentsTable = "DOCUMENTS"


class QueryType(IntEnum):
    GET = 1,
    COMMIT = 2,

def extractPickle():
    with open("/home/dany/Projects/wikisearch/WikiSearch/data/doc_map.pkl", "rb") as p:
        return pickle.load(p)

class Database:
    def __init__(self):
        self.connection = self.getConnection()
        self.cursor = self.connection.cursor()

    def getConnection(self):
        return sqlite3.connect(wikiDB)

    def executeQuery(self, query, params=()):
        res = self.cursor.execute(query, params)
        return res.fetchall()


db = Database()


createTable = f"""
CREATE TABLE IF NOT EXISTS {documentsTable}(
    DOC_ID INTEGER NOT NULL,
    TITLE TEXT
)
"""

insert_query = f"""
INSERT INTO {documentsTable} (
    DOC_ID,
    TITLE
) VALUES (?, ?)
"""


dropTable = f"""
DROP TABLE IF EXISTS {documentsTable} 
"""


selectQuery = f"""
SELECT * FROM {documentsTable} WHERE TITLE LIKE ?
"""

# db.executeQuery(query=createTable)
# db.connection.commit()


def selectValues(search):
    search_term = f"%{search}%"
    return db.executeQuery(selectQuery,params=(search_term,))
    # print(res)


def insertAllValues():
    data = extractPickle()

    for i, (key, value) in enumerate(data.items()):
        db.executeQuery(query=insert_query, params=(value, key))
        if i % 100_000 == 0 and i != 0:
            db.connection.commit()
            print(f"Commited {i}")

    db.connection.commit()


# insertAllValues()

values = selectValues("Dany")

for val in values:
    print(val)