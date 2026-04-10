import re
import xml.etree.ElementTree as ET
from codecs import getincrementaldecoder
from collections import Counter
from typing import Iterable, Iterator

WORD_RE = re.compile(r"[a-zA-Z]+")
LINK_RE = re.compile(r"\[\[(.*?)\]\]")
REDIRECT_RE = re.compile(r"^\s*#redirect\s*:?\s*\[\[", re.IGNORECASE)
PAGE_TAG = "{http://www.mediawiki.org/xml/export-0.11/}page"


def normalize_link_title(raw_link: str) -> str | None:
    title = raw_link.split("|")[0].strip().lower()
    if not title or ":" in title:
        return None
    return title


def parse_page(elem: ET.Element):
    if elem.find("./{*}redirect") is not None:
        return None

    namespace = elem.find("./{*}ns")
    if namespace is None or namespace.text != "0":
        return None

    revision = elem.find("./{*}revision")
    if revision is None:
        return None

    text_elem = revision.find("./{*}text")
    text = (text_elem.text or "") if text_elem is not None else ""
    if REDIRECT_RE.match(text):
        return None

    title_elem = elem.find("./{*}title")
    id_elem = elem.find("./{*}id")
    if title_elem is None or id_elem is None or title_elem.text is None or id_elem.text is None:
        return None

    normalized_text = text.lower()
    normalized_title = title_elem.text.lower()
    doc_id = int(id_elem.text)

    word_counts = Counter(WORD_RE.findall(normalized_text))
    cleaned_links = {
        normalized_link
        for normalized_link in (
            normalize_link_title(link)
            for link in LINK_RE.findall(normalized_text)
        )
        if normalized_link is not None
    }

    return {
        "doc_id": doc_id,
        "title": normalized_title,
        "page_length": sum(word_counts.values()),
        "word_counts": word_counts,
        "links": cleaned_links,
    }


def iter_documents(filename: str) -> Iterator[dict]:
    for _, elem in ET.iterparse(filename, events=("end",)):
        if elem.tag != PAGE_TAG:
            continue

        parsed_page = parse_page(elem)
        elem.clear()

        if parsed_page is not None:
            yield parsed_page


def iter_documents_from_chunks(chunks: Iterable[bytes]) -> Iterator[dict]:
    parser = ET.XMLPullParser(events=("end",))
    decoder = getincrementaldecoder("utf-8")()

    for chunk in chunks:
        if not chunk:
            continue

        parser.feed(decoder.decode(chunk))
        for _, elem in parser.read_events():
            if elem.tag != PAGE_TAG:
                continue

            parsed_page = parse_page(elem)
            elem.clear()

            if parsed_page is not None:
                yield parsed_page

    tail = decoder.decode(b"", final=True)
    if tail:
        parser.feed(tail)

    parser.close()
    for _, elem in parser.read_events():
        if elem.tag != PAGE_TAG:
            continue

        parsed_page = parse_page(elem)
        elem.clear()

        if parsed_page is not None:
            yield parsed_page
