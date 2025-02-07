# BPMN Graph Edit Distance

This utility compares two BPMN diagrams using Graph Edit Distance (GED) and Relative Graph Edit Distance (RGED).

## Requirements

- Python 3.12 or higher
- uv package manager

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

## Implementation Details

The GED and RGED calculations are implemented in the `ged.py` file.

- `compute_ged`: Computes the Graph Edit Distance (GED) between two graphs.
- `compute_rged`: Computes the Relative Graph Edit Distance (RGED) between two graphs.

The RGED is calculated as:

$$
\text{Relative GED} = \frac{\text{GED}(G1, G2)}{\text{GED}(G1, \text{Empty}) + \text{GED}(G2, \text{Empty})}
$$

The similarity score is calculated as:

$$
\text{Similarity} = 1 - \text{RGED}
$$
