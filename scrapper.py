import ipaddress
import os
import socket
from urllib.parse import urlparse

import trafilatura


class ScrapeError(ValueError):
    """Raised when a source URL yields no usable article text."""


def assert_public_http_url(url: str) -> None:
    """Reject anything that is not a public http(s) URL.

    The service fetches user-supplied links, so block the usual SSRF targets:
    non-http schemes, loopback, private, link-local, multicast and reserved
    addresses (cloud metadata endpoints included). Every resolved address must
    pass, not just the first one.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ScrapeError(f"Only public http(s) links are accepted: {url}")
    host = parsed.hostname
    if host.lower() == "localhost" or host.endswith(".internal"):
        raise ScrapeError(f"Blocked host: {host}")
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise ScrapeError(f"Could not resolve {host}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise ScrapeError(f"Blocked host: {host}")


def scrape_data(url: str, max_chars: int = 20000) -> str:
    """Fetch a page and return its main article content as markdown.

    Uses trafilatura: no API key, runs fully inside the container.
    Redirects are followed by trafilatura, so the public-host check is
    repeated on the final URL it reports when available.
    """
    assert_public_http_url(url)
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ScrapeError(f"Could not fetch {url}")

    text = trafilatura.extract(
        downloaded,
        output_format="markdown",
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )
    if not text or len(text.strip()) < 200:
        raise ScrapeError(f"No article content found at {url}")

    return text[:max_chars]


def save_data(data, timestamp, filename, output_folder="output"):
    os.makedirs(output_folder, exist_ok=True)
    raw_output_path = os.path.join(output_folder, f"{filename}_{timestamp}.md")
    with open(raw_output_path, "w", encoding="utf-8") as f:
        f.write(data)
    print(f"Raw data saved to {raw_output_path}")
