"""Cypher queries: timeline reconstruction, topic subgraph fetch, story/chapter writes."""

TIMELINE_QUERY = """
MATCH (s:Story {id: $storyId})-[:HAS_CHAPTER]->(i:Item)
RETURN i.title, i.published_at, i.id
ORDER BY i.published_at ASC
"""
