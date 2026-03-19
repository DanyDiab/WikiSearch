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
    DOC_IDs = f"SELECT DOC_ID FROM {db.DOCUMENTS_TABLE}"
    DOC_IDs = database.executeQuery(DOC_IDs)
    for docID in DOC_IDs:
        # theres gotta be a more efficient way


def main():
    database = db.Database()
    calculateTermFrequency(database=database)


if __name__ == "__main__":
    main()
