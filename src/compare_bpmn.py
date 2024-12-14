import argparse

from ged import compute_ged
from parse_bpmn import parse_bpmn


def parse_arguments():
    parser = argparse.ArgumentParser(description="Compare two BPMN files")
    parser.add_argument("file1", type=str, help="Path to the first BPMN file")
    parser.add_argument("file2", type=str, help="Path to the second BPMN file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    nodes1, edges1 = parse_bpmn(args.file1)
    nodes2, edges2 = parse_bpmn(args.file2)

    json_graph_1 = {"nodes": nodes1, "edges": edges1}
    json_graph_2 = {"nodes": nodes2, "edges": edges2}

    