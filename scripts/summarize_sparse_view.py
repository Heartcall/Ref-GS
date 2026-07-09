import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.make_sparse_view_dataset import DEFAULT_OUTPUT_ROOT as DEFAULT_SPARSE_DATA_ROOT


FIELDNAMES = [
    "dataset",
    "scene",
    "strategy",
    "views",
    "seed",
    "iteration",
    "train_views",
    "test_views",
    "psnr",
    "ssim",
    "lpips",
    "baseline_psnr",
    "baseline_ssim",
    "baseline_lpips",
    "delta_psnr",
    "delta_ssim",
    "delta_lpips",
    "checkpoint_exists",
    "render_exists",
    "metrics_exists",
    "status",
    "failure_reason",
    "notes",
]

ERROR_MARKERS = (
    "CUDA out of memory",
    "RuntimeError:",
    "Traceback",
    "KeyboardInterrupt",
    "No space left on device",
    "FileNotFoundError:",
    "ValueError:",
    "ImportError:",
)


def _to_float(value):
    if value in (None, "", "NA"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _metric_delta(value, baseline):
    if value is None or baseline is None:
        return None
    return value - baseline


def _load_results(path: Path) -> Tuple[Optional[dict], str]:
    if not path.exists():
        return None, "missing_metrics"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"bad_metrics_json: {exc}"
    aggregate = data.get("aggregate", data)
    return aggregate, "ok"


def _read_failure_reason(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"could not read log: {exc}"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for marker in ERROR_MARKERS:
        for line in reversed(lines):
            if marker in line:
                return line[-500:]
    return ""


def _log_failure_reason(log_root: Optional[Path], dataset: str, strategy: str, views: int, seed: int, scene: str) -> str:
    if log_root is None:
        return ""
    log_dir = log_root / dataset / strategy / f"views_{views}" / f"seed_{seed}" / scene
    for action in ("train", "render", "eval"):
        reason = _read_failure_reason(log_dir / action)
        if reason:
            return f"{action}: {reason}"
    return ""


def _has_any_action_log(log_root: Optional[Path], dataset: str, strategy: str, views: int, seed: int, scene: str) -> bool:
    if log_root is None:
        return False
    log_dir = log_root / dataset / strategy / f"views_{views}" / f"seed_{seed}" / scene
    return any((log_dir / action).exists() for action in ("train", "render", "eval"))


def _parse_sparse_model_dir(path: Path, sparse_output_root: Path) -> Optional[dict]:
    try:
        rel = path.relative_to(sparse_output_root)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) != 5:
        return None
    dataset, strategy, views_part, seed_part, scene = parts
    if not views_part.startswith("views_") or not seed_part.startswith("seed_"):
        return None
    try:
        views = int(views_part.split("_", 1)[1])
        seed = int(seed_part.split("_", 1)[1])
    except ValueError:
        return None
    return {"dataset": dataset, "strategy": strategy, "views": views, "seed": seed, "scene": scene}


def _candidate_model_dirs(sparse_output_root: Path) -> Iterable[Path]:
    if not sparse_output_root.exists():
        return []
    return sorted(path for path in sparse_output_root.glob("*/*/views_*/seed_*/*") if path.is_dir())


def _candidate_manifest_model_dirs(sparse_output_root: Path, sparse_data_root: Path) -> Iterable[Path]:
    if not sparse_data_root.exists():
        return []
    model_dirs = []
    for manifest_path in sorted(sparse_data_root.glob("*/*/views_*/seed_*/*/sparse_view_manifest.json")):
        parsed = _parse_sparse_model_dir(manifest_path.parent, sparse_data_root)
        if parsed is None:
            continue
        model_dirs.append(
            sparse_output_root
            / parsed["dataset"]
            / parsed["strategy"]
            / f"views_{parsed['views']}"
            / f"seed_{parsed['seed']}"
            / parsed["scene"]
        )
    return model_dirs


def _read_baseline_csv(path: Path) -> Dict[Tuple[str, str], dict]:
    baselines = {}
    if not path.exists():
        return baselines
    with path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row.get("dataset", ""), row.get("scene", ""))
            baselines[key] = {
                "psnr": _to_float(row.get("psnr")),
                "ssim": _to_float(row.get("ssim")),
                "lpips": _to_float(row.get("lpips")),
            }
    return baselines


def _read_baseline_outputs(root: Path) -> Dict[Tuple[str, str], dict]:
    baselines = {}
    if not root.exists():
        return baselines
    for result_path in sorted(root.glob("*/*/results.json")):
        dataset = result_path.parent.parent.name
        scene = result_path.parent.name
        aggregate, status = _load_results(result_path)
        if status == "ok" and aggregate:
            baselines[(dataset, scene)] = {
                "psnr": _to_float(aggregate.get("psnr")),
                "ssim": _to_float(aggregate.get("ssim")),
                "lpips": _to_float(aggregate.get("lpips")),
            }
    return baselines


def load_baselines(baseline_output_root: Path, baseline_metrics_csv: Path) -> Dict[Tuple[str, str], dict]:
    baselines = _read_baseline_outputs(baseline_output_root)
    baselines.update(_read_baseline_csv(baseline_metrics_csv))
    return baselines


def _manifest_counts(
    sparse_data_root: Path, dataset: str, strategy: str, views: int, seed: int, scene: str
) -> Tuple[Optional[int], Optional[int], str, str]:
    manifest_path = sparse_data_root / dataset / strategy / f"views_{views}" / f"seed_{seed}" / scene / "sparse_view_manifest.json"
    if not manifest_path.exists():
        return None, None, "missing", "missing sparse manifest"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, None, "failed", f"bad sparse manifest: {exc}"
    return (
        manifest.get("train_frames_selected"),
        manifest.get("test_frames"),
        manifest.get("status", "ok"),
        manifest.get("notes", ""),
    )


def _row_for_model(
    model_dir: Path,
    sparse_output_root: Path,
    baselines: Dict[Tuple[str, str], dict],
    sparse_data_root: Path,
    iteration: int,
    log_root: Optional[Path] = None,
) -> Optional[dict]:
    parsed = _parse_sparse_model_dir(model_dir, sparse_output_root)
    if parsed is None:
        return None
    dataset = parsed["dataset"]
    scene = parsed["scene"]
    strategy = parsed["strategy"]
    views = parsed["views"]
    seed = parsed["seed"]
    split_dir = model_dir / "test" / f"ours_{iteration}"
    result_path = model_dir / "results.json"
    if not result_path.exists():
        result_path = split_dir / "results.json"
    aggregate, status = _load_results(result_path)
    metrics_exists = status == "ok"
    psnr = _to_float(aggregate.get("psnr")) if aggregate else None
    ssim = _to_float(aggregate.get("ssim")) if aggregate else None
    lpips = _to_float(aggregate.get("lpips")) if aggregate else None
    baseline = baselines.get((dataset, scene), {})
    train_views, test_views, manifest_status, manifest_notes = _manifest_counts(sparse_data_root, dataset, strategy, views, seed, scene)
    checkpoint_exists = (model_dir / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply").exists()
    render_dir = split_dir / "renders"
    render_exists = render_dir.exists() and any(render_dir.iterdir())
    failure_reason = _log_failure_reason(log_root, dataset, strategy, views, seed, scene)
    has_action_log = _has_any_action_log(log_root, dataset, strategy, views, seed, scene)
    notes = manifest_notes or ""
    if manifest_status == "failed":
        row_status = "failed"
        failure_reason = failure_reason or notes
    elif failure_reason:
        row_status = "failed"
    elif metrics_exists:
        row_status = "completed"
    elif has_action_log:
        row_status = "running"
    elif not metrics_exists:
        row_status = "missing"
    if not metrics_exists:
        notes = "; ".join(part for part in [notes, status] if part)
    if failure_reason and failure_reason not in notes:
        notes = "; ".join(part for part in [notes, failure_reason] if part)
    return {
        "dataset": dataset,
        "scene": scene,
        "strategy": strategy,
        "views": views,
        "seed": seed,
        "iteration": aggregate.get("iteration", iteration) if aggregate else iteration,
        "train_views": train_views,
        "test_views": test_views,
        "psnr": psnr,
        "ssim": ssim,
        "lpips": lpips,
        "baseline_psnr": baseline.get("psnr"),
        "baseline_ssim": baseline.get("ssim"),
        "baseline_lpips": baseline.get("lpips"),
        "delta_psnr": _metric_delta(psnr, baseline.get("psnr")),
        "delta_ssim": _metric_delta(ssim, baseline.get("ssim")),
        "delta_lpips": _metric_delta(lpips, baseline.get("lpips")),
        "checkpoint_exists": checkpoint_exists,
        "render_exists": render_exists,
        "metrics_exists": metrics_exists,
        "status": row_status,
        "failure_reason": failure_reason,
        "notes": notes,
    }


def collect_sparse_rows(
    sparse_output_root: Path,
    baseline_output_root: Path,
    baseline_metrics_csv: Path,
    sparse_data_root: Path,
    iteration: int,
    log_root: Optional[Path] = None,
) -> List[dict]:
    baselines = load_baselines(baseline_output_root, baseline_metrics_csv)
    rows = []
    model_dirs = list(_candidate_model_dirs(sparse_output_root))
    known = {str(path) for path in model_dirs}
    for model_dir in _candidate_manifest_model_dirs(sparse_output_root, sparse_data_root):
        if str(model_dir) not in known:
            model_dirs.append(model_dir)
            known.add(str(model_dir))
    for model_dir in model_dirs:
        row = _row_for_model(model_dir, sparse_output_root, baselines, sparse_data_root, iteration, log_root=log_root)
        if row is not None:
            rows.append(row)
    return sorted(rows, key=lambda row: (row["dataset"], row["strategy"], row["views"], row["seed"], row["scene"]))


def _mean(values: Iterable[Optional[float]]) -> Optional[float]:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return statistics.mean(present)


def _stdev(values: Iterable[Optional[float]]) -> Optional[float]:
    present = [value for value in values if value is not None]
    if len(present) < 2:
        return None
    return statistics.stdev(present)


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        if math.isnan(value):
            return "NA"
        return f"{value:.6f}"
    return str(value)


def _group_rows(rows: List[dict], keys: Tuple[str, ...]) -> Dict[Tuple, List[dict]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return dict(grouped)


def _dataset_averages(rows: List[dict]) -> List[dict]:
    averages = []
    for key, group in sorted(_group_rows(rows, ("dataset", "strategy", "views", "seed")).items()):
        dataset, strategy, views, seed = key
        averages.append(
            {
                "dataset": dataset,
                "strategy": strategy,
                "views": views,
                "seed": seed,
                "scenes": len(group),
                "completed_scenes": sum(1 for row in group if row["status"] == "completed"),
                "psnr": _mean(row["psnr"] for row in group),
                "ssim": _mean(row["ssim"] for row in group),
                "lpips": _mean(row["lpips"] for row in group),
                "delta_psnr": _mean(row["delta_psnr"] for row in group),
                "delta_ssim": _mean(row["delta_ssim"] for row in group),
                "delta_lpips": _mean(row["delta_lpips"] for row in group),
            }
        )
    return averages


def _progress_counts(rows: List[dict]) -> dict:
    counts = {"completed": 0, "running": 0, "missing": 0, "failed": 0}
    for row in rows:
        status = row["status"]
        if status in counts:
            counts[status] += 1
        else:
            counts["missing"] += 1
    return counts


def _progress_by_dataset_views(rows: List[dict]) -> List[dict]:
    progress = []
    for key, group in sorted(_group_rows(rows, ("dataset", "strategy", "views", "seed")).items()):
        dataset, strategy, views, seed = key
        counts = _progress_counts(group)
        total = len(group)
        progress.append(
            {
                "dataset": dataset,
                "strategy": strategy,
                "views": views,
                "seed": seed,
                "total": total,
                **counts,
                "completion_rate": counts["completed"] / total if total else 0.0,
            }
        )
    return progress


def _cross_seed_averages(rows: List[dict]) -> List[dict]:
    averages = []
    for key, group in sorted(_group_rows(rows, ("dataset", "strategy", "views")).items()):
        dataset, strategy, views = key
        averages.append(
            {
                "dataset": dataset,
                "strategy": strategy,
                "views": views,
                "seeds": len(set(row["seed"] for row in group)),
                "psnr_mean": _mean(row["psnr"] for row in group),
                "psnr_std": _stdev(row["psnr"] for row in group),
                "ssim_mean": _mean(row["ssim"] for row in group),
                "ssim_std": _stdev(row["ssim"] for row in group),
                "lpips_mean": _mean(row["lpips"] for row in group),
                "lpips_std": _stdev(row["lpips"] for row in group),
                "delta_psnr_mean": _mean(row["delta_psnr"] for row in group),
                "delta_ssim_mean": _mean(row["delta_ssim"] for row in group),
                "delta_lpips_mean": _mean(row["delta_lpips"] for row in group),
            }
        )
    return averages


def _markdown_table(headers: List[str], rows: List[dict]) -> List[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_fmt(row.get(header)) for header in headers) + " |")
    return lines


def _write_markdown(path: Path, rows: List[dict], dataset_avg: List[dict], cross_seed_avg: List[dict], progress_counts: dict, progress_by_dataset_views: List[dict]) -> None:
    failures = [row for row in rows if row["status"] in ("failed", "missing", "running")]
    lines = [
        "# Sparse-View Evaluation Summary",
        "",
        "## Coverage",
        "",
        f"- Sparse rows discovered: {len(rows)}",
        f"- Rows with metrics: {sum(1 for row in rows if row['metrics_exists'])}",
        f"- Rows missing metrics: {sum(1 for row in rows if not row['metrics_exists'])}",
        f"- Rows with checkpoints: {sum(1 for row in rows if row['checkpoint_exists'])}",
        f"- Rows with rendered test images: {sum(1 for row in rows if row['render_exists'])}",
        f"- Completed: {progress_counts['completed']}",
        f"- Running: {progress_counts['running']}",
        f"- Missing: {progress_counts['missing']}",
        f"- Failed: {progress_counts['failed']}",
        "",
        "## Completion By Dataset/View",
        "",
    ]
    lines.extend(
        _markdown_table(
            ["dataset", "strategy", "views", "seed", "total", "completed", "running", "missing", "failed", "completion_rate"],
            progress_by_dataset_views,
        )
    )
    lines.extend(
        [
        "",
        "## Dataset Averages",
        "",
        ]
    )
    lines.extend(
        _markdown_table(
            ["dataset", "strategy", "views", "seed", "scenes", "completed_scenes", "psnr", "ssim", "lpips", "delta_psnr", "delta_ssim", "delta_lpips"],
            dataset_avg,
        )
    )
    lines.extend(["", "## Cross-Seed Averages", ""])
    lines.extend(
        _markdown_table(
            [
                "dataset",
                "strategy",
                "views",
                "seeds",
                "psnr_mean",
                "psnr_std",
                "ssim_mean",
                "ssim_std",
                "lpips_mean",
                "lpips_std",
                "delta_psnr_mean",
                "delta_ssim_mean",
                "delta_lpips_mean",
            ],
            cross_seed_avg,
        )
    )
    lines.extend(["", "## Per-Scene Table", ""])
    lines.extend(
        _markdown_table(
            [
                "dataset",
                "scene",
                "strategy",
                "views",
                "seed",
                "train_views",
                "test_views",
                "psnr",
                "ssim",
                "lpips",
                "baseline_psnr",
                "baseline_ssim",
                "baseline_lpips",
                "delta_psnr",
                "delta_ssim",
                "delta_lpips",
                "status",
                "failure_reason",
                "notes",
            ],
            rows,
        )
    )
    lines.extend(["", "## Failure Summary", ""])
    if failures:
        lines.extend(_markdown_table(["dataset", "scene", "strategy", "views", "seed", "status", "failure_reason", "notes"], failures))
    else:
        lines.append("No sparse rows with failed or missing metrics were found.")
    lines.extend(
        [
            "",
            "## Paper/Full-View Alignment Caveats",
            "",
            "- Sparse-view rows reduce only `transforms_train.json`; `transforms_test.json` remains the full test split.",
            "- Full-view baselines are read from `output/repro_paper` and/or `logs/repro/metrics_summary.csv`; they are not overwritten by this summary.",
            "- Sparse-view RGB metrics are protocol-specific and should not be mixed into the paper full-view table unless the paper uses the same sparse protocol.",
            "- Random sparse-view rows should be interpreted across seeds because individual camera subsets can have high variance.",
            "- Geometry/proxy metrics are intentionally excluded from the main sparse-view RGB summary.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(rows: List[dict], log_root: Path) -> None:
    log_root.mkdir(parents=True, exist_ok=True)
    csv_path = log_root / "sparse_view_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in FIELDNAMES})

    dataset_avg = _dataset_averages(rows)
    cross_seed_avg = _cross_seed_averages(rows)
    progress_counts = _progress_counts(rows)
    progress_by_dataset_views = _progress_by_dataset_views(rows)
    with (log_root / "sparse_view_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "rows": rows,
                "dataset_averages": dataset_avg,
                "cross_seed_averages": cross_seed_avg,
                "progress_counts": progress_counts,
                "progress_by_dataset_views": progress_by_dataset_views,
            },
            handle,
            indent=2,
        )
        handle.write("\n")
    _write_markdown(log_root / "sparse_view_summary.md", rows, dataset_avg, cross_seed_avg, progress_counts, progress_by_dataset_views)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize sparse-view Ref-GS RGB metrics against full-view baselines.")
    parser.add_argument("--sparse-output-root", type=Path, default=Path("output/sparse_view"))
    parser.add_argument("--baseline-output-root", type=Path, default=Path("output/repro_paper"))
    parser.add_argument("--baseline-metrics-csv", type=Path, default=Path("logs/repro/metrics_summary.csv"))
    parser.add_argument("--sparse-data-root", type=Path, default=DEFAULT_SPARSE_DATA_ROOT)
    parser.add_argument("--log-root", type=Path, default=Path("logs/sparse_view"))
    parser.add_argument("--iteration", type=int, default=31000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = collect_sparse_rows(
        sparse_output_root=args.sparse_output_root,
        baseline_output_root=args.baseline_output_root,
        baseline_metrics_csv=args.baseline_metrics_csv,
        sparse_data_root=args.sparse_data_root,
        iteration=args.iteration,
        log_root=args.log_root,
    )
    write_summary(rows, args.log_root)
    print(f"Wrote {len(rows)} sparse rows to {args.log_root / 'sparse_view_summary.csv'}")


if __name__ == "__main__":
    main()
