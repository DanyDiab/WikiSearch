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
import xml.etree.ElementTree as ET

from collections import Counter

CWD = os.getcwd()
DUMP_DIR = os.path.join(CWD, "wikidump")

doc_map: dict[str, int] = {}
link_graph: dict[int, list[int]] = {}
# word -> {docID: Frequency}
inverted_index: dict[str, dict[int, int]] = {}
document_lengths: dict[int, int] = {}


def parse_page(elem: ET.Element):
    if elem.find("./{*}redirect") is not None:
        return

    title = elem.find("./{*}title").text.lower()
    ns = elem.find("./{*}ns").text
    doc_id = elem.find("./{*}id").text
    revision = elem.find("./{*}revision")

    text_elem = revision.find("./{*}text")
    text = text_elem.text

    if title not in doc_map:
        doc_map[title] = doc_id

    words = re.findall(r"[a-zA-Z]+", text.lower())
    count = Counter(words)

    links = re.findall(r"\[\[(.*?)\]\]", text.lower())
    print(links)
    cleaned_links = [
        link.split("|")[0]
        for link in links
        if ":" not in link
    ]


for event, elem in ET.iterparse(os.path.join(DUMP_DIR, "a.xml"), events=("start", "end")):
    if elem.tag.endswith("page"):
        parse_page(elem)
