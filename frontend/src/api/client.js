// Thin fetch wrapper for the FastAPI backend: getFeed, getStories, getTimeline, getTopicGraph.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getFeed() { /* GET /feed */ }
export async function getStories() { /* GET /stories */ }
export async function getTimeline(storyId) { /* GET /stories/{id}/timeline */ }
export async function getTopicGraph(name) { /* GET /topics/{name}/graph */ }
