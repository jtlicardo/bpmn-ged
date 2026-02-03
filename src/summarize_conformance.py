import argparse
import json
from pathlib import Path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize conformance results into a single text file."
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="evaluation_results",
        help="Root evaluation_results folder",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="single.txt",
        help="Output text file path",
    )
    return parser.parse_args()


def detect_format(data: dict, filename: str) -> str:
    gen_dir = (data.get("generated_dir") or "").lower()
    if "generated_bpmn_xml" in gen_dir or "-xml" in filename:
        return "xml"
    if "generated_bpmn_json" in gen_dir or "-json" in filename:
        return "json"
    return "unknown"


def metric_line(label: str, metrics: dict | None) -> str:
    if not metrics:
        return f"{label} missing"
    return (
        f"{label} fitness={metrics['fitness']:.5f} "
        f"precision={metrics['precision']:.5f} "
        f"f1={metrics['f1']:.5f}"
    )


def main() -> None:
    args = parse_arguments()
    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        raise SystemExit(f"Results dir not found: {results_dir}")

    data_by_model: dict[str, dict[str, dict[bool, dict]]] = {}

    for model_dir in sorted(p for p in results_dir.iterdir() if p.is_dir()):
        model = model_dir.name
        for json_file in sorted(model_dir.glob("*.json")):
            with open(json_file, "r") as f:
                data = json.load(f)
            if "average_fitness_log" not in data:
                continue

            normalized = bool(data.get("normalized", False))
            fmt = detect_format(data, json_file.name)
            metrics = {
                "fitness": float(data.get("average_fitness_log", 0.0)),
                "precision": float(data.get("average_precision", 0.0)),
                "f1": float(data.get("average_f1", 0.0)),
            }

            data_by_model.setdefault(model, {}).setdefault(fmt, {})[normalized] = metrics

    lines: list[str] = []
    aggregate: dict[str, dict[bool, list[dict]]] = {}
    for model in sorted(data_by_model.keys()):
        lines.append(f"model: {model}")
        for fmt in sorted(data_by_model[model].keys()):
            raw_metrics = data_by_model[model][fmt].get(False)
            norm_metrics = data_by_model[model][fmt].get(True)

            lines.append(metric_line(f"{fmt} raw", raw_metrics))
            lines.append(metric_line(f"{fmt} norm", norm_metrics))

            if raw_metrics:
                aggregate.setdefault(fmt, {}).setdefault(False, []).append(raw_metrics)
            if norm_metrics:
                aggregate.setdefault(fmt, {}).setdefault(True, []).append(norm_metrics)
        lines.append("")

    def average_metrics(items: list[dict]) -> dict:
        if not items:
            return {"fitness": 0.0, "precision": 0.0, "f1": 0.0}
        count = len(items)
        return {
            "fitness": sum(i["fitness"] for i in items) / count,
            "precision": sum(i["precision"] for i in items) / count,
            "f1": sum(i["f1"] for i in items) / count,
        }

    if aggregate:
        lines.append("averages:")
        for fmt in sorted(aggregate.keys()):
            raw_avg = average_metrics(aggregate[fmt].get(False, []))
            norm_avg = average_metrics(aggregate[fmt].get(True, []))
            lines.append(
                f"{fmt} raw avg fitness={raw_avg['fitness']:.5f} "
                f"precision={raw_avg['precision']:.5f} "
                f"f1={raw_avg['f1']:.5f}"
            )
            lines.append(
                f"{fmt} norm avg fitness={norm_avg['fitness']:.5f} "
                f"precision={norm_avg['precision']:.5f} "
                f"f1={norm_avg['f1']:.5f}"
            )
        lines.append("")

    output_path = Path(args.output)
    output_path.write_text("\n".join(lines).rstrip() + "\n")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
