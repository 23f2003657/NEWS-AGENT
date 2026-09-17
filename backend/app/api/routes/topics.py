"""GET /topics/{name}/graph — Neo4j topic subgraph for the graph explorer."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/{name}/graph")
def get_topic_graph(name: str):
    raise NotImplementedError
