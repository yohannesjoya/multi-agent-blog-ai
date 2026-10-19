import ipaddress
import os
import socket
import time
from urllib.parse import urljoin, urlparse

import requests
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


MAX_REDIRECTS = 5
FETCH_TIMEOUT = 15
MAX_BYTES = 5_000_000
USER_AGENT = "Mozilla/5.0 (compatible; MultiAgentBlogAI/1.0; +https://github.com/yohannesjoya/multi-agent-blog-ai)"


_session = requests.Session()
_session.trust_env = False  # ignore proxy env vars; the host check must apply to the real connection


def fetch_public_html(url: str) -> str:
    """Fetch HTML, following redirects by hand so every hop is re-checked.

    Bounded by a total deadline and a decoded-byte cap read in chunks, so a
    slow or compressed response cannot stall or inflate past the limits.

    Residual risk, accepted for this rate-limited demo: the host is resolved
    for the check and again by requests for the connection (DNS rebinding
    window). Pinning the connection to the checked IP would need a custom
    transport that sets SNI and Host separately.
    """
    deadline = time.monotonic() + FETCH_TIMEOUT
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        assert_public_http_url(current)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ScrapeError(f"Timed out fetching {url}")
        resp = _session.get(
            current,
            allow_redirects=False,
            timeout=(5, remaining),
            stream=True,
            headers={"User-Agent": USER_AGENT},
        )
        try:
            if resp.is_redirect or resp.is_permanent_redirect:
                location = resp.headers.get("Location")
                if not location:
                    raise ScrapeError(f"Redirect without Location from {current}")
                current = urljoin(current, location)
                continue
            if resp.status_code != 200:
                raise ScrapeError(f"HTTP {resp.status_code} from {current}")
            chunks, total = [], 0
            for chunk in resp.iter_content(chunk_size=65536):
                if time.monotonic() > deadline:
                    raise ScrapeError(f"Timed out fetching {url}")
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ScrapeError(f"Page too large: {current}")
                chunks.append(chunk)
            encoding = resp.encoding
        finally:
            resp.close()
        return b"".join(chunks).decode(encoding or "utf-8", errors="replace")
    raise ScrapeError(f"Too many redirects from {url}")


def scrape_data(url: str, max_chars: int = 20000) -> str:
    """Fetch a page and return its main article content as markdown.

    Uses trafilatura for extraction only; fetching goes through
    fetch_public_html so redirects cannot escape the public-host check.
    """
    downloaded = fetch_public_html(url)
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
