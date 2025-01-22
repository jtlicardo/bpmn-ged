from typing import List

from pydantic import BaseModel


class Node(BaseModel):
    id: str
    type: str
    name: str | None = None


class Edge(BaseModel):
    source: str
    target: str


class BPMNGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
