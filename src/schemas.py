from typing import List

from pydantic import BaseModel

class Node(BaseModel):
    id: str
    type: str
    name: str | None = None

class Edge(BaseModel):
    source: str
    target: str
    name: str | None = None

class BPMNGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class NormalizedNode(BaseModel):
    id: str
    type: str
    original_name: str | None = None
    normalized_name: str | None = None

class NormalizedEdge(BaseModel):
    source: str
    target: str
    original_name: str | None = None
    normalized_name: str | None = None


class NormalizedBPMNGraph(BaseModel):
    nodes: List[NormalizedNode]
    edges: List[NormalizedEdge]
