#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.refgs_llff_common import LLFF_SCENES, RESOLUTIONS, read_json, write_json


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_ROOT = REPO_ROOT / "logs" / "refgs_llff"
DEFAULT_FSGS_SUMMARY = Path("/home/liuly/Surface_Reconstruction/Sparse/FSGS/logs/llff_repro/llff_repro_summary.json")
FSGS_MEANS = {
    "1_8": {"psnr": 20.4619, "ssim": 0.699808, "lpips": 0.204037},
    "1_4": {"psnr": 19.7724, "ssim": 0.663966, "lpips": 0.269889},
}


def row_from_status(scene, resolution, status):
    metrics = status.get("metrics") if status.get("status") == "completed" else None
    metrics = metrics if isinstance(metrics, dict) else {}
    train_stage = status.get("stages", {}).get("train", {})
    return {
        "scene": scene, "resolution": resolution, "status": status.get("status", "missing"),
        "psnr": metrics.get("psnr"), "ssim": metrics.get("ssim"), "lpips": metrics.get("lpips"),
        "train_views": len(status.get("train_images") or []),
        "test_views": len(status.get("test_images") or []),
        "checkpoint_exists": bool(status.get("checkpoint_exists")),
        "render_exists": bool(status.get("render_exists")),
        "metrics_exists": bool(status.get("metrics_exists")),
        "train_seconds": train_stage.get("elapsed_seconds"),
        "peak_memory_used_mib": train_stage.get("peak_memory_used_mib"),
        "pointcloud_source": (status.get("pointcloud") or {}).get("path"),
        "failure_reason": status.get("failure_reason", ""),
    }


def aggregate_resolution(rows, resolution):
    subset = [row for row in rows if row["resolution"] == resolution]
    counts = Counter(row["status"] for row in subset)
    completed = [row for row in subset if row["status"] == "completed"]
    mean = None
    if len(completed) == len(LLFF_SCENES):
        mean = {
            metric: sum(float(row[metric]) for row in completed) / len(completed)
            for metric in ("psnr", "ssim", "lpips")
        }
    blocked = sum(count for status, count in counts.items() if status.startswith("blocked_"))
    baseline = FSGS_MEANS[resolution]
    return {
        "completed": counts["completed"], "failed": counts["failed"],
        "missing": counts["missing"], "blocked": blocked, "counts": dict(counts),
        "mean": mean, "fsgs_mean": baseline,
        "refgs_minus_fsgs": {
            metric: mean[metric] - baseline[metric] for metric in baseline
        } if mean else None,
    }


def _write_csv(path, rows):
    fields = list(rows[0]) if rows else []
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def _fsgs_rows(path):
    payload = read_json(path, {}) or {}
    return {(row["resolution"], row["scene"]): row for row in payload.get("rows", [])}


def summarize(log_root=DEFAULT_LOG_ROOT, fsgs_summary=DEFAULT_FSGS_SUMMARY):
    log_root = Path(log_root)
    rows = []
    for resolution in RESOLUTIONS:
        for scene in LLFF_SCENES:
            payload = read_json(log_root / resolution / scene / "status.json", {}) or {}
            rows.append(row_from_status(scene, resolution, payload))
    aggregates = {resolution: aggregate_resolution(rows, resolution) for resolution in RESOLUTIONS}
    _write_csv(log_root / "refgs_llff_summary.csv", rows)
    write_json(log_root / "refgs_llff_summary.json", {"rows": rows, "aggregates": aggregates})
    lines = [
        "# Ref-GS under the FSGS LLFF 3-view protocol", "",
        "This is a fair cross-method comparison, not a Ref-GS paper LLFF reproduction.",
        "Ref-GS original-paper LLFF three-view result: 原论文未提供", "",
    ]
    for resolution in RESOLUTIONS:
        aggregate = aggregates[resolution]
        lines.extend([
            "## {}".format(resolution), "",
            "- completed: {}".format(aggregate["completed"]),
            "- failed: {}".format(aggregate["failed"]),
            "- missing: {}".format(aggregate["missing"]),
            "- blocked: {}".format(aggregate["blocked"]), "",
            "| Scene | PSNR | SSIM | LPIPS | Train/Test | Checkpoint | Render | Metrics | Status |",
            "|---|---:|---:|---:|---:|---|---|---|---|",
        ])
        for row in (item for item in rows if item["resolution"] == resolution):
            value = lambda key, digits: "" if row[key] is None else ("{:.%df}" % digits).format(row[key])
            lines.append("| {} | {} | {} | {} | {}/{} | {} | {} | {} | {} |".format(
                row["scene"], value("psnr", 4), value("ssim", 6), value("lpips", 6),
                row["train_views"], row["test_views"], row["checkpoint_exists"],
                row["render_exists"], row["metrics_exists"], row["status"],
            ))
        mean = aggregate["mean"]
        lines.extend(["", "Eight-scene mean: " + (
            "PSNR {:.4f}, SSIM {:.6f}, LPIPS {:.6f}".format(mean["psnr"], mean["ssim"], mean["lpips"])
            if mean else "unavailable until all eight scenes complete"
        ), ""])
    (log_root / "refgs_llff_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    fsgs = _fsgs_rows(fsgs_summary)
    comparisons = []
    for row in rows:
        baseline = fsgs.get((row["resolution"], row["scene"]), {})
        item = {"resolution": row["resolution"], "scene": row["scene"], "refgs_status": row["status"]}
        for metric in ("psnr", "ssim", "lpips"):
            ref_value, fsgs_value = row[metric], baseline.get(metric)
            item["refgs_" + metric] = ref_value
            item["fsgs_" + metric] = fsgs_value
            item["delta_" + metric] = ref_value - fsgs_value if ref_value is not None and fsgs_value is not None else None
        comparisons.append(item)
    _write_csv(log_root / "refgs_vs_fsgs_llff.csv", comparisons)
    compare_lines = [
        "# Ref-GS vs FSGS LLFF", "", "All differences are Ref-GS - FSGS.",
        "PSNR/SSIM: larger is better. LPIPS: smaller is better.", "",
        "| Resolution | Scene | Delta PSNR | Delta SSIM | Delta LPIPS |",
        "|---|---|---:|---:|---:|",
    ]
    for row in comparisons:
        fmt = lambda key, digits: "" if row[key] is None else ("{:.%df}" % digits).format(row[key])
        compare_lines.append("| {} | {} | {} | {} | {} |".format(
            row["resolution"], row["scene"], fmt("delta_psnr", 4),
            fmt("delta_ssim", 6), fmt("delta_lpips", 6),
        ))
    (log_root / "refgs_vs_fsgs_llff.md").write_text("\n".join(compare_lines) + "\n", encoding="utf-8")
    return rows, aggregates


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarize Ref-GS FSGS-protocol LLFF runs")
    parser.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
    parser.add_argument("--fsgs-summary", type=Path, default=DEFAULT_FSGS_SUMMARY)
    args = parser.parse_args(argv)
    _, aggregates = summarize(args.log_root, args.fsgs_summary)
    print(json.dumps(aggregates, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
