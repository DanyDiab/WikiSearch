import os
import time
import pickle

from parse_xml import read_xml_file
from get_wiki_content import (
    unzipFile,
    downloadBZ2,
    get_page_aspect,
    get_page_content,
    getFileBytesSize,
    formatElapsedTime
)

CWD = os.getcwd()
DUMP_DIR = os.path.join(CWD, "wikidump")
METADATA_CHUNK_SIZE_BYTES = 50 * 1024 * 1024
METADATA_CHECK_INTERVAL = 100
DOC_MAP_PATH = os.path.join(CWD, "doc_map.pkl")
LINK_GRAPH_PATH = os.path.join(CWD, "link_graph.pkl")
DOCUMENT_LENGTHS_PATH = os.path.join(CWD, "document_lengths.pkl")

BZ2_INDEX = 3

doc_map: list[tuple[str, int]] = []
link_graph: dict[int, list[str]] = {}
inverted_index: dict[str, list[tuple[int, int]]] = {}
document_lengths: dict[int, int] = {}

def main():
    os.makedirs(DUMP_DIR, exist_ok=True)
    page_content = get_page_content()

    # getting the size of each of the bz2 that we will be downloading
    raw_wiki_dump_strings = get_page_aspect(page_content, "pre")
    cleaned_wiki_dump_strings: list[str] = str(raw_wiki_dump_strings).split("\n")[BZ2_INDEX : -1]
    wiki_dump_file_sizes = getFileBytesSize(cleaned_wiki_dump_strings)

    a_tags = get_page_aspect(page_content, "a")
    bz2_files = a_tags[BZ2_INDEX:]
    for i, tag in enumerate(bz2_files):
        filepath = os.path.join(DUMP_DIR, "download.xml.bz2")
        downloadBZ2(tag, wiki_dump_file_sizes[i], filepath)

        print("Download Complete")
        print("Now UnZipping File")
        unzipStartTime = time.perf_counter()
        unzipFile(filepath)
        unzipElapsedTime = time.perf_counter() - unzipStartTime
        print(f"Unzip took {formatElapsedTime(unzipElapsedTime)}")

        unzipped_file = filepath.split(".bz2")[0]
        metadata_start_time = time.perf_counter()
        read_xml_file(
            unzipped_file,
            doc_map,
            link_graph,
            inverted_index,
            document_lengths,
        )
        metadata_end_time = time.perf_counter()
        print(f"Metadata took {formatElapsedTime(metadata_end_time - metadata_start_time)}")

        os.remove(os.path.join(DUMP_DIR, "download.xml"))
        os.remove(os.path.join(DUMP_DIR, "download.xml.bz2"))

        if i % 3 == 0:
            with open(f"doc_map_{i}.pkl", "wb") as p:
                pickle.dump(doc_map, p)
            doc_map.clear()

            with open(f"link_graph_{i}.pkl", "wb") as p:
                pickle.dump(doc_map, p)
            link_graph.clear()

            with open(f"document_lengths_{i}.pkl", "wb") as p:
                pickle.dump(doc_map, p)
            document_lengths.clear()




if __name__ == "__main__":
    main()
