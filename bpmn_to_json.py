import xml.etree.ElementTree as ET
import json


def parse_bpmn(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define the namespaces used in the XML
    namespaces = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}

    process = root.find("bpmn:process", namespaces)
    if process is None:
        print("No process found in the BPMN file.")
        return

    nodes = []
    edges = []

    for element in process:
        tag = element.tag.split("}")[-1]  # Remove namespace
        if tag == "sequenceFlow":
            edges.append(
                {
                    "source": element.attrib["sourceRef"],
                    "target": element.attrib["targetRef"],
                }
            )
        else:
            node = {"id": element.attrib["id"], "type": tag}
            if "name" in element.attrib:
                node["name"] = element.attrib["name"]
            nodes.append(node)

    return nodes, edges


def display_graph_info(nodes, edges):
    print("Nodes:")
    for node in nodes:
        print(f"  {node}")

    print("\nEdges:")
    for edge in edges:
        print(f"  {edge['source']} -> {edge['target']}")


def save_graph_to_json(nodes, edges, output_path):
    graph_data = {"nodes": nodes, "edges": edges}

    with open(output_path, "w") as f:
        json.dump(graph_data, f, indent=2)


file_path = "models/first.bpmn"
output_json = "graph_data.json"

nodes, edges = parse_bpmn(file_path)
if nodes and edges:
    display_graph_info(nodes, edges)
    save_graph_to_json(nodes, edges, output_json)
    print(f"\nGraph data saved to {output_json}")
