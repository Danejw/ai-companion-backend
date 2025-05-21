#!/usr/bin/env python3

from pathlib import Path
import json
import os
from typing import List, Dict, Any
from typing_extensions import TypedDict


# Define types
class Entity(TypedDict):
    name: str
    entityType: str
    observations: List[str]
    content: str


class Relation(TypedDict):
    from_: str  # Using from_ to avoid Python keyword
    to: str
    relationType: str


class KnowledgeGraph(TypedDict):
    entities: List[Entity]
    relations: List[Relation]


class KnowledgeGraphManager:
    def __init__(self):
        self._cache: KnowledgeGraph = {"entities": [], "relations": []}

    async def load_graph(self) -> KnowledgeGraph:
        return self._cache

    async def save_graph(self, graph: KnowledgeGraph):
        self._cache = graph

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        new_entities = [
            e for e in entities 
            if not any(existing.get("name") == e["name"] for existing in self._cache["entities"])
        ]
        self._cache["entities"].extend(new_entities)
        return new_entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        new_relations = [
            r for r in relations 
            if not any(
                existing.get("from_") == r["from_"] 
                and existing.get("to") == r["to"] 
                and existing.get("relationType") == r["relationType"] 
                for existing in self._cache["relations"]
            )
        ]
        self._cache["relations"].extend(new_relations)
        return new_relations

    async def add_observations(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for obs in observations:
            entity = next((e for e in self._cache["entities"] if e["name"] == obs["entityName"]), None)
            if not entity:
                raise ValueError(f"Entity with name {obs['entityName']} not found")
            new_observations = [content for content in obs["contents"] if content not in entity["observations"]]
            entity["observations"].extend(new_observations)
            results.append({"entityName": obs["entityName"], "addedObservations": new_observations})
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        self._cache["entities"] = [e for e in self._cache["entities"] if e["name"] not in entity_names]
        self._cache["relations"] = [
            r for r in self._cache["relations"]
            if r["from_"] not in entity_names and r["to"] not in entity_names
        ]

    async def delete_observations(self, deletions: List[Dict[str, Any]]) -> None:
        for deletion in deletions:
            entity = next((e for e in self._cache["entities"] if e["name"] == deletion["entityName"]), None)
            if entity:
                entity["observations"] = [
                    obs for obs in entity["observations"]
                    if obs not in deletion["observations"]
                ]

    async def delete_relations(self, relations: List[Relation]) -> None:
        self._cache["relations"] = [
            r for r in self._cache["relations"]
            if not any(
                r["from_"] == del_rel["from_"]
                and r["to"] == del_rel["to"]
                and r["relationType"] == del_rel["relationType"]
                for del_rel in relations
            )
        ]

    async def read_graph(self) -> KnowledgeGraph:
        return self._cache

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        query = query.lower()
        filtered_entities = [
            e for e in self._cache["entities"]
            if query in e["name"].lower()
            or query in e["entityType"].lower()
            or any(query in obs.lower() for obs in e["observations"])
        ]
        filtered_entity_names = {e["name"] for e in filtered_entities}
        filtered_relations = [
            r for r in self._cache["relations"]
            if r["from_"] in filtered_entity_names and r["to"] in filtered_entity_names
        ]
        return {"entities": filtered_entities, "relations": filtered_relations}

    async def open_nodes(self, names: List[str]) -> KnowledgeGraph:
        filtered_entities = [e for e in self._cache["entities"] if e["name"] in names]
        filtered_entity_names = {e["name"] for e in filtered_entities}
        filtered_relations = [
            r for r in self._cache["relations"]
            if r["from_"] in filtered_entity_names and r["to"] in filtered_entity_names
        ]
        return {"entities": filtered_entities, "relations": filtered_relations}