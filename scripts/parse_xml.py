"""

Visualize Representation of how to Parse the Files:

PARSE-PAGE

get title
get docID
get Text

doc_map[title] = docID

extract links = graph

tokenize test = words

update inverted index

doc_length[docID] = total_words

"""
import os
import re
import pickle
import xml.etree.ElementTree as ET

from collections import Counter

block_id = 0
BLOCK_SIZE = 50_000

CWD = os.getcwd()
DUMP_DIR = os.path.join(CWD, "wikidump")
BLOCK_DIR = os.path.join(CWD, "block_dir")
os.makedirs(BLOCK_DIR, exist_ok=True)

WORD_RE = re.compile(r"[a-zA-Z]+")
LINK_RE = re.compile(r"\[\[(.*?)\]\]")
PAGE_TAG = "{http://www.mediawiki.org/xml/export-0.11/}page"

def parse_page(
    elem: ET.Element,
    doc_map: list[tuple[str, int]],
    link_graph: dict[int, list[str]],
    inverted_index: dict[str, list[tuple[int, int]]],
    document_lengths: dict[int, int]
) -> bool:
    if elem.find("./{*}redirect") is not None:
        return False
    if elem.find("./{*}ns").text != "0":
        return False

    title = elem.find("./{*}title").text.lower()
    doc_id = int(elem.find("./{*}id").text)
    revision = elem.find("./{*}revision")

    text_elem = revision.find("./{*}text")
    text = text_elem.text or ""
    text = text.lower()

    doc_map.append((title, doc_id))

    words = WORD_RE.findall(text)
    count = Counter(words)

    for word, freq in count.items():
        if word not in inverted_index:
            inverted_index[word] = []

        inverted_index[word].append((doc_id, freq))

    links = LINK_RE.findall(text)

    cleaned_links = {
        link.split("|")[0]
        for link in links
        if ":" not in link
    }

    cleaned_links_list = list(cleaned_links)

    link_graph[doc_id] = cleaned_links_list

    document_lengths[doc_id] = len(words)

    return True



def write_block(inverted_index: dict[str, list[tuple[int, int]]]):
    global block_id

    filename = f"index_block_{block_id}.pkl"
    sorted_block = {}

    for word in sorted(inverted_index):
        inverted_index[word].sort()
        sorted_block[word] = inverted_index[word]

    with open(os.path.join(BLOCK_DIR, filename), "wb") as p:
        pickle.dump(sorted_block, p)

    inverted_index.clear()
    block_id += 1



def read_xml_file(
    filename: str,
    doc_map: list[tuple[str, int]],
    link_graph: dict[int, list[str]],
    inverted_index: dict[str, list[tuple[int, int]]],
    document_lengths: dict[int, int],
):
    doc_counter = 0

    for _, elem in ET.iterparse(filename, events=("end",)):
        if elem.tag == PAGE_TAG:
            result = parse_page(
                elem,
                doc_map,
                link_graph,
                inverted_index,
                document_lengths
            )
            elem.clear()

            if result:
                doc_counter += 1

            if result and doc_counter % BLOCK_SIZE == 0:
                write_block(inverted_index)

    if inverted_index:
        write_block(inverted_index)
