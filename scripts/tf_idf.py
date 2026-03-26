from db import Database, DOC_LENGTH_TABLE, INVERTED_INDEX_TABLE, DOCUMENTS_TABLE, LINKS_TABLE
import nltk
from nltk.corpus import words, stopwords, wordnet
from nltk.stem import WordNetLemmatizer

nltk.download('wordnet')
# nltk.download('averaged_perceptron_tagger_eng')

english_dict = set(words.words())
stop_words = set(stopwords.words())

pageLengthFilter = 500
numToReturn = 20

def isWordValid(word):
    if english_dict is None:
        raise RuntimeError("nltk is not installed")
    return word.lower() in english_dict

def get_wordnet_pos(treebank_tag: str) -> str:
    if treebank_tag.startswith('J'): return wordnet.ADJ
    elif treebank_tag.startswith('V'): return wordnet.VERB
    elif treebank_tag.startswith('N'): return wordnet.NOUN
    elif treebank_tag.startswith('R'): return wordnet.ADV
    else: return wordnet.NOUN

def extract_base_words(normalized_query: str, stop_words: set[str]) -> list[str]:
    filtered_query: list[str] = [word for word in normalized_query.split() if word not in stop_words]
    pos_tags: list[tuple[str, str]] = nltk.pos_tag(filtered_query)
    lemmatizer: WordNetLemmatizer = WordNetLemmatizer()
    
    cleaned_query: list[str] = []
    
    for word, tag in pos_tags:
        wordnet_pos: str = get_wordnet_pos(tag)
        base_word: str = lemmatizer.lemmatize(word, pos=wordnet_pos)
        cleaned_query.append(base_word)
        
    return cleaned_query


def getCandiadatePages(search_query: str) -> dict[int, list[int]]:
    db = Database()
    normalized_query = search_query.lower()
    # filter query for stop words
    filtered_query: list[str] = [word for word in normalized_query.split() if word not in stop_words]
    num_terms = len(filtered_query)
    in_query = ",".join(f"'{t}'" for t in filtered_query)
    query = f"""
        WITH TF_IDF AS(
            SELECT
                dm.doc_id,
                SUM((i.word_count * 1.0 / dl.page_length) * idf.idf) AS tf_idf_score
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
            HAVING COUNT(DISTINCT t.term) = {num_terms}
            ORDER BY SUM((i.word_count * 1.0 / dl.page_length) * idf.idf) DESC
            LIMIT {numToReturn}
        )
        SELECT DISTINCT
            l.doc_id,
            l.link_id,
            t1.tf_idf_score AS source_doc_score,
            t2.tf_idf_score AS link_doc_score
        FROM {LINKS_TABLE} l
        LEFT JOIN TF_IDF t1 ON l.doc_id = t1.doc_id
        LEFT JOIN TF_IDF t2 ON l.link_id = t2.doc_id
        WHERE
            t1.doc_id IS NOT NULL
            OR t2.doc_id IS NOT NULL
    """

    res = db.executeQuery(query)

    base_set = {}
    scores = {}
    for doc_id, link_id, source_doc_score, link_doc_score in res:
        if doc_id not in base_set:
            base_set[doc_id] = []
        if link_id not in base_set:
            base_set[link_id] = []
        base_set[doc_id].append(link_id)

        if source_doc_score is not None:
            scores[doc_id] = source_doc_score
            
        if link_doc_score is not None:
            scores[link_id] = link_doc_score
        

    return base_set, scores

def main():
    getCandiadatePages("obama")

if __name__ == "__main__":
    main()
