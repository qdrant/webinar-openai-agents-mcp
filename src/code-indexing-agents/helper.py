import logging
from collections.abc import Iterable
from urllib.parse import urljoin, urlparse

import requests
from agents import RunContextWrapper
from bs4 import BeautifulSoup

import models

logger = logging.getLogger(__name__)


def download_html(url: str) -> str:
    """
    Download the HTML content of a URL and return it as a string.
    Args:
        url: The URL to download
    Returns:
        The HTML content of the URL as a string
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def iter_urls(base_url: str) -> Iterable[str]:
    """
    Take a base URL and return all the internal links from it.
    The base URL points to an HTML document.

    Args:
        base_url: The URL of the HTML document to parse

    Returns:
        An iterable of unique URLs that are internal links from the base URL,
        ignoring fragments when determining uniqueness.
        Only returns URLs that are in the same directory as the base URL or its subdirectories.
    """
    # Fetch the HTML content from the base URL
    response = requests.get(base_url)
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the base domain and path for filtering internal links
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc
    base_scheme = parsed_base.scheme

    # Get the base directory path
    base_path = parsed_base.path
    if "/" in base_path.rstrip("/"):
        base_dir = base_path[: base_path.rstrip("/").rindex("/") + 1]
    else:
        base_dir = "/"

    # Set to track unique URLs (without fragments)
    unique_urls = set()

    # Find all anchor tags and extract their href attributes
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        # Convert relative URLs to absolute URLs
        absolute_url = urljoin(base_url, href)
        parsed_url = urlparse(absolute_url)

        # Skip external links
        if parsed_url.netloc != base_domain and parsed_url.netloc:
            continue

        # Skip URLs that go to parent directories
        if not parsed_url.path.startswith(base_dir):
            continue

        # Ensure the URL has a scheme
        if not parsed_url.scheme:
            absolute_url = f"{base_scheme}://{base_domain}{parsed_url.path}"
            if parsed_url.query:
                absolute_url += f"?{parsed_url.query}"
            parsed_url = urlparse(absolute_url)

        # Create a version of the URL without the fragment for uniqueness checking
        url_without_fragment = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        if parsed_url.query:
            url_without_fragment += f"?{parsed_url.query}"

        # Skip URLs we've already seen (ignoring fragments)
        if url_without_fragment in unique_urls:
            continue

        # Add to our set of unique URLs
        unique_urls.add(url_without_fragment)

        # Yield the full URL including fragment if it exists
        if parsed_url.fragment:
            yield f"{url_without_fragment}#{parsed_url.fragment}"
        else:
            yield url_without_fragment


async def on_handoff_callback(ctx: RunContextWrapper[None], input_data: models.BaseModel):
    logger.info(f"Handoff callback called with input: {input_data}")
