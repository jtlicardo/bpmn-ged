import json
import xml.etree.ElementTree as ET
from typing import Optional
import argparse

from schemas import BPMNGraph


def parse_bpmn(file_path: str) -> Optional[BPMNGraph]:
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
            edge = {
                "source": element.attrib["sourceRef"],
                "target": element.attrib["targetRef"],
            }
            if "name" in element.attrib:
                edge["name"] = element.attrib["name"]
            graph_data["edges"].append(edge)
        else:
            node = {"id": element.attrib["id"], "type": tag}
            if "name" in element.attrib:
                node["name"] = element.attrib["name"]
            graph_data["nodes"].append(node)

    return BPMNGraph(**graph_data)


def display_graph_info(graph_data: BPMNGraph) -> None:
    print("Nodes:")
    for node in graph_data.nodes:
        name_str = f" ({node.name})" if node.name else ""
        print(f"  {node.id} - {node.type}{name_str}")

    print("\nEdges:")
    for edge in graph_data.edges:
        name_str = f" [{edge.name}]" if edge.name else ""
        print(f"  {edge.source} -> {edge.target}{name_str}")


def save_graph_to_json(graph_data: BPMNGraph, output_path: str) -> None:
    try:
        with open(output_path, "w") as f:
            json.dump(graph_data.model_dump(), f, indent=2)
    except IOError as e:
        print(f"Error saving file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse BPMN file to graph structure')
    parser.add_argument('input_file', help='Path to input BPMN file')
    args = parser.parse_args()

    output_json = "graph_data.json"
    graph_data = parse_bpmn(args.input_file)

    if graph_data:
        display_graph_info(graph_data)
        save_graph_to_json(graph_data, output_json)
        print(f"\nGraph data saved to {output_json}")
