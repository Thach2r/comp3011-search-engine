import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

POLITENESS_DELAY = 6  # seconds between requests, as required by brief

def get_page(url):
    """
    Fetch a single page and return its HTML content.
    Returns None if the request fails.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def extract_links(html, base_url):
    """
    Extract all internal links from a page.
    Only returns links that belong to the same domain as base_url.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    base_domain = urlparse(base_url).netloc

    for tag in soup.find_all("a", href=True):
        full_url = urljoin(base_url, tag["href"])
        # Only keep links on the same domain
        if urlparse(full_url).netloc == base_domain:
            # Remove fragments (#section) and trailing slashes for consistency
            clean_url = full_url.split("#")[0].rstrip("/")
            if clean_url:
                links.add(clean_url)

    return links


def crawl(start_url):
    """
    Crawl all pages starting from start_url.
    Returns a dict of {url: html_content}.
    Respects the politeness window between requests.
    """
    visited = {}       # {url: html_content}
    to_visit = {start_url}

    print(f"Starting crawl from {start_url}")

    while to_visit:
        url = to_visit.pop()

        if url in visited:
            continue

        print(f"Crawling: {url}")
        html = get_page(url)

        if html is None:
            continue

        visited[url] = html

        new_links = extract_links(html, start_url)
        for link in new_links:
            if link not in visited:
                to_visit.add(link)

        if to_visit:
            print(f"  Waiting {POLITENESS_DELAY}s (politeness window)...")
            time.sleep(POLITENESS_DELAY)

    print(f"Crawl complete. {len(visited)} pages visited.")
    return visited