"""FastAPI application entrypoint. Wires up routers and startup/shutdown events."""
from fastapi import FastAPI
from app.api.routes import feed, stories, topics

app = FastAPI(title="AI News Agent")
app.include_router(feed.router, prefix="/feed", tags=["feed"])
app.include_router(stories.router, prefix="/stories", tags=["stories"])
app.include_router(topics.router, prefix="/topics", tags=["topics"])
