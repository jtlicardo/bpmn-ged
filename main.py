import xml.etree.ElementTree as ET


def parse_bpmn(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define the namespaces used in the XML
    namespaces = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}

    process = root.find("bpmn:process", namespaces)
    if process is None:
        print("No process found in the BPMN file.")
        return

    elements = {}
    sequence_flows = []

    for element in process:
        tag = element.tag.split("}")[-1]  # Remove namespace
        if tag == "sequenceFlow":
            sequence_flows.append(
                {
                    "id": element.attrib["id"],
                    "source": element.attrib["sourceRef"],
                    "target": element.attrib["targetRef"],
                }
            )
        else:
            elements[element.attrib["id"]] = {
                "type": tag,
                "name": element.attrib.get("name", ""),
            }

    return elements, sequence_flows


def display_graph_info(elements, sequence_flows):
    print("Elements:")
    for element_id, info in elements.items():
        print(f"  {element_id}: {info}")

    print("\nSequence Flows:")
    for flow in sequence_flows:
        print(f"  {flow['id']}: {flow['source']} -> {flow['target']}")


file_path = "models/first.bpmn"

elements, sequence_flows = parse_bpmn(file_path)
if elements and sequence_flows:
    display_graph_info(elements, sequence_flows)
