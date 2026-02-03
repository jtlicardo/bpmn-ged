import argparse
import csv
import hashlib
import json
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pm4py

@dataclass
class ConformanceResult:
    filename: str
    fitness_log: float
    avg_trace_fitness: float
    perc_fit_traces: float
    precision: float
    f1: float


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Semantic conformance evaluation using PM4Py (token-based replay)."
    )
    parser.add_argument("ground_truth_dir", type=str, help="Ground truth BPMN folder")
    parser.add_argument("generated_dir", type=str, help="Generated BPMN folder")
    parser.add_argument(
        "--traces", type=int, default=200, help="Number of traces to simulate per model"
    )
    parser.add_argument(
        "--max-trace-length",
        type=int,
        default=50,
        help="Maximum length of a simulated trace",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for log simulation"
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize labels using GPT mapping before conformance checking.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: 4, or 20 when --normalize is set)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path (requires --write-csv). Default: evaluation_results/conformance_results_TIMESTAMP.csv",
    )
    parser.add_argument(
        "--write-csv",
        action="store_true",
        help="Write per-file CSV metrics (default: off).",
    )
    parser.add_argument(
        "--summary-output",
        type=str,
        default=None,
        help="Output JSON file path (default: evaluation_results/conformance_summary_TIMESTAMP.json)",
    )
    return parser.parse_args()


def simulate_log(net, im, fm, traces: int, max_trace_length: int):
    parameters = {
        "noTraces": traces,
        "maxTraceLength": max_trace_length,
    }
    return pm4py.sim.play_out(net, im, fm, parameters=parameters)


def compute_conformance(log, net, im, fm) -> tuple[float, float, float, float, float]:
    fitness = pm4py.fitness_token_based_replay(log, net, im, fm)
    precision = pm4py.precision_token_based_replay(log, net, im, fm)

    fitness_log = float(fitness.get("log_fitness", 0.0))
    avg_trace_fitness = float(fitness.get("average_trace_fitness", 0.0))
    perc_fit_traces = float(
        fitness.get("perc_fit_traces", fitness.get("percentage_of_fitting_traces", 0.0))
    )

    f1 = (
        (2 * fitness_log * precision / (fitness_log + precision))
        if (fitness_log + precision)
        else 0.0
    )
    return fitness_log, avg_trace_fitness, perc_fit_traces, precision, f1


def derive_seed(base_seed: int, filename: str) -> int:
    digest = hashlib.md5(filename.encode("utf-8")).hexdigest()
    return base_seed + (int(digest, 16) % 1_000_000)


def build_label_mapping(ground_truth_path: Path, generated_path: Path) -> dict:
    from normalize_bpmn import normalize_graphs
    from parse_bpmn import parse_bpmn

    gt_graph = parse_bpmn(str(ground_truth_path))
    gen_graph = parse_bpmn(str(generated_path))

    if gt_graph is None or gen_graph is None:
        raise ValueError("Unable to parse BPMN for normalization.")

    normalized_gt, normalized_gen = normalize_graphs(
        gt_graph, gen_graph, str(ground_truth_path)
    )

    mapping: dict[str, str] = {}
    for node in list(normalized_gt.nodes) + list(normalized_gen.nodes):
        if node.original_name and node.normalized_name:
            mapping[node.original_name] = node.normalized_name
    return mapping


def apply_label_mapping(net, mapping: dict) -> None:
    for transition in net.transitions:
        if transition.label and transition.label in mapping:
            transition.label = mapping[transition.label]


def summarize_results(results: List[ConformanceResult]) -> dict:
    count = len(results)
    if count == 0:
        return {
            "file_count": 0,
            "average_fitness_log": 0.0,
            "average_avg_trace_fitness": 0.0,
            "average_perc_fit_traces": 0.0,
            "average_precision": 0.0,
            "average_f1": 0.0,
        }

    return {
        "file_count": count,
        "average_fitness_log": round(sum(r.fitness_log for r in results) / count, 5),
        "average_avg_trace_fitness": round(
            sum(r.avg_trace_fitness for r in results) / count, 5
        ),
        "average_perc_fit_traces": round(
            sum(r.perc_fit_traces for r in results) / count, 5
        ),
        "average_precision": round(sum(r.precision for r in results) / count, 5),
        "average_f1": round(sum(r.f1 for r in results) / count, 5),
    }


def write_csv(results: List[ConformanceResult], output_file: str) -> None:
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = [
            "filename",
            "fitness_log",
            "avg_trace_fitness",
            "perc_fit_traces",
            "precision",
            "f1",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "filename": result.filename,
                    "fitness_log": round(result.fitness_log, 5),
                    "avg_trace_fitness": round(result.avg_trace_fitness, 5),
                    "perc_fit_traces": round(result.perc_fit_traces, 5),
                    "precision": round(result.precision, 5),
                    "f1": round(result.f1, 5),
                }
            )


def write_summary_json(
    summary: dict,
    output_file: str,
    ground_truth_dir: str,
    generated_dir: str,
    traces: int,
    max_trace_length: int,
    seed: int,
    normalized: bool,
) -> None:
    payload = {
        "ground_truth_dir": ground_truth_dir,
        "generated_dir": generated_dir,
        "traces": traces,
        "max_trace_length": max_trace_length,
        "seed": seed,
        "conformance_method": "token_based_replay",
        "normalized": normalized,
    }
    payload.update(summary)
    with open(output_file, "w") as f:
        json.dump(payload, f, indent=2)


def process_file_pair(args: dict) -> tuple[Optional[ConformanceResult], Optional[str]]:
    try:
        seed = args["seed"]
        random.seed(seed)
        try:  # optional numpy seeding
            import numpy as np

            np.random.seed(seed)
        except Exception:
            pass

        gt_path = Path(args["ground_truth_path"])
        gen_path = Path(args["generated_path"])

        gt_bpmn = pm4py.read_bpmn(str(gt_path))
        gt_net, gt_im, gt_fm = pm4py.convert_to_petri_net(gt_bpmn)

        gen_bpmn = pm4py.read_bpmn(str(gen_path))
        gen_net, gen_im, gen_fm = pm4py.convert_to_petri_net(gen_bpmn)

        if args["normalize"]:
            mapping = build_label_mapping(gt_path, gen_path)
            apply_label_mapping(gt_net, mapping)
            apply_label_mapping(gen_net, mapping)

        log = simulate_log(
            gt_net, gt_im, gt_fm, args["traces"], args["max_trace_length"]
        )

        fitness_log, avg_trace_fitness, perc_fit_traces, precision, f1 = (
            compute_conformance(log, gen_net, gen_im, gen_fm)
        )

        return (
            ConformanceResult(
                filename=args["filename"],
                fitness_log=fitness_log,
                avg_trace_fitness=avg_trace_fitness,
                perc_fit_traces=perc_fit_traces,
                precision=precision,
                f1=f1,
            ),
            None,
        )
    except Exception as exc:
        return None, str(exc)


def main() -> None:
    args = parse_arguments()
    ground_truth_dir = Path(args.ground_truth_dir)
    generated_dir = Path(args.generated_dir)

    if not ground_truth_dir.exists():
        raise SystemExit(f"Ground truth dir not found: {ground_truth_dir}")
    if not generated_dir.exists():
        raise SystemExit(f"Generated dir not found: {generated_dir}")

    results_dir = Path("evaluation_results")
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = (
        args.output
        or str(results_dir / f"conformance_results_{timestamp}.csv")
        if args.write_csv
        else None
    )
    summary_output = args.summary_output or str(
        results_dir / f"conformance_summary_{timestamp}.json"
    )

    ground_truth_files = {f.name: f for f in ground_truth_dir.glob("*.bpmn")}
    results: List[ConformanceResult] = []
    skipped: List[str] = []

    process_args: List[dict] = []
    for filename, gt_path in sorted(ground_truth_files.items()):
        gen_path = generated_dir / filename
        if not gen_path.exists():
            print(
                f"Warning: No matching file found for {filename} in generated directory"
            )
            skipped.append(filename)
            continue
        process_args.append(
            {
                "filename": filename,
                "ground_truth_path": str(gt_path),
                "generated_path": str(gen_path),
                "traces": args.traces,
                "max_trace_length": args.max_trace_length,
                "normalize": args.normalize,
                "seed": derive_seed(args.seed, filename),
            }
        )

    total_files = len(process_args)
    completed = 0

    if total_files == 0:
        print("No matching BPMN files to evaluate.")
        return

    max_workers = args.workers if args.workers is not None else (20 if args.normalize else 4)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_file_pair, args_dict): args_dict["filename"]
            for args_dict in process_args
        }
        for future in as_completed(futures):
            filename = futures[future]
            completed += 1
            try:
                result, error = future.result()
                if result:
                    results.append(result)
                    print(
                        f"[{completed}/{total_files}] {filename} - "
                        f"Fitness: {result.fitness_log:.5f} Precision: {result.precision:.5f} F1: {result.f1:.5f}"
                    )
                else:
                    print(
                        f"[{completed}/{total_files}] Error processing {filename}: {error}"
                    )
                    skipped.append(filename)
            except Exception as exc:
                print(f"[{completed}/{total_files}] Error processing {filename}: {exc}")
                skipped.append(filename)

    if results:
        if args.write_csv and output_file:
            write_csv(results, output_file)
        summary = summarize_results(results)
        summary["skipped_files"] = len(skipped)
        write_summary_json(
            summary,
            summary_output,
            str(ground_truth_dir),
            str(generated_dir),
            args.traces,
            args.max_trace_length,
            args.seed,
            args.normalize,
        )
        print("\nEvaluation complete.")
        if args.write_csv and output_file:
            print(f"Metrics CSV: {output_file}")
        print(f"Summary JSON: {summary_output}")
    else:
        print("No results to write.")


if __name__ == "__main__":
    main()
