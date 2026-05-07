import json
import os
import re
from bs4 import BeautifulSoup
from typing import Optional, TypedDict


class WordStats(TypedDict):
    """Frequency and position data for one word on one page."""

    count: int
    positions: list[int]


InvertedIndex = dict[str, dict[str, WordStats]]

INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "index.json")
PAGES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pages.json")


def extract_words(html: str) -> list[str]:
    """
    Extract all words from a page's HTML content.
    Strips HTML tags, lowercases everything, and returns a list of words
    in order (preserving position information).
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")
    # Find all words (letters and numbers only, no punctuation)
    words = re.findall(r'[a-z0-9]+', text.lower())
    return words


def extract_text(html: str) -> str:
    """Extract clean plain text from HTML for snippet generation."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ").strip()


def build_index(pages: dict[str, str]) -> tuple[InvertedIndex, dict[str, str]]:
    """
    Build an inverted index from a dict of {url: html_content}.

    Index structure:
    {
        "word": {
            "url": {
                "count": 3,
                "positions": [5, 12, 47]
            }
        }
    }
    """
    index: InvertedIndex = {}
    page_texts: dict[str, str] = {}

    for url, html in pages.items():
        page_texts[url] = extract_text(html)
        words = extract_words(html)

        for position, word in enumerate(words):
            # O(1) average lookup per word due to dict hash table
            if word not in index:
                index[word] = {}

            if url not in index[word]:
                index[word][url] = {"count": 0, "positions": []}

            index[word][url]["count"] += 1
            index[word][url]["positions"].append(position)

    return index, page_texts


def save_index(index: InvertedIndex, page_texts: dict[str, str]) -> None:
    """Save the index to a JSON file."""
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    with open(PAGES_PATH, "w", encoding="utf-8") as f:
        json.dump(page_texts, f, indent=2)
    print(f"Index saved to {INDEX_PATH}")


def load_index() -> Optional[tuple[InvertedIndex, dict[str, str]]]:
    """
    Load the index from a JSON file.
    Returns None if the file doesn't exist.
    """
    if not os.path.exists(INDEX_PATH) or not os.path.exists(PAGES_PATH):
        print("No index found. Please run 'build' first.")
        return None

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index: InvertedIndex = json.load(f)
    with open(PAGES_PATH, "r", encoding="utf-8") as f:
        page_texts: dict[str, str] = json.load(f)
    print(f"Index loaded. {len(index)} unique words.")
    return index, page_texts
