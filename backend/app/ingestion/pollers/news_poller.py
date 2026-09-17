"""Polls the GNews API using an incremental `since` cursor (LLD 2.2-A)."""
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.ingestion.normalizer import normalize
from app.ingestion.scheduler import get_last_poll_timestamp, set_last_poll_timestamp

SOURCE_NAME = "gnews"
API_URL = "https://gnews.io/api/v4/search"
PAGE_SIZE = 50  # GNews max per request is 100; 50 keeps responses light


def fetch_new_items(since: datetime | None = None, query: str | None = None) -> list[dict]:
    """Fetch AI-related articles published after `since` and return them normalized.

    Note: GNews free-tier has no strict 'since' — `from` filters by publish date,
    so overlapping polls are expected and handled by dedup at insert time.
    """
    if since is None:
        since = get_last_poll_timestamp(SOURCE_NAME)

    params = {
        "q": query or settings.news_query,
        "lang": "en",
        "max": PAGE_SIZE,
        "sortby": "publishedAt",
        "apikey": settings.news_api_key,
        "from": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    response = httpx.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    articles = response.json().get("articles", [])
    return [normalize(a, source_type="news") for a in articles]


def run(source_name: str = SOURCE_NAME, query: str | None = None) -> int:
    """One poll cycle: fetch -> dedupe -> insert. Returns number of new items stored."""
    from app.processing.dedup import insert_new_items

    since = get_last_poll_timestamp(source_name)
    items = fetch_new_items(since=since, query=query)
    inserted = insert_new_items(items)
    set_last_poll_timestamp(source_name, datetime.now(timezone.utc))
    return inserted


if __name__ == "__main__":
    print(f"Inserted {run()} new items.")
