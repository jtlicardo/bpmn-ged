# BPMN Graph Edit Distance

This utility compares two BPMN diagrams using Graph Edit Distance (GED) and Relative Graph Edit Distance (RGED).

## Requirements

- Python 3.12 or higher
- The following Python packages:
  - networkx
  - numpy
  - scipy

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/jtlicardo/bpmn-ged
    cd bpmn-ged
    ```

2. Install `uv` package manager:
    ```sh
    pip install uv
    ```

## Usage

To compare two BPMN files, run the following command:

```sh
uv run src/compare_bpmn.py <path-to-first-bpmn-file> <path-to-second-bpmn-file>
```

For example:

```sh
uv run src/compare_bpmn.py models/first.bpmn models/second.bpmn
```

Example output

```sh
Graph Edit Distance (GED): 3.0
Relative Graph Edit Distance (RGED): 0.60000
Graph Similarity: 0.40000
```