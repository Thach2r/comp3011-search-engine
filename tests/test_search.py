import pytest
from src.search import print_word, find_pages, compute_tfidf
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
    return build_index(pages)


# Unit Tests: print_word

class TestPrintWord:

    def test_prints_existing_word(self, sample_index, capsys):
        """print_word should print info for a word that exists."""
        print_word(sample_index, "good")
        captured = capsys.readouterr()
        assert "good" in captured.out
        assert "page(s)" in captured.out

    def test_prints_not_found_for_missing_word(self, sample_index, capsys):
        """print_word should say not found for a word not in index."""
        print_word(sample_index, "elephant")
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_case_insensitive_print(self, sample_index, capsys):
        """print_word should handle uppercase input."""
        print_word(sample_index, "GOOD")
        captured = capsys.readouterr()
        assert "not found" not in captured.out

    def test_prints_url_and_count(self, sample_index, capsys):
        """print_word output should include URL and count."""
        print_word(sample_index, "good")
        captured = capsys.readouterr()
        assert "http://page1.com" in captured.out
        assert "Count" in captured.out


# Unit Tests: find_pages

class TestFindPages:

    def test_find_single_word(self, sample_index):
        """find_pages should return pages containing a single word."""
        results = find_pages(sample_index, "good")
        urls = [r[0] for r in results]
        assert "http://page1.com" in urls
        assert "http://page2.com" in urls
        assert "http://page4.com" not in urls

    def test_find_multi_word_and_logic(self, sample_index):
        """find_pages should return only pages containing ALL words."""
        results = find_pages(sample_index, "good friends")
        urls = [r[0] for r in results]
        # Only page1 has both "good" and "friends"
        assert "http://page1.com" in urls
        assert "http://page2.com" not in urls
        assert "http://page3.com" not in urls

    def test_find_returns_empty_for_missing_word(self, sample_index):
        """find_pages should return empty list if a word doesn't exist."""
        results = find_pages(sample_index, "elephant")
        assert results == []

    def test_find_empty_query(self, sample_index, capsys):
        """find_pages should handle empty query gracefully."""
        results = find_pages(sample_index, "")
        assert results == []

    def test_find_case_insensitive(self, sample_index):
        """find_pages should treat GOOD and good as the same."""
        results_lower = find_pages(sample_index, "good")
        results_upper = find_pages(sample_index, "GOOD")
        assert len(results_lower) == len(results_upper)

    def test_find_results_sorted_by_score(self, sample_index):
        """find_pages results should be sorted highest score first."""
        results = find_pages(sample_index, "good")
        scores = [r[1] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_find_no_results_when_no_page_has_all_words(self, sample_index, capsys):
        """find_pages should return empty when no page has all query words."""
        results = find_pages(sample_index, "good mystery")
        assert results == []


# Unit Tests: compute_tfidf

class TestComputeTfidf:

    def test_returns_positive_score(self, sample_index):
        """TF-IDF score should be positive for a word that exists."""
        total_pages = len(sample_index)
        score = compute_tfidf("good", "http://page1.com", sample_index, total_pages)
        assert score > 0

    def test_rare_word_scores_higher_than_common_word(self, sample_index):
        """A rare word should have higher IDF than a common word."""
        # "good" appears in 2 pages, "life" appears in 1 page
        # life should have higher IDF (rarer word)
        total_pages = 4  # we have 4 pages in sample_index fixture
        score_common = compute_tfidf("good", "http://page2.com", sample_index, total_pages)
        score_rare = compute_tfidf("life", "http://page4.com", sample_index, total_pages)
        assert score_rare > score_common


# Integration Tests

class TestSearchIntegration:

    def test_build_then_find(self):
        """Full pipeline: build index then find words."""
        pages = {
            "http://a.com": "<p>python is great for programming</p>",
            "http://b.com": "<p>python and java are programming languages</p>",
            "http://c.com": "<p>music and art are wonderful</p>",
        }
        index = build_index(pages)
        results = find_pages(index, "python programming")
        urls = [r[0] for r in results]

        assert "http://a.com" in urls
        assert "http://b.com" in urls
        assert "http://c.com" not in urls

    def test_whitespace_query_handling(self):
        """find_pages should handle extra whitespace in queries."""
        pages = {"http://a.com": "<p>good friends</p>"}
        index = build_index(pages)
        results = find_pages(index, "  good  friends  ")
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
        index = build_index(pages)

        start = time.time()
        find_pages(index, "good friends")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"find_pages took too long: {elapsed:.2f}s"
