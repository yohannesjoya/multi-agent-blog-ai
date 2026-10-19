import os

import trafilatura


class ScrapeError(ValueError):
    """Raised when a source URL yields no usable article text."""


def scrape_data(url: str, max_chars: int = 20000) -> str:
    """Fetch a page and return its main article content as markdown.

    Uses trafilatura: no API key, runs fully inside the container.
    """
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
