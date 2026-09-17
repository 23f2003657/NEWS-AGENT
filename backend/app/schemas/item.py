"""Pydantic request/response schemas for Item."""
from pydantic import BaseModel

class ItemOut(BaseModel):
    id: str
    title: str
    url: str
    story_id: str | None = None
