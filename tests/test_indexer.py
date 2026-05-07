import pytest
import json
import os
import tempfile
from src.indexer import extract_words, build_index, save_index, load_index


# Unit Tests: extract_words 

class TestExtractWords:

    def test_extracts_basic_words(self):
        """extract_words should return list of words from HTML."""
        html = "<p>Hello world</p>"
        words = extract_words(html)
        assert "hello" in words
        assert "world" in words

    def test_lowercases_all_words(self):
        """extract_words should lowercase everything."""
        html = "<p>Good FRIENDS Are GREAT</p>"
        words = extract_words(html)
        assert "good" in words
        assert "friends" in words
        assert "Good" not in words
        assert "FRIENDS" not in words

    def test_strips_html_tags(self):
        """extract_words should ignore HTML tags."""
        html = "<h1>Title</h1><p>Body text</p>"
        words = extract_words(html)
        assert "h1" not in words
        assert "title" in words
        assert "body" in words

    def test_removes_punctuation(self):
        """extract_words should not include punctuation as words."""
        html = "<p>Hello, world! How's life?</p>"
        words = extract_words(html)
        assert "," not in words
        assert "!" not in words
        assert "hello" in words

    def test_returns_empty_list_for_empty_html(self):
        """extract_words should return empty list for empty input."""
        words = extract_words("")
        assert words == []

    def test_preserves_word_order(self):
        """extract_words should preserve the order of words."""
        html = "<p>one two three</p>"
        words = extract_words(html)
        assert words.index("one") < words.index("two") < words.index("three")


# Unit Tests: build_index 

class TestBuildIndex:

    def test_builds_basic_index(self):
        """build_index should index words from pages."""
        pages = {"http://page1.com": "<p>hello world</p>"}
        index, page_texts = build_index(pages)
        assert "hello" in index
        assert "world" in index
        assert page_texts["http://page1.com"] == "hello world"

    def test_records_correct_count(self):
        """build_index should count word occurrences correctly."""
        pages = {"http://page1.com": "<p>good good good</p>"}
        index, page_texts = build_index(pages)
        assert index["good"]["http://page1.com"]["count"] == 3

    def test_records_correct_positions(self):
        """build_index should record word positions correctly."""
        pages = {"http://page1.com": "<p>good friends good</p>"}
        index, page_texts = build_index(pages)
        positions = index["good"]["http://page1.com"]["positions"]
        assert len(positions) == 2
        assert positions[0] < positions[1]

    def test_handles_multiple_pages(self):
        """build_index should index words across multiple pages."""
        pages = {
            "http://page1.com": "<p>hello world</p>",
            "http://page2.com": "<p>hello python</p>"
        }
        index, page_texts = build_index(pages)
        assert "http://page1.com" in index["hello"]
        assert "http://page2.com" in index["hello"]
        assert "http://page1.com" not in index["python"]

    def test_returns_empty_index_for_empty_pages(self):
        """build_index should return empty dict for empty input."""
        index, page_texts = build_index({})
        assert index == {}
        assert page_texts == {}

    def test_case_insensitive_indexing(self):
        """build_index should treat Good and good as the same word."""
        pages = {"http://page1.com": "<p>Good good GOOD</p>"}
        index, page_texts = build_index(pages)
        assert index["good"]["http://page1.com"]["count"] == 3


# Integration Tests: save and load 

class TestSaveAndLoad:

    def test_save_then_load_returns_same_index(self):
        """save_index and load_index should be inverse operations."""
        pages = {"http://page1.com": "<p>hello world</p>"}
        original_index, page_texts = build_index(pages)

        # Use a temporary file so we don't affect real data
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_pages_path = f.name

        try:
            import src.indexer as indexer_module
            original_path = indexer_module.INDEX_PATH
            original_pages_path = indexer_module.PAGES_PATH
            indexer_module.INDEX_PATH = temp_path
            indexer_module.PAGES_PATH = temp_pages_path

            save_index(original_index, {})
            loaded_index, loaded_page_texts = load_index()

            assert loaded_index == original_index
            assert loaded_page_texts == {}
        finally:
            indexer_module.INDEX_PATH = original_path
            indexer_module.PAGES_PATH = original_pages_path
            os.unlink(temp_path)
            os.unlink(temp_pages_path)

    def test_load_returns_none_when_no_file(self):
        """load_index should return None if index file doesn't exist."""
        import src.indexer as indexer_module
        original_path = indexer_module.INDEX_PATH
        original_pages_path = indexer_module.PAGES_PATH
        indexer_module.INDEX_PATH = "/nonexistent/path/index.json"
        indexer_module.PAGES_PATH = "/nonexistent/path/pages.json"

        try:
            result = load_index()
            assert result is None
        finally:
            indexer_module.INDEX_PATH = original_path
            indexer_module.PAGES_PATH = original_pages_path


# Performance Tests 

class TestIndexerPerformance:

    def test_build_index_performance(self):
        """build_index should handle many pages efficiently."""
        import time
        pages = {
            f"http://page{i}.com": f"<p>{'word ' * 500}</p>"
            for i in range(50)
        }

        start = time.time()
        index, page_texts = build_index(pages)
        elapsed = time.time() - start

        assert len(index) > 0
        assert len(page_texts) == 50
        assert elapsed < 5.0, f"build_index took too long: {elapsed:.2f}s"
