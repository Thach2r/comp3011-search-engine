import math
from typing import TypedDict


class WordStats(TypedDict):
    """Frequency and position data for one word on one page."""

    count: int
    positions: list[int]


InvertedIndex = dict[str, dict[str, WordStats]]
SearchResult = tuple[str, float]


def print_word(index: InvertedIndex, word: str) -> None:
    """
    Print the inverted index entry for a single word.
    Shows which pages contain the word, with count and positions.
    """
    word = word.lower().strip()

    if word not in index:
        print(f"'{word}' not found in index.")
        return

    entries = index[word]
    print(f"\nWord: '{word}' — found in {len(entries)} page(s)")
    print("-" * 50)
    for url, stats in entries.items():
        print(f"  URL:       {url}")
        print(f"  Count:     {stats['count']}")
        print(f"  Positions: {stats['positions']}")
        print()


def compute_tfidf(word: str, url: str, index: InvertedIndex, total_pages: int) -> float:
    """
    Compute TF-IDF score for a word in a specific page.

    TF  = count of word in page / total words in page
    IDF = log(total pages / pages containing word)
    """
    count = index[word][url]["count"]
    total_positions = max(index[word][url]["positions"]) + 1
    tf = count / total_positions

    pages_with_word = len(index[word])
    idf = math.log(total_pages / pages_with_word)

    return tf * idf


def get_snippet(text: str, words: list[str], window: int = 50) -> str:
    """Return a short preview around the first matching query word."""
    text_lower = text.lower()

    for word in words:
        position = text_lower.find(word.lower())
        if position != -1:
            start = max(0, position - window)
            end = min(len(text), position + len(word) + window)
            snippet = " ".join(text[start:end].split())
            return f"...{snippet}..."

    return ""


def find_pages(
    index: InvertedIndex,
    query: str,
    page_texts: dict[str, str] = {},
) -> list[SearchResult]:
    """
    Find all pages containing ALL words in the query (AND logic).
    Returns results ranked by combined TF-IDF score.
    """
    words: list[str] = [w.lower().strip() for w in query.split()]

    if not words:
        print("Empty query.")
        return []

    # Check each word exists in index
    for word in words:
        if word not in index:
            print(f"'{word}' not found in index. No results.")
            return []

    # AND logic: only pages that contain ALL words
    candidate_sets: list[set[str]] = [set(index[word].keys()) for word in words]
    # Set intersection for AND logic: O(min(len(s1), len(s2)))
    matching_pages = candidate_sets[0]
    for s in candidate_sets[1:]:
        matching_pages = matching_pages.intersection(s)

    if not matching_pages:
        print(f"No pages contain all of: {words}")
        return []

    # Rank by TF-IDF
    total_pages = sum(len(entries) for entries in index.values())
    scored: list[SearchResult] = []
    for url in matching_pages:
        score = sum(compute_tfidf(word, url, index, total_pages) for word in words)
        scored.append((url, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    print(f"\nFound {len(scored)} page(s) containing {words}:")
    print("-" * 50)
    for rank, (url, score) in enumerate(scored, 1):
        print(f"  {rank}. {url}")
        print(f"     Score: {score:.4f}")
        snippet = get_snippet(page_texts.get(url, ""), words)
        if snippet:
            print(f'     Preview: "{snippet}"')

    return scored
