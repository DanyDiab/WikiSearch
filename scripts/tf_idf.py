from re import search
from db import Database, DOC_LENGTH_TABLE, INVERTED_INDEX_TABLE, DOCUMENTS_TABLE, LINKS_TABLE
import nltk
from nltk.corpus import words, stopwords, wordnet
from nltk.stem import WordNetLemmatizer

# nltk.download('wordnet')

english_dict = set(words.words())
stop_words = set(stopwords.words())

pageLengthFilter = 500
numToReturn = 200

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


def getCandiadatePages(search_query: str) -> tuple[list, list]:
    db = Database()
    normalized_query = search_query.lower()
    # filter query for stop words
    cleaned_query = extract_base_words(normalized_query=normalized_query,stop_words=stop_words)
    in_query = ",".join(f"'{t}'" for t in cleaned_query)
    query = f"""
        WITH TF_IDF AS(
            SELECT
                dm.doc_id
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
            ORDER BY SUM((i.word_count * 1.0 / dl.page_length) * idf.idf) DESC
            LIMIT {numToReturn}
        )
        SELECT
            DISTINCT l.doc_id,
            dm.page_name
            FROM {LINKS_TABLE} l
            JOIN {DOCUMENTS_TABLE} dm ON dm.doc_id = l.doc_id
            WHERE
            l.doc_id IN TF_IDF OR
            l.link_id IN TF_IDF
    """

    res = db.executeQuery(query)
    stringRes = ",".join(str(doc_id[0]) for doc_id in res)
    links = getLinks(docIDs=stringRes,db=db)
    return (res,links)


def getLinks(docIDs: list, db: Database):
    query = f"""SELECT * FROM {LINKS_TABLE} WHERE doc_id IN ({docIDs}) AND link_id IN ({docIDs})"""
    res = db.executeQuery(query=query)
    return res

def main():

    getCandiadatePages("obama")

if __name__ == "__main__":
    main()
