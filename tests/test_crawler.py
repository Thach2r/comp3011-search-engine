import pytest
from unittest.mock import patch, MagicMock
from src.crawler import get_page, extract_links, crawl


# Unit Tests: get_page 

class TestGetPage:

    def test_returns_html_on_success(self):
        """get_page should return HTML string on successful request."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("src.crawler.requests.get", return_value=mock_response):
            result = get_page("http://example.com")

        assert result == "<html><body>Hello</body></html>"

    def test_returns_none_on_network_error(self):
        """get_page should return None when a network error occurs."""
        import requests as req
        with patch("src.crawler.requests.get", side_effect=req.RequestException("timeout")):
            result = get_page("http://example.com")

        assert result is None

    def test_returns_none_on_404(self):
        """get_page should return None when server returns 4xx error."""
        import requests as req
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.RequestException("404")

        with patch("src.crawler.requests.get", return_value=mock_response):
            result = get_page("http://example.com")

        assert result is None


# Unit Tests: extract_links 

class TestExtractLinks:

    def test_extracts_internal_links(self):
        """extract_links should return links on the same domain."""
        html = '<a href="/page/2">Next</a><a href="/author/Einstein">Author</a>'
        links = extract_links(html, "https://quotes.toscrape.com")

        assert "https://quotes.toscrape.com/page/2" in links
        assert "https://quotes.toscrape.com/author/Einstein" in links

    def test_excludes_external_links(self):
        """extract_links should not return links to other domains."""
        html = '<a href="https://google.com">Google</a>'
        links = extract_links(html, "https://quotes.toscrape.com")

        assert "https://google.com" not in links

    def test_returns_empty_set_for_no_links(self):
        """extract_links should return empty set when page has no links."""
        html = "<p>No links here</p>"
        links = extract_links(html, "https://quotes.toscrape.com")

        assert links == set()

    def test_handles_empty_html(self):
        """extract_links should handle empty HTML gracefully."""
        links = extract_links("", "https://quotes.toscrape.com")
        assert links == set()

    def test_deduplicates_links(self):
        """extract_links should not return duplicate URLs."""
        html = '<a href="/page/2">Next</a><a href="/page/2">Also Next</a>'
        links = extract_links(html, "https://quotes.toscrape.com")

        assert len([l for l in links if "page/2" in l]) == 1


# Integration Tests: crawl 

class TestCrawl:

    def test_crawl_visits_linked_pages(self):
        """crawl should follow links and return multiple pages."""
        page1_html = '<a href="/page/2">Next</a><p>Page one content</p>'
        page2_html = '<a href="/">Home</a><p>Page two content</p>'

        def fake_get_page(url):
            if url == "https://quotes.toscrape.com":
                return page1_html
            elif url == "https://quotes.toscrape.com/page/2":
                return page2_html
            return None

        with patch("src.crawler.get_page", side_effect=fake_get_page):
            with patch("src.crawler.time.sleep"):  # skip waiting
                result = crawl("https://quotes.toscrape.com")

        assert "https://quotes.toscrape.com" in result
        assert "https://quotes.toscrape.com/page/2" in result

    def test_crawl_does_not_revisit_pages(self):
        """crawl should not visit the same page twice."""
        html = '<a href="/">Home</a><p>Content</p>'
        call_count = {"n": 0}

        def fake_get_page(url):
            call_count["n"] += 1
            return html

        with patch("src.crawler.get_page", side_effect=fake_get_page):
            with patch("src.crawler.time.sleep"):
                crawl("https://quotes.toscrape.com")

        assert call_count["n"] == 1

    def test_crawl_handles_failed_pages(self):
        """crawl should skip pages that return None and continue."""
        def fake_get_page(url):
            return None

        with patch("src.crawler.get_page", side_effect=fake_get_page):
            with patch("src.crawler.time.sleep"):
                result = crawl("https://quotes.toscrape.com")

        assert result == {}


# Performance Tests 

class TestCrawlerPerformance:

    def test_extract_links_performance(self):
        """extract_links should process a large page quickly."""
        import time
        # Generate HTML with 1000 links
        links_html = "".join(f'<a href="/page/{i}">Page {i}</a>' for i in range(1000))
        html = f"<html><body>{links_html}</body></html>"

        start = time.time()
        extract_links(html, "https://quotes.toscrape.com")
        elapsed = time.time() - start

        assert elapsed < 2.0, f"extract_links took too long: {elapsed:.2f}s"