import argparse

from ged import compute_ged, compute_rged
from parse_bpmn import parse_bpmn


def parse_arguments():
    parser = argparse.ArgumentParser(description="Compare two BPMN files")
    parser.add_argument("file1", type=str, help="Path to the first BPMN file")
    parser.add_argument("file2", type=str, help="Path to the second BPMN file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    graph_1 = parse_bpmn(args.file1)
    graph_2 = parse_bpmn(args.file2)

    ged = compute_ged(graph_1, graph_2)
    rged = compute_rged(graph_1, graph_2)

    print(f"Graph Edit Distance (GED): {ged}")
    print(f"Relative Graph Edit Distance (RGED): {rged:.5f}")
    print(f"Graph Similarity: {1 - rged:.5f}")
