"""SQLAlchemy models: Item, Story (see HLD/LLD section 2.1 for full column list)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase

# Dialect-agnostic types: real Postgres types in prod, SQLite-friendly fallbacks in tests.
UUIDType = UUID(as_uuid=True).with_variant(String(36), "sqlite")
TagsType = ARRAY(Text).with_variant(JSON, "sqlite")


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(timezone.utc)


def new_id():
    return str(uuid.uuid4())


class Item(Base):
    """A single ingested piece of content (news article / paper / tool release)."""

    __tablename__ = "items"

    id = Column(UUIDType, primary_key=True, default=new_id)
    source_type = Column(String, nullable=False)  # news / paper / tool
    source_name = Column(String, nullable=False)  # e.g. "gnews" — stays a text field for extensibility
    external_id = Column(String, nullable=False, unique=True, index=True)  # canonical URL hash / arXiv ID / release tag
    title = Column(Text, nullable=False)
    raw_text = Column(Text)
    url = Column(Text)
    published_at = Column(DateTime(timezone=True), nullable=False)
    ingested_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    story_id = Column(UUIDType, ForeignKey("stories.id"), nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(TagsType, nullable=True)


class Story(Base):
    """An evolving storyline; items attach to it as chapters (see LLD 2.1)."""

    __tablename__ = "stories"

    id = Column(UUIDType, primary_key=True, default=new_id)
    title = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="active")  # active / dormant / resolved
    first_seen_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    last_updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    centroid_embedding_id = Column(String, nullable=True)  # pointer to Chroma story-centroid vector
    item_count = Column(Integer, nullable=False, default=0)


class PollCursor(Base):
    """Per-source last-successful-poll timestamp (LLD 2.2-A cursor persistence)."""

    __tablename__ = "poll_cursors"

    source = Column(String, primary_key=True)  # e.g. "gnews", "arxiv", "github"
    last_polled_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
