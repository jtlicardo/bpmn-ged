import os
import csv
from pathlib import Path
from parse_bpmn import parse_bpmn
from normalize_bpmn import normalize_graphs
from ged import compute_ged, compute_rged
import argparse
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description="Compare BPMN files from two directories")
    parser.add_argument("ground_truth_dir", type=str, help="Path to the ground truth BPMN files directory")
    parser.add_argument("comparison_dir", type=str, help="Path to the comparison BPMN files directory")
    parser.add_argument(
        "--model", 
        type=str, 
        choices=["gpt-4o-mini", "o3-mini"],
        default="gpt-4o-mini",
        help="Choose the OpenAI model to use for normalization"
    )
    parser.add_argument(
        "--output", 
        type=str,
        default=None,
        help="Output CSV file path (default: evaluation_results_TIMESTAMP.csv)"
    )
    return parser.parse_args()

def evaluate_bpmn_directories(ground_truth_dir: str, comparison_dir: str, model: str, output_file: str | None = None):
    results_dir = "evaluation_results"
    os.makedirs(results_dir, exist_ok=True)

    # Generate default output filename if none provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(results_dir, f"evaluation_results_{timestamp}.csv")

    # Get list of BPMN files from ground truth directory
    ground_truth_files = {f.name: f for f in Path(ground_truth_dir).glob("*.bpmn")}
    
    results = []
    
    # Compare each file
    for filename, ground_truth_path in ground_truth_files.items():
        comparison_path = Path(comparison_dir) / filename
        
        if not comparison_path.exists():
            print(f"Warning: No matching file found for {filename} in comparison directory")
            continue
            
        try:
            # Parse both BPMN files
            graph_1 = parse_bpmn(str(ground_truth_path))
            graph_2 = parse_bpmn(str(comparison_path))
            
            # Normalize and compare
            normalized_graph_1, normalized_graph_2 = normalize_graphs(
                graph_1, 
                graph_2, 
                str(ground_truth_path),
                model=model
            )
            
            ged = compute_ged(normalized_graph_1, normalized_graph_2)
            rged = compute_rged(normalized_graph_1, normalized_graph_2)
            similarity = 1 - rged
            
            results.append({
                'filename': filename,
                'ged': ged,
                'rged': round(rged, 5),
                'similarity': round(similarity, 5)
            })
            
            print(f"Processed {filename} - Similarity: {round(similarity, 5)}")
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue
    
    # Write results to CSV
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['filename', 'ged', 'rged', 'similarity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nEvaluation complete. Results saved to: {output_file}")

if __name__ == "__main__":
    args = parse_arguments()
    evaluate_bpmn_directories(
        args.ground_truth_dir,
        args.comparison_dir,
        args.model,
        args.output
    )