"""GET /stories and /stories/{id}/timeline — story list and chronological chapters."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def list_stories():
    raise NotImplementedError

@router.get("/{story_id}/timeline")
def get_timeline(story_id: str):
    raise NotImplementedError
