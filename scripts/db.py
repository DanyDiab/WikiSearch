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
INVERTED_INDEX_TABLE = "INVERTED_INDEX"
TERMS_TABLE = "TERMS"


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
    

    def combineDataBaseTables(self):
        db.executeQuery(f"ATTACH DATABASE '{WIKI_DB}' AS dany_db")

        db.executeQuery("PRAGMA synchronous = OFF")
        db.executeQuery("PRAGMA journal_mode = MEMORY")
        db.executeQuery("PRAGMA cache_size = 100000")

        self.drop_table(DOCUMENTS_TABLE)
        self.drop_table(DOC_LENGTH_TABLE)
        self.drop_table(LINKS_TABLE)

        Docquery = f"CREATE TABLE {DOCUMENTS_TABLE} AS SELECT * FROM dany_db.{DOCUMENTS_TABLE}" 
        DocLenQuery = f"CREATE TABLE {DOC_LENGTH_TABLE} AS SELECT * FROM dany_db.{DOC_LENGTH_TABLE}" 
        LinksQuery = f"CREATE TABLE {LINKS_TABLE} AS SELECT * FROM dany_db.{LINKS_TABLE}" 

        db.executeQuery(query=Docquery)
        db.executeQuery(query=DocLenQuery)
        db.executeQuery(query=LinksQuery)
        
        db.connection.commit()
        db.executeQuery("DETACH DATABASE dany_db")

    # def selectValuesFromTitle(self, table: str, search: str):
    #     query = f"""
    #     SELECT * FROM {table} WHERE TITLE LIKE ?
    #     """
    #     search_term = f"%{search}%"
    #     return db.executeQuery(query,params=(search_term,))

    # def selectValuesFromID(table: str, id: int):
    #     query = f"SELECT * FROM {table} WHERE DOC_ID == ?"
    #     return db.executeQuery(query=query, params=(id,))

    # def showTablesInDatabase(self):
    #     query = "SELECT name FROM sqlite_master WHERE type='table'"
    #     return db.executeQuery(query)
    
# this clears the database, like garbage collection, use after dropping tables or other big changes removing elements
    def vacuumDatabase(self):
        query = "VACUUM"
        db.executeQuery(query)
        print("Database vacuumed")

    def dropAllTables(self):
        self.drop_table(DOCUMENTS_TABLE)
        self.drop_table(DOC_LENGTH_TABLE)
        self.drop_table(LINKS_TABLE)
        self.vacuumDatabase()

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
    # files = sorted(os.listdir(PICKLE_FILES))
    db = Database()
    
    # print(db.executeQuery("SELECT * FROM TERMS LIMIT 100"))
    # query = "CREATE INDEX idx_inverted_doc_id ON INVERTED_INDEX(doc_id);"
    # db.executeQuery(query=query)
    # for f in files:
    #     print(f"On file: {f}")
    #     file_path = os.path.join(PICKLE_FILES, f)

    #     if 'doc_map' in f:
    #         push_doc_map_into_db(db, file_path)
    #     elif 'lengths' in f:
    #         push_doc_lengths_into_db(db, file_path)
    #     else:
    #         push_link_graph_to_db(db, file_path)
