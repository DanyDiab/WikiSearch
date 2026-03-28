from db import Database, DOC_LENGTH_TABLE, DOCUMENTS_TABLE, INVERTED_INDEX_TABLE, LINKS_TABLE
import heapq
import nltk
import re
from nltk.corpus import words, stopwords, wordnet
from nltk.stem import WordNetLemmatizer

# nltk.download('wordnet')
# nltk.download('averaged_perceptron_tagger_eng')

english_dict = set(words.words())
stop_words = set(stopwords.words())

pageLengthFilter = 500
numToReturn = 20
candidatePoolSize = 1000
lemmatizer = WordNetLemmatizer()

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
    
    cleaned_query: list[str] = []
    
    for word, tag in pos_tags:
        wordnet_pos: str = get_wordnet_pos(tag)
        base_word: str = lemmatizer.lemmatize(word, pos=wordnet_pos)
        cleaned_query.append(base_word)
        
    return cleaned_query


def normalize_text(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [
        lemmatizer.lemmatize(token)
        for token in tokens
        if token not in stop_words
    ]


def contains_subsequence(values: list[str], target: list[str]) -> bool:
    if not target or len(target) > len(values):
        return False

    last_index = len(values) - len(target) + 1
    for start in range(last_index):
        if values[start:start + len(target)] == target:
            return True

    return False


def get_title_boost(page_name: str, normalized_query_tokens: list[str]) -> float:
    normalized_title_tokens = normalize_text(page_name)
    if not normalized_query_tokens or not normalized_title_tokens:
        return 0.0

    title_token_set = set(normalized_title_tokens)
    matched_terms = sum(1 for token in normalized_query_tokens if token in title_token_set)
    if matched_terms == 0:
        return 0.0

    coverage = matched_terms / len(normalized_query_tokens)
    extra_terms = max(0, len(normalized_title_tokens) - matched_terms)

    title_boost = coverage * 2.0
    if coverage == 1.0:
        title_boost += 2.0
    if contains_subsequence(normalized_title_tokens, normalized_query_tokens):
        title_boost += 3.0
    if normalized_title_tokens == normalized_query_tokens:
        title_boost += 4.0

    title_boost -= min(extra_terms, 10) * 0.15
    return title_boost


def getCandiadatePages(search_query: str) -> dict[int, list[int]]:
    db = Database()
    normalized_query = search_query.lower()
    # filter query for stop words
    filtered_query: list[str] = [word for word in normalized_query.split() if word not in stop_words]
    if not filtered_query:
        return {}, {}

    num_terms = len(filtered_query)
    in_query = ",".join(f"'{t}'" for t in filtered_query)
    query = f"""
        SELECT
            d.doc_id,
            d.page_name,
            SUM(i.tf_idf) AS tf_idf_score
        FROM {INVERTED_INDEX_TABLE} i
        JOIN TERMS t ON t.term_id = i.term_id
        JOIN {DOC_LENGTH_TABLE} dl ON dl.doc_id = i.doc_id
        JOIN {DOCUMENTS_TABLE} d ON d.doc_id = i.doc_id
        WHERE
            t.term IN ({in_query})
            AND dl.page_length > {pageLengthFilter}
            AND i.tf_idf IS NOT NULL
        GROUP BY d.doc_id
        HAVING COUNT(DISTINCT t.term) = {num_terms}
        ORDER BY tf_idf_score DESC
        LIMIT {candidatePoolSize}
    """

    candidate_rows = db.executeQuery(query)
    normalized_query_tokens = normalize_text(search_query)

    top_seed_pages = []
    for doc_id, page_name, tf_idf_score in candidate_rows:
        seed_score = tf_idf_score + get_title_boost(page_name, normalized_query_tokens)
        if len(top_seed_pages) < numToReturn:
            heapq.heappush(top_seed_pages, (seed_score, doc_id))
        elif seed_score > top_seed_pages[0][0]:
            heapq.heapreplace(top_seed_pages, (seed_score, doc_id))

    ranked_seed_pages = sorted(top_seed_pages, reverse=True)
    tf_idf_mult = {
        doc_id: score
        for score, doc_id in ranked_seed_pages
    }

    total = sum(tf_idf_mult.values())
    if total > 0:
        tf_idf_mult = {
            key: (1 / max(1e-9, 1 - (val / total)))
            for key, val in tf_idf_mult.items()
        }

    if not tf_idf_mult:
        return {}, {}

    seed_doc_ids = ",".join(str(doc_id) for _, doc_id in ranked_seed_pages)
    link_query = f"""
        SELECT DISTINCT
            l.doc_id,
            l.link_id
        FROM {LINKS_TABLE} l
        WHERE l.doc_id IN ({seed_doc_ids})

        UNION

        SELECT DISTINCT
            l.doc_id,
            l.link_id
        FROM {LINKS_TABLE} l
        WHERE l.link_id IN ({seed_doc_ids})
    """

    res = db.executeQuery(link_query)

    base_set = {}
    for doc_id, link_id in res:
        if doc_id not in base_set:
            base_set[doc_id] = []
        if link_id not in base_set:
            base_set[link_id] = []
        base_set[doc_id].append(link_id)

    return base_set, tf_idf_mult

def main():
    getCandiadatePages("obama")

if __name__ == "__main__":
    main()
