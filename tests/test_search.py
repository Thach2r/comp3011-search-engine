import pytest
from src.search import print_word, find_pages, compute_tfidf, get_snippet
from src.indexer import build_index


# Fixtures

@pytest.fixture
def sample_index():
    """Shared index used across multiple tests."""
    pages = {
        "http://page1.com": "<p>good friends are great people</p>",
        "http://page2.com": "<p>good people do good things always</p>",
        "http://page3.com": "<p>friends are wonderful and kind</p>",
        "http://page4.com": "<p>life is full of wonder and mystery</p>",
    }
    index, page_texts = build_index(pages)
    return index, page_texts


# Unit Tests: print_word

class TestPrintWord:

    def test_prints_existing_word(self, sample_index, capsys):
        """print_word should print info for a word that exists."""
        index, page_texts = sample_index
        print_word(index, "good")
        captured = capsys.readouterr()
        assert "good" in captured.out
        assert "page(s)" in captured.out

    def test_prints_not_found_for_missing_word(self, sample_index, capsys):
        """print_word should say not found for a word not in index."""
        index, page_texts = sample_index
        print_word(index, "elephant")
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_case_insensitive_print(self, sample_index, capsys):
        """print_word should handle uppercase input."""
        index, page_texts = sample_index
        print_word(index, "GOOD")
        captured = capsys.readouterr()
        assert "not found" not in captured.out

    def test_prints_url_and_count(self, sample_index, capsys):
        """print_word output should include URL and count."""
        index, page_texts = sample_index
        print_word(index, "good")
        captured = capsys.readouterr()
        assert "http://page1.com" in captured.out
        assert "Count" in captured.out


# Unit Tests: find_pages

class TestFindPages:

    def test_find_single_word(self, sample_index):
        """find_pages should return pages containing a single word."""
        index, page_texts = sample_index
        results = find_pages(index, "good", page_texts)
        urls = [r[0] for r in results]
        assert "http://page1.com" in urls
        assert "http://page2.com" in urls
        assert "http://page4.com" not in urls

    def test_find_multi_word_and_logic(self, sample_index):
        """find_pages should return only pages containing ALL words."""
        index, page_texts = sample_index
        results = find_pages(index, "good friends", page_texts)
        urls = [r[0] for r in results]
        # Only page1 has both "good" and "friends"
        assert "http://page1.com" in urls
        assert "http://page2.com" not in urls
        assert "http://page3.com" not in urls

    def test_find_returns_empty_for_missing_word(self, sample_index):
        """find_pages should return empty list if a word doesn't exist."""
        index, page_texts = sample_index
        results = find_pages(index, "elephant", page_texts)
        assert results == []

    def test_find_empty_query(self, sample_index, capsys):
        """find_pages should handle empty query gracefully."""
        index, page_texts = sample_index
        results = find_pages(index, "", page_texts)
        assert results == []

    def test_find_case_insensitive(self, sample_index):
        """find_pages should treat GOOD and good as the same."""
        index, page_texts = sample_index
        results_lower = find_pages(index, "good", page_texts)
        results_upper = find_pages(index, "GOOD", page_texts)
        assert len(results_lower) == len(results_upper)

    def test_find_results_sorted_by_score(self, sample_index):
        """find_pages results should be sorted highest score first."""
        index, page_texts = sample_index
        results = find_pages(index, "good", page_texts)
        scores = [r[1] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_find_no_results_when_no_page_has_all_words(self, sample_index, capsys):
        """find_pages should return empty when no page has all query words."""
        index, page_texts = sample_index
        results = find_pages(index, "good mystery", page_texts)
        assert results == []


# Unit Tests: compute_tfidf

class TestComputeTfidf:

    def test_returns_positive_score(self, sample_index):
        """TF-IDF score should be positive for a word that exists."""
        index, page_texts = sample_index
        total_pages = len(index)
        score = compute_tfidf("good", "http://page1.com", index, total_pages)
        assert score > 0

    def test_rare_word_scores_higher_than_common_word(self, sample_index):
        """A rare word should have higher IDF than a common word."""
        # "good" appears in 2 pages, "life" appears in 1 page
        # life should have higher IDF (rarer word)
        index, page_texts = sample_index
        total_pages = 4  # we have 4 pages in sample_index fixture
        score_common = compute_tfidf("good", "http://page2.com", index, total_pages)
        score_rare = compute_tfidf("life", "http://page4.com", index, total_pages)
        assert score_rare > score_common


# Unit Tests: get_snippet

class TestGetSnippet:

    def test_returns_preview_around_matching_word(self):
        """get_snippet should return text around the first matching query word."""
        text = "This is a short page about good friends and kind people."
        snippet = get_snippet(text, ["friends"], window=10)
        assert snippet.startswith("...")
        assert snippet.endswith("...")
        assert "friends" in snippet

    def test_returns_empty_string_when_no_word_matches(self):
        """get_snippet should return empty string when no query word is found."""
        snippet = get_snippet("This page talks about kindness.", ["elephant"])
        assert snippet == ""


# Integration Tests

class TestSearchIntegration:

    def test_build_then_find(self):
        """Full pipeline: build index then find words."""
        pages = {
            "http://a.com": "<p>python is great for programming</p>",
            "http://b.com": "<p>python and java are programming languages</p>",
            "http://c.com": "<p>music and art are wonderful</p>",
        }
        index, page_texts = build_index(pages)
        results = find_pages(index, "python programming", page_texts)
        urls = [r[0] for r in results]

        assert "http://a.com" in urls
        assert "http://b.com" in urls
        assert "http://c.com" not in urls

    def test_whitespace_query_handling(self):
        """find_pages should handle extra whitespace in queries."""
        pages = {"http://a.com": "<p>good friends</p>"}
        index, page_texts = build_index(pages)
        results = find_pages(index, "  good  friends  ", page_texts)
        assert len(results) > 0


# Performance Tests

class TestSearchPerformance:

    def test_find_performance_on_large_index(self):
        """find_pages should complete quickly on a large index."""
        import time
        pages = {
            f"http://page{i}.com": f"<p>good friends word{i} content here</p>"
            for i in range(200)
        }
        index, page_texts = build_index(pages)

        start = time.time()
        find_pages(index, "good friends", page_texts)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"find_pages took too long: {elapsed:.2f}s"
