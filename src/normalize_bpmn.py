from openai import OpenAI
from pydantic import BaseModel
from typing import List
from schemas import BPMNGraph, NormalizedBPMNGraph, NormalizedNode, NormalizedEdge
from parse_bpmn import parse_bpmn
from dotenv import load_dotenv
import os
import json

class NormalizationRequest(BaseModel):
    g1: List[dict]  # first graph nodes
    g2: List[dict]  # second graph nodes
    e1: List[dict]  # first graph edges
    e2: List[dict]  # second graph edges



class NormalizationMapping(BaseModel):
    original_name: str
    normalized_name: str

class NormalizationResponse(BaseModel):
    name_mappings: List[NormalizationMapping]

MODEL = "gpt-5-mini"

PROMPT = """Normalize BPMN task, event, and sequence flow labels by mapping them to simple letter names (A, B, C, etc.):
- Match semantically similar elements (tasks, events, flows)
- Use ONLY letters (A, B, C, etc.) as normalized names for ALL elements
- Same elements get same letters ONLY if they are semantically similar
- Different/unrelated elements MUST get different letters
- Consider element sequence via edges
- Only normalize elements that have labels/names - ignore unlabeled elements
- Do not normalize IDs, only normalize labels/names

Examples:

Input:
{
  "g1": [
    {"name": "Submit order", "type": "task", "id": "1"},
    {"name": "Process payment", "type": "task", "id": "2"}
  ],
  "g2": [
    {"name": "Send order", "type": "task", "id": "task_1"},
    {"name": "Handle payment", "type": "task", "id": "task_2"}
  ],
  "e1": [
    {"name": "Order submitted", "source": "1", "target": "2"}
  ],
  "e2": [
    {"name": "Order sent", "source": "task_1", "target": "task_2"}
  ]
}

Expected Output:
{
  "name_mappings": [
    {"original_name": "Submit order", "normalized_name": "A"},
    {"original_name": "Send order", "normalized_name": "A"},
    {"original_name": "Process payment", "normalized_name": "B"},
    {"original_name": "Handle payment", "normalized_name": "B"},
    {"original_name": "Order submitted", "normalized_name": "C"},
    {"original_name": "Order sent", "normalized_name": "C"}
  ]
}"""

def create_normalized_graph(graph: BPMNGraph, name_mapping: dict) -> NormalizedBPMNGraph:
    """
    Create a normalized graph from the given graph using the provided name mappings.
    """
    normalized_nodes = []
    for node in graph.nodes:
        normalized_node = NormalizedNode(
            id=node.id,
            type=node.type,
            original_name=node.name,
            normalized_name=name_mapping.get(node.name) if node.name else None
        )
        normalized_nodes.append(normalized_node)
    
    normalized_edges = []
    for edge in graph.edges:
        normalized_edge = NormalizedEdge(
            source=edge.source,
            target=edge.target,
            original_name=edge.name,
            normalized_name=name_mapping.get(edge.name) if edge.name else None
        )
        normalized_edges.append(normalized_edge)
    
    return NormalizedBPMNGraph(nodes=normalized_nodes, edges=normalized_edges)

def normalize_graphs(graph1: BPMNGraph, graph2: BPMNGraph, source_file: str) -> tuple[NormalizedBPMNGraph, NormalizedBPMNGraph]:
    load_dotenv(override=True)
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    request = NormalizationRequest(
        g1=[n.model_dump() for n in graph1.nodes],
        g2=[n.model_dump() for n in graph2.nodes],
        e1=[e.model_dump() for e in graph1.edges],
        e2=[e.model_dump() for e in graph2.edges]
    )

    completion_args = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": str(request.model_dump())}
        ],
        "response_format": NormalizationResponse
    }


    completion = client.beta.chat.completions.parse(**completion_args)

    # print(f"Input tokens: {completion.usage.prompt_tokens}")
    # print(f"Reasoning tokens: {completion.usage.completion_tokens_details.reasoning_tokens}")
    print(f"Output tokens: {completion.usage.completion_tokens}")

    # Create normalized graphs using the mappings from LLM
    name_mapping = {m.original_name: m.normalized_name for m in completion.choices[0].message.parsed.name_mappings}

    graph1_normalized = create_normalized_graph(graph1, name_mapping)
    graph2_normalized = create_normalized_graph(graph2, name_mapping)

    # Create normalized_graphs directory if it doesn't exist
    output_dir = "normalized_graphs"
    os.makedirs(output_dir, exist_ok=True)

     # Extract base filename without extension and path
    base_filename = os.path.splitext(os.path.basename(source_file))[0]
    filename = os.path.join(output_dir, f"{base_filename}_normalized.json")
    
    output_data = {
        "graph1": graph1_normalized.model_dump(),
        "graph2": graph2_normalized.model_dump(),
        "mappings": name_mapping
    }
    
    with open(filename, "w") as f:
        json.dump(output_data, f, indent=2)
    
    return graph1_normalized, graph2_normalized


if __name__ == "__main__":
    graph1 = parse_bpmn("models/first.bpmn")
    graph2 = parse_bpmn("models/second.bpmn")
    _, _ = normalize_graphs(graph1, graph2, "models/first.bpmn")
