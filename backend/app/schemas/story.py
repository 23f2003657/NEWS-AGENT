"""Pydantic request/response schemas for Story and its timeline."""
from pydantic import BaseModel

class StoryOut(BaseModel):
    id: str
    title: str
    status: str
    item_count: int
