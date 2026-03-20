from db import Database, DOC_LENGTH_TABLE, INVERTED_INDEX_TABLE, DOCUMENTS_TABLE

try:
    # Optional dependency for word validation helpers.
    from nltk.corpus import words
    english_dict = set(words.words())
except ModuleNotFoundError:
    english_dict = None


def isWordValid(word):
    if english_dict is None:
        raise RuntimeError("nltk is not installed")
    return word.lower() in english_dict

# TF
def calculateTermFrequency(db: Database):
    # docQuery = f"SELECT * FROM {db.DOCUMENTS_TABLE}"
    # docIDs = database.executeQuery(docQuery)

    # docLenQuery = f"SELECT * FROM {db.DOC_LENGTH_TABLE}"
    # docLens = database.executeQuery(docLenQuery)

    # termsQuery = f"SELECT * FROM {db.TERMS_TABLE}"
    # terms = database.executeQuery(termsQuery)
    

    # print(f"searching inverted index for {docIDs[0][1]}")
    term = "algorithm"
    query = f"""
    SELECT
        dm.page_name,
        (i.word_count * 1.0 / dl.page_length) * idf.idf AS tf_idf,
        i.word_count,
        dl.page_length
    FROM {INVERTED_INDEX_TABLE} i
    JOIN TERMS t ON t.term_id = i.term_id
    JOIN {DOC_LENGTH_TABLE} dl ON dl.doc_id = i.doc_id
    JOIN {DOCUMENTS_TABLE} dm ON dm.doc_id = i.doc_id
    CROSS JOIN (
        SELECT
            LOG(
                (SELECT COUNT(*) FROM {DOC_LENGTH_TABLE}) * 1.0 /
                COUNT(DISTINCT i2.doc_id)
            ) AS idf
        FROM {INVERTED_INDEX_TABLE} i2
        JOIN TERMS t2 ON t2.term_id = i2.term_id
        WHERE t2.term = '{term}'
    ) AS idf
    WHERE t.term = '{term}'
    AND dl.page_length > 500
    ORDER BY tf_idf DESC
    LIMIT 100
    """


    # query = f"""
    #     SELECT dm.page_name, i.word_count, dl.page_length, i.doc_id
    #     FROM {INVERTED_INDEX_TABLE} i
    #     JOIN {DOC_LENGTH_TABLE} dl ON dl.doc_id = i.doc_id
    #     JOIN TERMS t ON t.term_id = i.term_id
    #     JOIN {DOCUMENTS_TABLE} dm ON dm.doc_id = i.doc_ido 'algorithm' AND dm.page_name = 'multi-digit multiplication'
    # """

    # | doc_id | word_count | term_id JOIN term | 

    # query = f"""
    # SELECT t.term, i.word_count
    # FROM {INVERTED_INDEX_TABLE} i
    # JOIN TERMS t ON t.term_id = i.term_id
    # WHERE i.doc_id = 81251898
    # """
    res = db.executeQuery(query)
    for val in res:
        print(val)



def main():
    database = Database()
    calculateTermFrequency(db=database)

if __name__ == "__main__":
    main()
