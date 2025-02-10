import networkx as nx

from schemas import NormalizedBPMNGraph


def to_digraph(graph_data: NormalizedBPMNGraph) -> nx.DiGraph:
    """
    Convert the given NormalizedBPMNGraph structure into a directed graph (DiGraph).
    """
    json_data = graph_data.model_dump()

    G = nx.DiGraph()

    for node in json_data.get("nodes", []):
        node_id = node["id"]
        attrs = {k: v for k, v in node.items() if k != "id"}
        G.add_node(node_id, **attrs)

    for edge in json_data.get("edges", []):
        source = edge["source"]
        target = edge["target"]
        attrs = {k: v for k, v in edge.items() if k not in ["source", "target"]}
        G.add_edge(source, target, **attrs)

    return G



def edge_match(e1: dict, e2: dict) -> bool:
    """
    Compare if two edges are equal based on their attributes.
    Returns True if the edges should be considered equal, False otherwise.
    """
    return e1["normalized_name"] == e2["normalized_name"]


def node_subst_cost(n1: dict, n2: dict) -> float:
    """
    Calculate the substitution cost between two nodes.
    Returns:
    - 0.0: perfect match (same type and normalized name)
    - 0.5: partial match (different type but same normalized name)
    - 1.0: complete mismatch
    """
    name_match = n1["normalized_name"] == n2["normalized_name"]
    type_match = n1["type"] == n2["type"]
    
    if name_match and type_match:
        return 0.0
    elif name_match:  # Only names match, types are different
        return 0.5
    return 1.0


def node_ins_cost(n: dict) -> float:
    return 1.0


def node_del_cost(n: dict) -> float:
    return 1.0


def compute_ged(json_graph_1: NormalizedBPMNGraph, json_graph_2: NormalizedBPMNGraph) -> float:
    """
    Compute the Graph Edit Distance (GED) between two graphs given in JSON format.
    """
    G1 = to_digraph(json_graph_1)
    G2 = to_digraph(json_graph_2)
    return nx.algorithms.similarity.graph_edit_distance(
        G1, G2, 
        node_subst_cost=node_subst_cost,
        node_ins_cost=node_ins_cost,
        node_del_cost=node_del_cost,
        edge_match=edge_match,
        timeout=10.0
    )


def compute_rged(json_graph_1: NormalizedBPMNGraph, json_graph_2: NormalizedBPMNGraph) -> float:
    """
    Compute the Relative Graph Edit Distance (Relative GED) between two graphs given in JSON format.
    Relative GED = (GED(G1, G2) / (GED(G1, Empty) + GED(G2, Empty)))
    """
    empty_graph = NormalizedBPMNGraph(nodes=[], edges=[])

    ged_G1_G2 = compute_ged(json_graph_1, json_graph_2)
    ged_G1_empty = compute_ged(json_graph_1, empty_graph)
    ged_G2_empty = compute_ged(json_graph_2, empty_graph)

    return ged_G1_G2 / (ged_G1_empty + ged_G2_empty)
