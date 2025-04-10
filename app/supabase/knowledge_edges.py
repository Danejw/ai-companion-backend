# app/models/knowledge_edge.py
import json
import logging
import os
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import UUID
from supabase import create_client
from uuid import UUID
import datetime
from app.utils.similarity import cosine_similarity



SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)



# Only create edges if the similarity score is above or equal to this threshold
SIMILARITY_THRESHOLD = 0.8  # adjust as needed


class KnowledgeEdge(BaseModel):
    user_id: UUID
    source_id: UUID  # id of the memory where the edge originated
    target_id: UUID  # id of the memory being connected
    similarity_score: float
    relation_type: Optional[List[str]] = "semantic_similarity"
    notes: Optional[str] = None
    created_at: Optional[str] = None  # Will default in DB
    
    
"""
RELATION TYPE EXPLANATION:

# Cognitive / Reflective Relations:
- recalls:  If both memories are personal disclosures and share overlapping topics or language_style is “reflective”.
- self_reference: If self_awareness is true in both and they share similar tone or concern (like importance, recurring themes).
- builds_on: If both are recurring_theme and the second memory is newer (timestamp comparison) and topic-aligned.
- evolves: Same as builds_on, but sentiment_score has shifted—shows growth or change in tone over time.

# Emotional Relations:
- emotionally_linked: If emotional_intensity matches (like both “high”) and they share a topic or tone.
- emotional_shift: If sentiment_score moves drastically between two closely timed memories (e.g. 0.7 to -0.5), suggesting a pivot or emotional swing.
- comfort_zone: If a memory has high importance and shows a habit (ritual), link to others with lower intensity as grounding nodes.

# Contradiction & Tension:
- contradicts: If sentiment scores are opposite signs and topics match (e.g. one positive, one negative about "friendship").
- boundary_violation: If one memory has boundary_discussion = true and the other is emotionally intense or has a negative sentiment. Indicates a topic crossing a comfort line.

# Structural / Pattern-Based:
- habitual: If both are ritual and mention the same topic. Shows repetition or a pattern.
- reaffirms:  If two memories have very similar embeddings + high importance + same sentiment score direction. Could indicate the user repeating a belief or experience to themselves.

# Topic Clustering:
- topic_cluster:  If topics overlap heavily (e.g., 2 out of 3 match), they’re topically connected even if sentiment or intensity differ.

# Temporal Relation:
- time_linked: Memories created within a short time window, suggesting proximity or clustering in experience.

"""

def get_relation_type(memory_a: Dict, memory_b: Dict) -> List[str]:
    relation_types = []

    # Print out metadata if needed
    # try:
    #     # Remove embeddings and format JSON
    #     a_clean = json.dumps({k: v for k, v in memory_a.items() if k != "embedding"}, indent=2).splitlines()
    #     b_clean = json.dumps({k: v for k, v in memory_b.items() if k != "embedding"}, indent=2).splitlines()

    #     max_lines = max(len(a_clean), len(b_clean))
    #     a_clean += [""] * (max_lines - len(a_clean))
    #     b_clean += [""] * (max_lines - len(b_clean))

    #     print("\n🧠 Source vs Target Metadata:")
    #     print(f"{'SOURCE':<50} || {'TARGET'}")
    #     print("-" * 100)

    #     for line_a, line_b in zip(a_clean, b_clean):
    #         print(f"{line_a:<50} || {line_b}")

    # except Exception as e:
    #     print("⚠️ Error pretty-printing metadata:", e)
    
    

    # --- Cognitive / Reflective Relations ---
    # Recall
    if memory_a.get("disclosure") and memory_b.get("disclosure") and set(memory_a.get("topics", [])) & set(memory_b.get("topics", [])):
        if memory_a.get("language_style") == "reflective" and memory_b.get("language_style") == "reflective":
            relation_types.append("recalls")
            
    # Self-Reference
    if memory_a.get("self_awareness") and memory_b.get("self_awareness"):
        relation_types.append("self_reference")
        
    # Evolves
    if memory_a.get("recurring_theme") and memory_b.get("recurring_theme") and set(memory_a.get("topics", [])) & set(memory_b.get("topics", [])):
        if memory_b.get("timestamp") > memory_a.get("timestamp"):
            relation_types.append("builds_on")
            if abs(memory_a.get("sentiment_score", 0) - memory_b.get("sentiment_score", 0)) > 0.5:
                relation_types.append("evolves")

    # --- Emotional Relations ---
    # Emotionally Linked
    if memory_a.get("emotional_intensity") == memory_b.get("emotional_intensity") and set(memory_a.get("topics", [])) & set(memory_b.get("topics", [])):
        relation_types.append("emotionally_linked")
        
    # Emotional Shift
    if abs(memory_a.get("sentiment_score", 0) - memory_b.get("sentiment_score", 0)) > 0.6 and set(memory_a.get("topics", [])) & set(memory_b.get("topics", [])):
        relation_types.append("emotional_shift")
        
    # Comfort Zone
    if (memory_a.get("ritual") and memory_a.get("emotional_intensity") == "low" and memory_a.get("sentiment_score", 0) >= 0 and memory_b.get("emotional_intensity") == "high"):
        relation_types.append("comfort_zone")

    # --- Contradiction & Tension ---
    # Contradicts
    if memory_a.get("sentiment_score", 0) * memory_b.get("sentiment_score", 0) < 0 and set(memory_a.get("topics", [])) & set(memory_b.get("topics", [])):
        relation_types.append("contradicts")
        
    # Boundary Violation
    if memory_a.get("boundary_discussion") and memory_b.get("emotional_intensity") == "high":
        relation_types.append("boundary_violation")

    # --- Structural / Pattern-Based ---
    # Habitual
    if memory_a.get("ritual") and memory_b.get("ritual") and set(memory_a.get("topics", [])) & set(memory_b.get("topics", [])):
        relation_types.append("habitual")
        
    # Reaffirms
    if (set(memory_a.get("topics", [])) & set(memory_b.get("topics", [])) and abs(memory_a.get("sentiment_score", 0) - memory_b.get("sentiment_score", 0)) < 0.1 and abs(memory_a.get("importance", 0) - memory_b.get("importance", 0)) < 0.1):
        relation_types.append("reaffirms")

    # --- Topic Clustering ---
    # Topic Cluster
    shared_topics = set(memory_a.get("topics", [])) & set(memory_b.get("topics", []))
    if len(shared_topics) >= 2:
        relation_types.append("topic_cluster")
        
    # --- Temporal Relation ---
    # Time Linked
    try:
        time_a = datetime.fromisoformat(memory_a.get("timestamp"))
        time_b = datetime.fromisoformat(memory_b.get("timestamp"))
        time_diff = abs((time_b - time_a).days)

        if 0 < time_diff <= 3:  # In Days, adjust range for your needs
            relation_types.append("time_linked")
    except Exception:
        pass  # Fallback in case timestamps are missing or malformed
    
    # fallback
    if not relation_types:
        relation_types.append("semantic_similarity")

    return relation_types


def create_knowledge_edges(user_id: UUID, source_id: UUID, source_embedding: List[float], source_metadata: dict, top_k: int = 5):
    try:
        # 1. Get all other memories for this user
        response = supabase.table("user_knowledge") \
            .select("id, embedding, metadata") \
            .eq("user_id", str(user_id)) \
            .neq("id", str(source_id)) \
            .execute()
            
        memories = response.data or []
        if not memories:
            return
        
        # 2. Compute similarity scores
        scored = []
        for mem in memories:
            target_id = UUID(mem["id"])
            target_embedding = json.loads(mem["embedding"])
            score = cosine_similarity(source_embedding, target_embedding)
            
            if score >= SIMILARITY_THRESHOLD and target_id != source_id:
                scored.append((target_id, score))
        
        # 3. Sort and filter top K
        scored.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored[:top_k]
        
        # Now print only what you're going to insert
        for target_id, score in top_matches:
            print(f"Edge to insert — Target ID: {target_id}, Score: {score}")

        # 4. Insert edges (skip duplicates)
        for target_id, score in top_matches:
            
            target_row = next((m for m in memories if UUID(m["id"]) == target_id), None)
            if not target_row:
                continue

            # convert metadata to dict if not already
            target_metadata_raw = target_row.get("metadata")
            if isinstance(target_metadata_raw, str):
                target_metadata = json.loads(target_metadata_raw)
            elif isinstance(target_metadata_raw, dict):
                target_metadata = target_metadata_raw
            else:
                target_metadata = {} 
            
                      
            existing = supabase.table("knowledge_edges") \
                .select("id") \
                .eq("user_id", str(user_id)) \
                .eq("source_id", str(source_id)) \
                .eq("target_id", str(target_id)) \
                .execute()
            
            if existing.data:
                continue  # already exists
            
            relation_type = get_relation_type(source_metadata, target_metadata)

            supabase.table("knowledge_edges").insert({
                "user_id": str(user_id),
                "source_id": str(source_id),
                "target_id": str(target_id),
                "similarity_score": score,
                "relation_type": relation_type
            }).execute()

    except Exception as e:
        logging.error(f"Error creating knowledge edges: {e}")
                
        
def get_connected_memories(user_id: UUID, source_id: UUID, relation_type: Optional[str] = None, min_score: float = 0.75):
    """
    Retrieves memories connected to the given source_id via semantic edges.

    Args:
        user_id: ID of the user
        source_id: ID of the memory to start from
        relation_type: Optional filter for type of connection
        min_score: Minimum similarity score to consider

    Returns:
        List of connected memory rows from user_knowledge
    """
    filters = (
        supabase.table("knowledge_edges")
        .select("target_id")
        .eq("user_id", str(user_id))
        .eq("source_id", str(source_id))
        .gte("similarity_score", min_score)
    )

    if relation_type:
        filters = filters.eq("relation_type", relation_type)

    edge_response = filters.execute()

    target_ids = [edge["target_id"] for edge in edge_response.data]

    if not target_ids:
        return []

    memory_response = (
        supabase.table("user_knowledge")
        .select("*")
        .in_("id", target_ids)
        .execute()
    )

    # return a filtered list of connected memories
    simplified_response = simplify_related_memories(memory_response.data)
    return simplified_response


class SimplifiedMemory(BaseModel):
    date: str
    text: str

def simplify_related_memories(memories: List[Dict]) -> List[SimplifiedMemory]:
    simplified = []

    for memory in memories: 
        if "id" in memory and "knowledge_text" in memory:
            readable_date = ""
            try:
                # Parse metadata if it's a string
                metadata = memory.get("metadata", {})
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                
                if "timestamp" in metadata:
                    dt = datetime.datetime.fromisoformat(metadata["timestamp"])
                    readable_date = dt.strftime("%b %d, %Y")  # e.g. "Apr 07, 2025"
            except Exception as e:
                logging.error(f"Error parsing date: {e}")
                pass  # fallback if timestamp is malformed

            simplified.append(SimplifiedMemory(date=readable_date, text=memory["knowledge_text"]))

    return simplified

