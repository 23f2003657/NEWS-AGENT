"""Normalizes raw poller output into the common staging schema:
{source_type, source_name, external_id, url, title, raw_text, published_at, fetched_at}"""
import hashlib
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}


def canonicalize_url(url: str) -> str:
    """Lowercase scheme/host, drop tracking query params and fragment, strip trailing slash."""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query) if k.lower() not in TRACKING_PARAMS))
    return urlunsplit((scheme, netloc, path, query, ""))


def url_hash(url: str) -> str:
    return hashlib.sha256(canonicalize_url(url).encode("utf-8")).hexdigest()


def _parse_iso_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def normalize_gnews(article: dict[str, Any], source_name: str = "gnews") -> dict[str, Any]:
    """Map one GNews article object onto the common staging schema."""
    url = article.get("url", "")
    return {
        "source_type": "news",
        "source_name": source_name,
        "external_id": url_hash(url),
        "url": canonicalize_url(url),
        "title": article.get("title", "").strip(),
        "raw_text": (article.get("description") or "").strip(),
        "published_at": _parse_iso_datetime(article["publishedAt"]),
        "fetched_at": datetime.now(timezone.utc),
    }


def normalize(raw_item: dict[str, Any], source_type: str) -> dict[str, Any]:
    """Dispatch to the per-source normalizer. Raises for unknown sources."""
    if source_type == "news":
        return normalize_gnews(raw_item)
    raise ValueError(f"No normalizer implemented for source_type={source_type!r}")
