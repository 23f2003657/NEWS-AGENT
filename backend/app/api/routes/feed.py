"""GET /feed — paginated items newest-first, annotated with story_id/story_title."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def get_feed():
    raise NotImplementedError
