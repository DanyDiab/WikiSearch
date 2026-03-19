import os
import pickle
import sqlite3
from pathlib import Path

baseDIR = Path(__file__).parent.parent
DATABASE_DIR = baseDIR / "database"
WIKI_DB = DATABASE_DIR / "wiki.db"
PICKLE_FILES =  baseDIR / "wikidump" / "data"

DOCUMENTS_TABLE = "DOCUMENTS"
DOC_LENGTH_TABLE = "DOC_LENGTHS"
LINKS_TABLE = "LINKS"


def open_pickle(filePath: str):
    with open(filePath, "rb") as p:
        return pickle.load(p)



class Database:
    def __init__(self):
        self.connection = self.getConnection()
        self.cursor = self.connection.cursor()



    def commit(self):
        self.connection.commit()



    def getConnection(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(WIKI_DB)



    def executeQuery(self, query, params=()):
        res = self.cursor.execute(query, params)
        return res.fetchall()



    def execute_many(self, query, data):
        self.cursor.executemany(query, data)



    def create_table(self, table_name: str, fields: str):
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {fields}
        )
        """
        self.executeQuery(query)
        self.commit()



    def drop_table(self, table_name: str):
        query = f"DROP TABLE IF EXISTS {table_name}"
        self.executeQuery(query)
        self.commit()



# def selectValuesFromTitle(table: str, search: str):
#     query = f"""
#     SELECT * FROM {table} WHERE TITLE LIKE ?
#     """
#     search_term = f"%{search}%"
#     return db.executeQuery(query,params=(search_term,))

# def selectValuesFromID(table: str, id: int):
#     query = f"SELECT * FROM {table} WHERE DOC_ID == ?"
#     return db.executeQuery(query=query, params=(id,))

# def showEntireTable(table: str):
#     query = f"SELECT * FROM {table}"
#     return db.executeQuery(query=query)

# def showTablesInDatabase():
#     query = "SELECT name FROM sqlite_master WHERE type='table'"
#     return db.executeQuery(query)


# def insertAllValues(table: str, picklePath: str, fields: tuple):
#     insert_query = f"""INSERT INTO {table} (
#         {fields[0]},
#         {fields[1]}
#     ) VALUES (?, ?)"""

#     chunkSize = 100_000
#     data = extractPickle(picklePath)
#     for i, (key, value) in enumerate(data.items()):
#         db.executeQuery(query=insert_query, params=(key, value))
#         if i % chunkSize == 0 and i != 0:
#             db.connection.commit()
#             print(f"Commited {i}\r", end="")
#     db.connection.commit()
#     print(f"insert complete into {table}")


# def insertAllValuesArray(table: str, picklePath: str, fields: tuple):
#     insert_query = f"""INSERT INTO {table} (
#     {fields[0]},
#     {fields[1]}
#     ) VALUES (?, ?)"""

#     chunkSize = 100_000
#     data = extractPickle(picklePath)
#     counter = 0
#     for key, values in data.items():
#         for value in values:
#             db.executeQuery(query=insert_query, params=(key, value))
#             if counter % chunkSize == 0 and counter != 0:
#                 db.connection.commit()
#                 print(f"Commited {counter}\r", end="")
#             counter+=1
    
#     db.connection.commit()
#     print(f"insert complete into {table}")


# # this clears the database, like garbage collection, use after dropping tables or other big changes removing elements
# def vacuumDatabase():
#     query = "VACUUM"
#     db.executeQuery(query)
#     print("Database vacuumed")

# def dropAllTables():
#     drop_Table(documentsTable)
#     drop_Table(docLengthTable)
#     drop_Table(linkTable)
#     vacuumDatabase()

# def createTablesAndInsertValues():
#     docID = "DOC_ID"
#     title = "TITLE"
#     wordCount = "WORD_COUNT"
#     sourceDocId = "SOURCE_DOC_ID"
#     targetDocId = "TARGET_DOC_ID"
#     create_table(documentsTable, f"{title} TEXT, {docID} INTEGER PRIMARY KEY NOT NULL")
#     docMapPickle = PicklePaths / "doc_map.pkl"
#     insertAllValues(documentsTable,docMapPickle, (title,docID))
    
#     create_table(docLengthTable, f"{docID} INTEGER PRIMARY KEY NOT NULL, {wordCount} INTEGER NOT NULL")
#     docLengthPickle = PicklePaths / "document_lengths.pkl"
#     insertAllValues(docLengthTable,docLengthPickle, (docID,wordCount))

#     create_table(linkTable, f"{sourceDocId} INTEGER NOT NULL, {targetDocId} INTEGER NOT NULL, PRIMARY KEY ({sourceDocId}, {targetDocId})")
#     linkPickle = PicklePaths / "link_graph.pkl"
#     insertAllValuesArray(linkTable,linkPickle, (sourceDocId, targetDocId))



def push_doc_map_into_db(db: Database, file_path: str):
    data = open_pickle(file_path)
    print("Loaded Data")

    insert_data = [
        (page_name, doc_id)
        for page_name, doc_id in data.items()
    ]

    db.drop_table(DOCUMENTS_TABLE)
    db.create_table(DOCUMENTS_TABLE, f"page_name TEXT, doc_id INTEGER PRIMARY KEY NOT NULL")

    query = f"""
    INSERT INTO {DOCUMENTS_TABLE} (
        page_name,
        doc_id
    ) 
    VALUES (?, ?)
    """

    db.execute_many(query, insert_data)
    db.commit()



def push_doc_lengths_into_db(db: Database, file_path: str):
    data = open_pickle(file_path)
    print("Loaded Data")

    insert_data = [
        (doc_id, page_length)
        for doc_id, page_length in data.items()
    ]

    db.drop_table(DOC_LENGTH_TABLE)
    db.create_table(DOC_LENGTH_TABLE, f"doc_id INTEGER PRIMARY KEY NOT NULL, page_length INTEGER")

    query = f"""
    INSERT INTO {DOC_LENGTH_TABLE} (
        doc_id,
        page_length
    )
    VALUES (?, ?)
    """
    db.execute_many(query, insert_data)
    db.commit()



def push_link_graph_to_db(db: Database, file_path: str):
    data = open_pickle(file_path)
    print("Loaded Data")

    insert_data = []
    for doc_id, link_ids in data.items():
        insert_data.extend([
            (doc_id, link_id)
            for link_id in link_ids
        ])

    db.drop_table(LINKS_TABLE)
    db.create_table(LINKS_TABLE, f"doc_id INTEGER, link_id INTEGER")

    query = f"""
    INSERT INTO {LINKS_TABLE} (
        doc_id,
        link_id
    )
    VALUES (?, ?)
    """
    db.execute_many(query, insert_data)
    db.commit()





if __name__ == '__main__':
    files = sorted(os.listdir(PICKLE_FILES))
    db = Database()

    for f in files:
        print(f"On file: {f}")
        file_path = os.path.join(PICKLE_FILES, f)

        if 'doc_map' in f:
            push_doc_map_into_db(db, file_path)
        elif 'lengths' in f:
            push_doc_lengths_into_db(db, file_path)
        else:
            push_link_graph_to_db(db, file_path)
