from re import search
from db import Database, DOC_LENGTH_TABLE, INVERTED_INDEX_TABLE, DOCUMENTS_TABLE
import nltk
from nltk.corpus import words, stopwords

# nltk.download("stopwords")

english_dict = set(words.words())
stop_words = set(stopwords.words())

pageLengthFilter = 500

def isWordValid(word):
    if english_dict is None:
        raise RuntimeError("nltk is not installed")
    return word.lower() in english_dict

def calculateTermFrequency(db: Database):
    search_query = "Mountains of the world"

    normalized_query = search_query.lower()
    filtered_query = [word for word in normalized_query.split() if word not in stop_words]
    in_query = ",".join(f"'{t}'" for t in filtered_query)
    query = f"""
        SELECT
            dm.doc_id,
            dm.page_name,
            SUM((i.word_count * 1.0 / dl.page_length) * idf.idf) AS tf_idf
        FROM {INVERTED_INDEX_TABLE} i
        JOIN TERMS t ON t.term_id = i.term_id
        JOIN {DOC_LENGTH_TABLE} dl ON dl.doc_id = i.doc_id
        JOIN {DOCUMENTS_TABLE} dm ON dm.doc_id = i.doc_id

        JOIN (
            SELECT
                t2.term,
                LOG(
                    (SELECT COUNT(*) FROM {DOC_LENGTH_TABLE}) * 1.0 /
                    COUNT(DISTINCT i2.doc_id)
                ) AS idf
            FROM {INVERTED_INDEX_TABLE} i2
            JOIN TERMS t2 ON t2.term_id = i2.term_id
            WHERE t2.term IN ({in_query})
            GROUP BY t2.term
        ) AS idf ON idf.term = t.term

        WHERE t.term IN ({in_query}) AND dl.page_length > {pageLengthFilter}

        GROUP BY dm.doc_id
        ORDER BY tf_idf DESC
        LIMIT 20
    """

    res = db.executeQuery(query)
    for val in res:
        print(val)



def main():
    database = Database()
    calculateTermFrequency(db=database)

if __name__ == "__main__":
    main()
