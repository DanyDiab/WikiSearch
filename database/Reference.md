# Database Reference

## TABLE: TERMS
Maps unique words to IDs.
- **term_id** (INTEGER, PK): Unique ID for the word.
- **term** (TEXT, UNIQUE): The actual word string.

## TABLE: INVERTED_INDEX
Links words to documents and stores frequency.
- **term_id** (INTEGER, PK/FK): Reference to TERMS.
- **doc_id** (INTEGER, PK/FK): Reference to DOCUMENTS.
- **word_count** (INTEGER): Number of times the word appears in this doc.

## TABLE: DOCUMENTS
Stores the doc id with title.
- **doc_id** (INTEGER, PK): Unique ID for the page.
- **page_name** (TEXT): The title of the page.

## TABLE: DOC_LENGTHS
Used to normalize scores based on document size.
- **doc_id** (INTEGER, PK/FK): Reference to DOCUMENTS.
- **page_length** (INTEGER): Total word count of the document.

## TABLE: LINKS
Stores the graph structure for HITS algorithm.
- **doc_id** (INTEGER, FK): The page containing the link.
- **link_id** (INTEGER, FK): The page the link points to.