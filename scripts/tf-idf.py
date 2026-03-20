import nltk
# NOTE WHEN FIRST RUNNING MAKE SURE TO RUN THIS!!!!!!!!!!!!!!
# nltk.download('words')
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
from nltk.corpus import words
import db

english_dict = set(words.words())


def isWordValid(word):
    return word.lower() in english_dict

# TF
def calculateTermFrequency(database: db.Database):
    docQuery = f"SELECT * FROM {db.DOCUMENTS_TABLE}"
    docIDs = database.executeQuery(docQuery)

    docLenQuery = f"SELECT * FROM {db.DOC_LENGTH_TABLE}"
    docLens = database.executeQuery(docLenQuery)

    termsQuery = f"SELECT * FROM {db.TERMS_TABLE}"
    terms = database.executeQuery(termsQuery)
    

    print(f"searching inverted index for {docIDs[0][1]}")
    invertedQuery = f"SELECT * FROM {db.INVERTED_INDEX_TABLE} WHERE DOC_ID == {docIDs[0][1]}"
    res = database.executeQuery(invertedQuery)
    print(res)

def main():
    database = db.Database()
    calculateTermFrequency(database=database)

if __name__ == "__main__":
    main()
