import os
import csv
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Any
from parse_bpmn import parse_bpmn
from normalize_bpmn import normalize_graphs
from ged import compute_ged, compute_rged
import argparse
from datetime import datetime

@dataclass
class ComparisonResult:
    filename: str
    ged: float
    rged: float
    similarity: float

def parse_arguments():
    parser = argparse.ArgumentParser(description="Compare BPMN files from two directories")
    parser.add_argument("ground_truth_dir", type=str, help="Path to the ground truth BPMN files directory")
    parser.add_argument("comparison_dir", type=str, help="Path to the comparison BPMN files directory")
    parser.add_argument(
        "--output", 
        type=str,
        default=None,
        help="Output CSV file path (default: evaluation_results_TIMESTAMP.csv)"
    )
    return parser.parse_args()

def process_file_pair(args: Dict[str, Any]) -> ComparisonResult | None:
    try:
        # Parse both BPMN files
        graph_1 = parse_bpmn(str(args['ground_truth_path']))
        graph_2 = parse_bpmn(str(args['comparison_path']))
        
        # Normalize and compare
        normalized_graph_1, normalized_graph_2 = normalize_graphs(
            graph_1, 
            graph_2, 
            str(args['ground_truth_path'])
        )
        
        ged = compute_ged(normalized_graph_1, normalized_graph_2)
        rged = compute_rged(normalized_graph_1, normalized_graph_2)
        similarity = 1 - rged
        
        return ComparisonResult(
            filename=args['filename'],
            ged=ged,
            rged=round(rged, 5),
            similarity=round(similarity, 5)
        )
        
    except Exception as e:
        print(f"Error processing {args['filename']}: {str(e)}")
        return None

def evaluate_bpmn_directories(ground_truth_dir: str, comparison_dir: str, output_file: str | None = None):
    results_dir = "evaluation_results"
    os.makedirs(results_dir, exist_ok=True)

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(results_dir, f"evaluation_results_{timestamp}.csv")

    ground_truth_files = {f.name: f for f in Path(ground_truth_dir).glob("*.bpmn")}
    
    # Prepare arguments for parallel processing
    process_args = []
    for filename, ground_truth_path in ground_truth_files.items():
        comparison_path = Path(comparison_dir) / filename
        
        if not comparison_path.exists():
            print(f"Warning: No matching file found for {filename} in comparison directory")
            continue
            
        process_args.append({
            'filename': filename,
            'ground_truth_path': ground_truth_path,
            'comparison_path': comparison_path,
        })

    results = []
    total_files = len(process_args)
    completed = 0

    # Use ProcessPoolExecutor for parallel processing
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_file_pair, args): args['filename'] 
                  for args in process_args}
        
        for future in as_completed(futures):
            filename = futures[future]
            completed += 1
            
            try:
                result = future.result()
                if result:
                    results.append(result)
                    print(f"[{completed}/{total_files}] Processed {filename} - "
                          f"Similarity: {result.similarity}")
            except Exception as e:
                print(f"[{completed}/{total_files}] Error processing {filename}: {str(e)}")

    # Write results to CSV
    if results:
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['filename', 'ged', 'rged', 'similarity']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerows([vars(result)])
    
    print(f"\nEvaluation complete. Results saved to: {output_file}")

if __name__ == "__main__":
    args = parse_arguments()
    evaluate_bpmn_directories(
        args.ground_truth_dir,
        args.comparison_dir,
        args.output
    )
