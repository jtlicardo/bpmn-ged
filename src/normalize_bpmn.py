from openai import OpenAI
from pydantic import BaseModel
from typing import List
from schemas import BPMNGraph, NormalizedBPMNGraph, NormalizedNode, NormalizedEdge
from parse_bpmn import parse_bpmn
from dotenv import load_dotenv
import os
import json
from datetime import datetime

class NormalizationRequest(BaseModel):
    g1: List[dict]  # first graph nodes
    g2: List[dict]  # second graph nodes
    e1: List[dict]  # first graph edges
    e2: List[dict]  # second graph edges

class EdgeNormalizationMapping(BaseModel):
    original_name: str | None
    normalized_name: str | None

class NodeNormalizationMapping(BaseModel):
    original_name: str
    normalized_name: str

class NormalizationResponse(BaseModel):
    node_mappings: List[NodeNormalizationMapping]
    edge_mappings: List[EdgeNormalizationMapping]

PROMPT = """Normalize BPMN tasks, events, and sequence flow labels:
- Match semantically similar tasks, events, and flow labels
- Use 'A', 'B', 'C', etc. as normalized names for tasks and events
- Use '1', '2', '3', etc. as normalized names for flow labels
- Only output original_name and normalized_name pairs
- Same tasks/events/labels get same normalized names ONLY if they are semantically similar
- Different/unrelated tasks/events MUST get different normalized names
- Consider node sequence via edges"""

def create_normalized_graph(graph: BPMNGraph, node_mapping: dict, edge_mapping: dict) -> NormalizedBPMNGraph:
    """
    Create a normalized graph from the given graph using the provided node and edge mappings.
    """
    normalized_nodes = []
    for node in graph.nodes:
        normalized_node = NormalizedNode(
            id=node.id,
            type=node.type,
            original_name=node.name,
            normalized_name=node_mapping.get(node.name) if node.name else None
        )
        normalized_nodes.append(normalized_node)
    
    normalized_edges = []
    for edge in graph.edges:
        normalized_edge = NormalizedEdge(
            source=edge.source,
            target=edge.target,
            original_name=edge.name,
            normalized_name=edge_mapping.get(edge.name) if edge.name else None
        )
        normalized_edges.append(normalized_edge)
    
    return NormalizedBPMNGraph(nodes=normalized_nodes, edges=normalized_edges)

def normalize_graphs(graph1: BPMNGraph, graph2: BPMNGraph, model: str = "gpt-4o-mini") -> tuple[NormalizedBPMNGraph, NormalizedBPMNGraph]:
    load_dotenv(override=True)
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    request = NormalizationRequest(
        g1=[n.model_dump() for n in graph1.nodes],
        g2=[n.model_dump() for n in graph2.nodes],
        e1=[e.model_dump() for e in graph1.edges],
        e2=[e.model_dump() for e in graph2.edges]
    )

    completion_args = {
        "model": model,
        "messages": [
            {"role": "developer", "content": PROMPT},
            {"role": "user", "content": str(request.model_dump())}
        ],
        "response_format": NormalizationResponse
    }

    if model == "o3-mini":
        completion_args["reasoning_effort"] = "low"

    completion = client.beta.chat.completions.parse(**completion_args)

    print(f"Input tokens: {completion.usage.prompt_tokens}")
    print(f"Reasoning tokens: {completion.usage.completion_tokens_details.reasoning_tokens}")
    print(f"Output tokens: {completion.usage.completion_tokens}")

    # Create normalized graphs using the mappings from LLM
    node_mapping = {m.original_name: m.normalized_name for m in completion.choices[0].message.parsed.node_mappings}
    edge_mapping = {m.original_name: m.normalized_name for m in completion.choices[0].message.parsed.edge_mappings}

    graph1_normalized = create_normalized_graph(graph1, node_mapping, edge_mapping)
    graph2_normalized = create_normalized_graph(graph2, node_mapping, edge_mapping)

    # Save normalized graphs with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"normalized_{timestamp}.json"
    
    normalized_graphs = {
        "graph1": graph1_normalized.model_dump(),
        "graph2": graph2_normalized.model_dump()
    }
    
    with open(filename, "w") as f:
        json.dump(normalized_graphs, f, indent=2)
    
    print(f"Normalized graphs saved to {filename}")

    return graph1_normalized, graph2_normalized


if __name__ == "__main__":
    graph1 = parse_bpmn("models/first.bpmn")
    graph2 = parse_bpmn("models/second.bpmn")
    _, _ = normalize_graphs(graph1, graph2)

