import json
import os
import re
from bs4 import BeautifulSoup

INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "index.json")


def extract_words(html):
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


def build_index(pages):
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
    index = {}

    for url, html in pages.items():
        words = extract_words(html)

        for position, word in enumerate(words):
            if word not in index:
                index[word] = {}

            if url not in index[word]:
                index[word][url] = {"count": 0, "positions": []}

            index[word][url]["count"] += 1
            index[word][url]["positions"].append(position)

    return index


def save_index(index):
    """Save the index to a JSON file."""
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"Index saved to {INDEX_PATH}")


def load_index():
    """
    Load the index from a JSON file.
    Returns None if the file doesn't exist.
    """
    if not os.path.exists(INDEX_PATH):
        print("No index found. Please run 'build' first.")
        return None

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)
    print(f"Index loaded. {len(index)} unique words.")
    return index