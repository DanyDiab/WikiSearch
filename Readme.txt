WikiSearch Readme

Environment
- Python 3
- A standard Python virtual environment can be used to run the project.

Setup
1. Open a terminal in the project root.
2. Create a virtual environment:
   python3 -m venv .venv
3. Activate the virtual environment:
   source .venv/bin/activate
4. Upgrade `pip`:
   python3 -m pip install --upgrade pip
5. Install the Python dependencies from `requirements.txt`:
   pip install -r requirements.txt

Install Dependencies
- Download the NLTK resources used by the query pipeline:
  ```python3 -m nltk.downloader words stopwords averaged_perceptron_tagger_eng wordnet```

NLTK Resources
- The query pipeline in `scripts/tf_idf.py` depends on the following NLTK data packages:
  - `words`
  - `stopwords`
  - `averaged_perceptron_tagger_eng`
  - `wordnet`
- These are used for:
  - validating English words
  - removing stop words from queries
  - part-of-speech tagging
  - lemmatization
- If these resources are not installed, the query program will fail with an NLTK `LookupError`.
- The downloader command only needs to be run once per environment.

Main Scripts
- Build the full database from the Wikipedia dump:
  python3 scripts/download.py
  Note: This does not need to be run for normal verification or marking. It is the full data build path and is included for completeness.

- Run the search program against the default database (`database/wiki.db`):
  python3 scripts/main.py

- Run the search program against a specific database file:
  python3 scripts/main.py --db database/temp_first_dump.db

- Build only the first Wikipedia dump file into a temporary database:
  python3 scripts/temp_first_dump_test.py
  Estimated runtime: approximately 1 hour 35 minutes based on our run for the first dump block.

Compressed Temporary Database
- A compressed temporary submission database file is included at:
  database/temp_first_dump_submission.db.zst
- This database is a reduced submission version derived from the first Wikipedia dump file from the March 1, 2026 snapshot.
- We originally prepared a database based on the entire first dump chunk, but that database was still too large to submit through Brightspace.
- For that reason, the submitted database is a smaller subset of that first-dump database, so that the marker can still run and verify the program within the upload limit.
- Because it only contains a reduced subset of the first dump chunk, query coverage is limited compared with both the full first-dump database and the fully built final database.
- The fully built final database is approximately 115 GB in size and gives much broader coverage and better overall query results.

- To decompress it into `database/temp_first_dump_submission.db`, run:
  zstd -d -f database/temp_first_dump_submission.db.zst -o database/temp_first_dump_submission.db

- Then run the search program against that database:
  python3 scripts/main.py --db database/temp_first_dump_submission.db

Example Queries For `temp_first_dump_submission.db`
- apple
- astronomy
- computer science
- abraham lincoln
- aristotle

Useful SQLite Checks
- Show the number of documents in the selected database:
  sqlite3 database/temp_first_dump_submission.db "SELECT COUNT(*) FROM DOCUMENTS;"

- Show a few page titles:
  sqlite3 database/temp_first_dump_submission.db "SELECT page_name FROM DOCUMENTS ORDER BY doc_id LIMIT 20;"

- Show pages containing a keyword in the title:
  sqlite3 database/temp_first_dump_submission.db "SELECT page_name FROM DOCUMENTS WHERE page_name LIKE '%astronomy%' LIMIT 10;"

Notes
- The search program prompts for a query after startup.
- The included `temp_first_dump_submission.db.zst` is intended as a smaller verification database for testing and marking.
- Since `temp_first_dump_submission.db` is only a reduced subset derived from the first March 1, 2026 dump file, some topics may be missing or have weaker results than the full database.
- To leave the virtual environment when finished, run:
  deactivate
