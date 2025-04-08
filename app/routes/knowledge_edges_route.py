# app/routes/graph.py
from fastapi import APIRouter, Depends
from typing import List, Optional
from uuid import UUID

from app.auth import verify_token
from app.function.memory_extraction import MemoryResponse
from app.supabase.knowledge_edges import get_connected_memories, simplify_related_memories



router = APIRouter()

@router.get("/related-memories")
async def related_memories(
    source_id: UUID,
    user_id: UUID,
    relation_type: Optional[str] = None,
    min_score: float = 0.75
):
    """
    Get related memories connected by knowledge edges.

    Params:
    - source_id: ID of the memory node you're starting from
    - relation_type: Filter by relationship type (optional)
    - min_score: Minimum similarity score (default 0.75)

    Returns:
    - List of memory records from user_knowledge
    """
    #user_id = user["id"]
    results = get_connected_memories(user_id, source_id, relation_type, min_score)
    return results
