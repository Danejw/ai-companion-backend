#!/usr/bin/env python3

from mcp.server.fastmcp import FastMCP
from .knowledge_graph import KnowledgeGraphManager, Entity, Relation, KnowledgeGraph
from typing import List, Dict, Any

# Create FastMCP server
mcp = FastMCP("Memory Graph", dependencies=["mcp"])

# Initialize knowledge graph manager
knowledge_graph = KnowledgeGraphManager()


@mcp.tool()
async def create_entities(entities: List[Entity]) -> List[Entity]:
    """Create multiple new entities in the knowledge graph.

    Args:
        entities: List of entities to create, each with name, type and observations

    Returns:
        List of newly created entities (excluding any that already existed)
    """
    return await knowledge_graph.create_entities(entities)


@mcp.tool()
async def create_relations(relations: List[Relation]) -> List[Relation]:
    """Create new relations between entities in the knowledge graph.

    Args:
        relations: List of relations to create, each with from_, to and relationType

    Returns:
        List of newly created relations (excluding any duplicates)
    """
    return await knowledge_graph.create_relations(relations)


@mcp.tool()
async def add_observations(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add new observations to existing entities.

    Args:
        observations: List of observations to add, each with entityName and contents

    Returns:
        List of results showing which observations were added to which entities
    """
    return await knowledge_graph.add_observations(observations)


@mcp.tool()
async def delete_entities(entity_names: List[str]) -> None:
    """Delete entities and their associated relations from the graph.

    Args:
        entity_names: List of entity names to delete
    """
    await knowledge_graph.delete_entities(entity_names)


@mcp.tool()
async def delete_observations(deletions: List[Dict[str, Any]]) -> None:
    """Delete specific observations from entities.

    Args:
        deletions: List of deletions, each with entityName and observations to remove
    """
    await knowledge_graph.delete_observations(deletions)


@mcp.tool()
async def delete_relations(relations: List[Relation]) -> None:
    """Delete specific relations from the graph.

    Args:
        relations: List of relations to delete
    """
    await knowledge_graph.delete_relations(relations)


@mcp.tool()
async def read_graph() -> KnowledgeGraph:
    """Read the entire knowledge graph.

    Returns:
        The complete knowledge graph with all entities and relations
    """
    return await knowledge_graph.read_graph()


@mcp.tool()
async def search_nodes(query: str) -> KnowledgeGraph:
    """Search for nodes and their relations matching a query string.

    Args:
        query: Search string to match against node names, types and observations

    Returns:
        Subgraph containing matching entities and their interconnecting relations
    """
    return await knowledge_graph.search_nodes(query)


@mcp.tool()
async def open_nodes(names: List[str]) -> KnowledgeGraph:
    """Get a subgraph containing specific nodes and their interconnecting relations.

    Args:
        names: List of entity names to include

    Returns:
        Subgraph containing the specified entities and relations between them
    """
    return await knowledge_graph.open_nodes(names)

