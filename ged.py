import networkx as nx


def json_to_digraph(json_data):
    """
    Convert the given JSON graph structure into a directed graph (DiGraph).
    Expected JSON format:
    {
      "nodes": [
        {"id": "Node_1", ... },
        ...
      ],
      "edges": [
        {"source": "Node_1", "target": "Node_2"},
        ...
      ]
    }
    """
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


def node_match(n1, n2):
    """
    Compare if two nodes are equal based on their attributes.
    Returns True if the nodes should be considered equal, False otherwise.
    """
    if "type" in n1 and "type" in n2:
        if n1["type"] != n2["type"]:
            return False

    if "name" in n1 and "name" in n2:
        if n1["name"] != n2["name"]:
            return False

    return True


def compute_ged(json_graph_1, json_graph_2):
    """
    Compute the Graph Edit Distance (GED) between two graphs given in JSON format.
    """
    G1 = json_to_digraph(json_graph_1)
    G2 = json_to_digraph(json_graph_2)

    return nx.algorithms.similarity.graph_edit_distance(G1, G2, node_match=node_match)


if __name__ == "__main__":
    graph_json_1 = {
        "nodes": [
            {"id": "StartEvent_1", "type": "startEvent"},
            {"id": "Activity_14k7ctp", "type": "task", "name": "Write draft"},
            {"id": "Gateway_1p0lqz7", "type": "parallelGateway"},
            {"id": "Activity_10dlls5", "type": "task", "name": "Contact publisher"},
            {"id": "Activity_08pijh0", "type": "task", "name": "Process payment"},
            {"id": "Gateway_0hkn0t9", "type": "parallelGateway"},
            {"id": "Event_05ig0cp", "type": "endEvent"},
        ],
        "edges": [
            {"source": "StartEvent_1", "target": "Activity_14k7ctp"},
            {"source": "Activity_14k7ctp", "target": "Gateway_1p0lqz7"},
            {"source": "Gateway_1p0lqz7", "target": "Activity_10dlls5"},
            {"source": "Gateway_1p0lqz7", "target": "Activity_08pijh0"},
            {"source": "Activity_08pijh0", "target": "Gateway_0hkn0t9"},
            {"source": "Activity_10dlls5", "target": "Gateway_0hkn0t9"},
            {"source": "Gateway_0hkn0t9", "target": "Event_05ig0cp"},
        ],
    }

    # Deleted the end event and its incoming edge -> GED = 2
    # Changed the start event type -> GED = 1
    # Total GED = 3

    graph_json_2 = {
        "nodes": [
            {"id": "StartEvent_1", "type": "MODIFIED_startEvent"},
            {"id": "Activity_14k7ctp", "type": "task", "name": "Write draft"},
            {"id": "Gateway_1p0lqz7", "type": "parallelGateway"},
            {"id": "Activity_10dlls5", "type": "task", "name": "Contact publisher"},
            {"id": "Activity_08pijh0", "type": "task", "name": "Process payment"},
            {"id": "Gateway_0hkn0t9", "type": "parallelGateway"},
            # {"id": "Event_05ig0cp", "type": "endEvent"},
        ],
        "edges": [
            {"source": "StartEvent_1", "target": "Activity_14k7ctp"},
            {"source": "Activity_14k7ctp", "target": "Gateway_1p0lqz7"},
            {"source": "Gateway_1p0lqz7", "target": "Activity_10dlls5"},
            {"source": "Gateway_1p0lqz7", "target": "Activity_08pijh0"},
            {"source": "Activity_08pijh0", "target": "Gateway_0hkn0t9"},
            {"source": "Activity_10dlls5", "target": "Gateway_0hkn0t9"},
            # {"source": "Gateway_0hkn0t9", "target": "Event_05ig0cp"},
        ],
    }

    ged_value = compute_ged(graph_json_1, graph_json_2)
    print("Graph Edit Distance:", ged_value)
