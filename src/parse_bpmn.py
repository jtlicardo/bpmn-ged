import json
import xml.etree.ElementTree as ET
from typing import Optional


def parse_bpmn(file_path: str) -> Optional[dict]:
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define the namespaces used in the XML
    namespaces = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}

    process = root.find("bpmn:process", namespaces)
    if process is None:
        print("No process found in the BPMN file.")
        return None

    graph_data = {"nodes": [], "edges": []}

    for element in process:
        tag = element.tag.split("}")[-1]  # Remove namespace
        if tag == "sequenceFlow":
            graph_data["edges"].append(
                {
                    "source": element.attrib["sourceRef"],
                    "target": element.attrib["targetRef"],
                }
            )
        else:
            node = {"id": element.attrib["id"], "type": tag}
            if "name" in element.attrib:
                node["name"] = element.attrib["name"]
            graph_data["nodes"].append(node)

    return graph_data


def display_graph_info(graph_data: dict) -> None:
    print("Nodes:")
    for node in graph_data["nodes"]:
        print(f"  {node}")

    print("\nEdges:")
    for edge in graph_data["edges"]:
        print(f"  {edge['source']} -> {edge['target']}")


def save_graph_to_json(graph_data: dict, output_path: str) -> None:
    with open(output_path, "w") as f:
        json.dump(graph_data, f, indent=2)


if __name__ == "__main__":
    file_path = "models/first.bpmn"
    output_json = "graph_data.json"

    graph_data = parse_bpmn(file_path)

    if graph_data:
        display_graph_info(graph_data)
        save_graph_to_json(graph_data, output_json)
        print(f"\nGraph data saved to {output_json}")
