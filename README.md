# COMP3011 Search Engine

A command-line search engine that crawls [quotes.toscrape.com](https://quotes.toscrape.com), builds an inverted index, and supports ranked search queries using TF-IDF scoring.

## Features

- Crawls all pages of a website with a 6-second politeness window
- Builds an inverted index storing word frequency and position data
- Supports single and multi-word search queries (AND logic)
- Ranks results using TF-IDF scoring
- Saves and loads index from disk

## Project Structure

```text
comp3011-search-engine/
├── src/
│   ├── crawler.py     # Web crawler
│   ├── indexer.py     # Inverted index builder
│   ├── search.py      # Search and TF-IDF ranking
│   └── main.py        # Command-line interface
├── tests/
│   ├── test_crawler.py
│   ├── test_indexer.py
│   ├── test_search.py
│   └── test_main.py
├── data/
│   └── index.json     # Generated index file
├── requirements.txt
└── README.md
```

## Installation

```bash
# Clone the repository
git clone https://github.com/Thach2r/comp3011-search-engine.git
cd comp3011-search-engine

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python3 -m src.main
```

### Commands

| Command | Description | Example |
|---|---|---|
| `build` | Crawl website and build index | `> build` |
| `load` | Load existing index from disk | `> load` |
| `print <word>` | Show index entry for a word | `> print good` |
| `find <query>` | Find pages containing all query words | `> find good friends` |
| `quit` | Exit the program | `> quit` |

### Example Session

```text
load
Index loaded. 4570 unique words.

print indifference
Word: 'indifference' — found in 11 page(s)

find good friends
Found 34 page(s) containing ['good', 'friends']:

1. https://quotes.toscrape.com/tag/contentment/page/1 Score: 1.3111 ...

quit
Goodbye.
```

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage report
python3 -m pytest tests/ --cov=src --cov-report=term-missing
```

**Test results: 56 tests, 100% coverage**

## Dependencies

- `requests` — HTTP requests for web crawling
- `beautifulsoup4` — HTML parsing
- `pytest` — Test framework
- `pytest-cov` — Coverage reporting

## Design Decisions & Complexity Analysis

### Data Structure: Nested Dictionary

The inverted index uses a nested dictionary structure:

```python
{word: {url: {count: int, positions: list[int]}}}
```

- **Lookup complexity: O(1)** — Python dictionaries use hash tables, so looking up any word is constant time regardless of index size.
- **Trade-off:** Higher memory usage compared to a database like SQLite, but acceptable for this dataset size (4,570 words, 214 pages). SQLite would reduce memory but increase lookup latency.

### Crawling: Set-based Visited Tracking

Using a `set` for visited URLs ensures O(1) membership checks, preventing duplicate crawls efficiently.

### Search Ranking: TF-IDF

Results are ranked using TF-IDF scoring:

- **TF (Term Frequency):** rewards pages where the query word appears often
- **IDF (Inverse Document Frequency):** penalises words that appear across many pages, boosting rare/specific terms
- **Trade-off:** TF-IDF is simpler than BM25 or neural ranking, but performs well for this dataset and is fully explainable.

### Storage: JSON vs SQLite

Index is stored as JSON for simplicity and human-readability.

- **JSON:** fast to load, easy to inspect, no dependencies
- **SQLite alternative:** lower memory, supports concurrent access, but adds complexity and slower for full-index loads
