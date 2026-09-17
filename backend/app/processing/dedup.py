"""Exact dedup: canonical URL/ID hashing against the items.external_id unique key."""
from sqlalchemy import select

from app.db.models import Item
from app.db.postgres import SessionLocal


def is_exact_duplicate(external_id: str) -> bool:
    with SessionLocal() as db:
        return db.scalar(select(Item.id).where(Item.external_id == external_id).limit(1)) is not None


def insert_new_items(items: list[dict]) -> int:
    """Insert only items whose external_id we haven't seen. Idempotent on re-polls.

    Batch-fetch existing IDs once instead of querying per item.
    """
    if not items:
        return 0
    ids = {i["external_id"] for i in items}
    with SessionLocal() as db:
        existing = set(db.scalars(select(Item.external_id).where(Item.external_id.in_(ids))))
        seen = set()
        rows = []
        for i in items:
            if i["external_id"] in existing or i["external_id"] in seen:
                continue  # already in DB or duplicated within this batch
            seen.add(i["external_id"])
            rows.append(
                Item(
                    source_type=i["source_type"],
                    source_name=i["source_name"],
                    external_id=i["external_id"],
                    title=i["title"],
                    raw_text=i["raw_text"],
                    url=i["url"],
                    published_at=i["published_at"],
                    ingested_at=i["fetched_at"],
                )
            )
        db.add_all(rows)
        db.commit()
        return len(rows)
