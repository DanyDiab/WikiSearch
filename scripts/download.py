import bz2
import os
import queue
import threading
import time
from codecs import getincrementaldecoder
from pathlib import Path

from db import Database, WIKI_DB
from get_wiki_content import formatElapsedTime, get_dump_file_tags, streamDownloadBZ2
from parse_xml import PAGE_TAG, parse_page
from tqdm import tqdm

BATCH_SIZE = 2_000
MAX_FILES_ENV = "WIKI_MAX_FILES"
QUEUE_MAXSIZE = 32
SENTINEL = object()
DECOMPRESSED_REPORT_BYTES = 128 * 1024 * 1024
PARSED_REPORT_DOCS = 2_000


def flush_batches(
    db: Database,
    term_id_cache: dict[str, int],
    documents: list[tuple[int, str]],
    doc_lengths: list[tuple[int, int]],
    postings_by_doc: list[tuple[int, dict[str, int]]],
    raw_links: list[tuple[int, str]],
):
    if not documents:
        return 0

    db.insert_documents(documents)
    db.insert_doc_lengths(doc_lengths)

    unseen_terms = sorted(
        {
            term
            for _, word_counts in postings_by_doc
            for term in word_counts
            if term not in term_id_cache
        }
    )
    db.ensure_terms(unseen_terms)
    term_id_cache.update(db.fetch_term_ids(unseen_terms))

    postings = []
    for doc_id, word_counts in postings_by_doc:
        for term, word_count in word_counts.items():
            postings.append((term_id_cache[term], doc_id, word_count))

    db.insert_postings(postings)
    db.insert_raw_links(raw_links)
    db.commit()

    flushed_count = len(documents)
    documents.clear()
    doc_lengths.clear()
    postings_by_doc.clear()
    raw_links.clear()
    return flushed_count


def get_dump_file_limit() -> int | None:
    raw_value = os.environ.get(MAX_FILES_ENV)
    if raw_value is None or raw_value == "":
        return None
    return max(int(raw_value), 0)


def put_or_stop(work_queue: queue.Queue, item, stop_event: threading.Event):
    while True:
        if stop_event.is_set():
            return False
        try:
            work_queue.put(item, timeout=0.5)
            return True
        except queue.Full:
            continue


def get_or_stop(work_queue: queue.Queue, stop_event: threading.Event):
    while True:
        if stop_event.is_set() and work_queue.empty():
            return SENTINEL
        try:
            return work_queue.get(timeout=0.5)
        except queue.Empty:
            if stop_event.is_set():
                return SENTINEL


def record_worker_error(
    error_queue: queue.Queue,
    stop_event: threading.Event,
    stage_name: str,
    exc: Exception,
):
    if error_queue.empty():
        error_queue.put(RuntimeError(f"{stage_name} failed: {exc}"))
    stop_event.set()


def log_progress(message: str):
    tqdm.write(message)


def downloader_worker(tag, file_size: int, compressed_queue: queue.Queue, stop_event: threading.Event, error_queue: queue.Queue):
    try:
        log_progress("Started downloading compressed data ...")
        for compressed_chunk in streamDownloadBZ2(tag, file_size):
            if stop_event.is_set():
                break
            if not put_or_stop(compressed_queue, compressed_chunk, stop_event):
                return
    except Exception as exc:
        record_worker_error(error_queue, stop_event, "Downloader", exc)
    finally:
        put_or_stop(compressed_queue, SENTINEL, stop_event)


def decompressor_worker(
    compressed_queue: queue.Queue,
    xml_queue: queue.Queue,
    stop_event: threading.Event,
    error_queue: queue.Queue,
):
    decompressor = bz2.BZ2Decompressor()
    decompressed_total = 0
    next_report = DECOMPRESSED_REPORT_BYTES
    try:
        log_progress("Started decompression ...")
        while True:
            compressed_chunk = get_or_stop(compressed_queue, stop_event)
            if compressed_chunk is SENTINEL:
                break

            decompressed_chunk = decompressor.decompress(compressed_chunk)
            if decompressed_chunk and not put_or_stop(xml_queue, decompressed_chunk, stop_event):
                return
            if decompressed_chunk:
                decompressed_total += len(decompressed_chunk)
                while decompressed_total >= next_report:
                    log_progress(
                        f"Finished decompressing {decompressed_total / (1024 * 1024):.0f} MB of XML data"
                    )
                    next_report += DECOMPRESSED_REPORT_BYTES
    except Exception as exc:
        record_worker_error(error_queue, stop_event, "Decompressor", exc)
    finally:
        if decompressed_total:
            log_progress(
                f"Finished decompression for {decompressed_total / (1024 * 1024):.0f} MB of XML data"
            )
        put_or_stop(xml_queue, SENTINEL, stop_event)


def xml_queue_iter(xml_queue: queue.Queue, stop_event: threading.Event):
    while True:
        item = get_or_stop(xml_queue, stop_event)
        if item is SENTINEL:
            return
        yield item


def parser_worker(
    xml_queue: queue.Queue,
    db_queue: queue.Queue,
    stop_event: threading.Event,
    error_queue: queue.Queue,
):
    parser = None
    decoder = getincrementaldecoder("utf-8")()
    batch = []
    parsed_documents = 0
    next_report = PARSED_REPORT_DOCS

    try:
        import xml.etree.ElementTree as ET

        parser = ET.XMLPullParser(events=("end",))
        log_progress("Started parsing decompressed data ...")
        for xml_chunk in xml_queue_iter(xml_queue, stop_event):
            parser.feed(decoder.decode(xml_chunk))
            for _, elem in parser.read_events():
                if elem.tag != PAGE_TAG:
                    continue

                parsed_page = parse_page(elem)
                elem.clear()
                if parsed_page is None:
                    continue

                batch.append(parsed_page)
                parsed_documents += 1
                while parsed_documents >= next_report:
                    log_progress(f"Finished parsing {parsed_documents} documents from decompressed data")
                    next_report += PARSED_REPORT_DOCS
                if len(batch) >= BATCH_SIZE:
                    if not put_or_stop(db_queue, batch, stop_event):
                        return
                    batch = []

        tail = decoder.decode(b"", final=True)
        if tail:
            parser.feed(tail)

        parser.close()
        for _, elem in parser.read_events():
            if elem.tag != PAGE_TAG:
                continue

            parsed_page = parse_page(elem)
            elem.clear()
            if parsed_page is None:
                continue

            batch.append(parsed_page)
            parsed_documents += 1
            while parsed_documents >= next_report:
                log_progress(f"Finished parsing {parsed_documents} documents from decompressed data")
                next_report += PARSED_REPORT_DOCS
            if len(batch) >= BATCH_SIZE:
                if not put_or_stop(db_queue, batch, stop_event):
                    return
                batch = []

        if batch:
            put_or_stop(db_queue, batch, stop_event)
    except Exception as exc:
        record_worker_error(error_queue, stop_event, "Parser", exc)
    finally:
        if parsed_documents:
            log_progress(f"Finished parsing decompressed data for {parsed_documents} documents")
        put_or_stop(db_queue, SENTINEL, stop_event)


def db_writer_worker(
    db_path: Path,
    db_queue: queue.Queue,
    stop_event: threading.Event,
    error_queue: queue.Queue,
    progress_queue: queue.Queue,
):
    db = Database(db_path=db_path)
    term_id_cache: dict[str, int] = {}
    documents: list[tuple[int, str]] = []
    doc_lengths: list[tuple[int, int]] = []
    postings_by_doc: list[tuple[int, dict[str, int]]] = []
    raw_links: list[tuple[int, str]] = []
    processed_documents = 0

    try:
        log_progress("Started pushing to the DB ...")
        while True:
            page_batch = get_or_stop(db_queue, stop_event)
            if page_batch is SENTINEL:
                break

            for parsed_page in page_batch:
                doc_id = parsed_page["doc_id"]
                documents.append((doc_id, parsed_page["title"]))
                doc_lengths.append((doc_id, parsed_page["page_length"]))
                postings_by_doc.append((doc_id, parsed_page["word_counts"]))
                raw_links.extend((doc_id, target_title) for target_title in parsed_page["links"])

            if len(documents) >= BATCH_SIZE:
                processed_documents += flush_batches(
                    db,
                    term_id_cache,
                    documents,
                    doc_lengths,
                    postings_by_doc,
                    raw_links,
                )
                progress_queue.put(("db", processed_documents))

        processed_documents += flush_batches(
            db,
            term_id_cache,
            documents,
            doc_lengths,
            postings_by_doc,
            raw_links,
        )
        progress_queue.put(("db", processed_documents))
    except Exception as exc:
        record_worker_error(error_queue, stop_event, "DB writer", exc)
    finally:
        db.close()
        progress_queue.put(SENTINEL)


def run_pipeline_for_dump(tag, file_size: int, db_path: Path) -> int:
    stop_event = threading.Event()
    error_queue: queue.Queue = queue.Queue(maxsize=1)
    compressed_queue: queue.Queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
    xml_queue: queue.Queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
    db_queue: queue.Queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
    progress_queue: queue.Queue = queue.Queue()

    threads = [
        threading.Thread(
            target=downloader_worker,
            args=(tag, file_size, compressed_queue, stop_event, error_queue),
            name="download-worker",
        ),
        threading.Thread(
            target=decompressor_worker,
            args=(compressed_queue, xml_queue, stop_event, error_queue),
            name="decompress-worker",
        ),
        threading.Thread(
            target=parser_worker,
            args=(xml_queue, db_queue, stop_event, error_queue),
            name="parser-worker",
        ),
        threading.Thread(
            target=db_writer_worker,
            args=(db_path, db_queue, stop_event, error_queue, progress_queue),
            name="db-writer-worker",
        ),
    ]

    for thread in threads:
        thread.start()

    processed_documents = 0
    try:
        while True:
            message = progress_queue.get()
            if message is SENTINEL:
                break
            stage_name, value = message
            if stage_name == "db" and value > processed_documents:
                processed_documents = value
                log_progress(f"Finished DB insertions for {processed_documents} documents")
    finally:
        for thread in threads:
            thread.join()

    if not error_queue.empty():
        raise error_queue.get()

    return processed_documents


def initialize_database(db_path: Path):
    database = Database(db_path=db_path)
    try:
        database.reset_database()
        database.create_schema()
    finally:
        database.close()


def finalize_database(db_path: Path):
    database = Database(db_path=db_path)
    try:
        database.finalize_database()
    finally:
        database.close()


def build_dump_set(dump_files: list[tuple], db_path: Path) -> int:
    if not dump_files:
        raise RuntimeError("No dump files were found at the configured Wikimedia URL.")

    initialize_database(db_path)

    total_processed = 0
    for index, (tag, file_size) in enumerate(dump_files, start=1):
        href = tag.get("href")
        if href is None:
            continue

        print(f"[{index}/{len(dump_files)}] Pipelining {href} into SQLite")
        parse_start = time.perf_counter()
        file_processed = run_pipeline_for_dump(tag, file_size, db_path)
        total_processed += file_processed
        print(f"Pipeline took {formatElapsedTime(time.perf_counter() - parse_start)}")

    print("Finalizing indexes, links, and TF-IDF")
    finalize_start = time.perf_counter()
    finalize_database(db_path)
    print(f"Finalize took {formatElapsedTime(time.perf_counter() - finalize_start)}")
    return total_processed


def main():
    dump_files = get_dump_file_tags()
    dump_file_limit = get_dump_file_limit()
    if dump_file_limit is not None:
        dump_files = dump_files[:dump_file_limit]

    build_start = time.perf_counter()
    processed_documents = build_dump_set(dump_files, WIKI_DB)
    print(
        f"Completed build for {processed_documents} documents in "
        f"{formatElapsedTime(time.perf_counter() - build_start)}"
    )


if __name__ == "__main__":
    main()
