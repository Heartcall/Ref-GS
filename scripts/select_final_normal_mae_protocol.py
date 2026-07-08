#!/usr/bin/env python3
"""Select and report final normal-MAE protocol candidates from protocol-grid evidence."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.eval_geometry import evaluate_scene


PAPER_NORMAL_MAE_DEG = 2.21
SCENE_MASK_POLICY = {
    "ball": "explicit_mask",
    "car": "source_rgba_alpha",
    "coffee": "source_rgba_alpha",
    "helmet": "source_rgba_alpha",
    "teapot": "source_rgba_alpha",
    "toaster": "source_rgba_alpha",
}


def read_csv(path: Path) -> List[Dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: List[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def choose_normal_space(space_rows: Sequence[Dict[str, str]]) -> Dict[str, object]:
    usable = [
        r
        for r in space_rows
        if r.get("scene") != "__average__"
        and r.get("absolute_dot") in ("False", "false", False, "")
        and r.get("flip_preset") == "none"
        and as_float(r.get("normal_mae_deg")) is not None
    ]
    grouped: Dict[str, List[float]] = {}
    for row in usable:
        grouped.setdefault(str(row.get("normal_space")), []).append(float(row["normal_mae_deg"]))
    means = {space: sum(values) / len(values) for space, values in grouped.items() if values}
    if not means:
        return {"normal_space": "as_saved", "status": "protocol_uncertain", "reason": "no_space_inference_rows"}
    ordered = sorted(means.items(), key=lambda item: item[1])
    if len(ordered) < 2 or abs(ordered[0][1] - ordered[1][1]) < 0.05:
        return {
            "normal_space": "as_saved",
            "status": "protocol_uncertain",
            "reason": "space_hypotheses_not_separable; using as_saved by conservative default",
            "space_means": means,
        }
    return {
        "normal_space": ordered[0][0],
        "status": "protocol_selected",
        "reason": "space hypothesis has distinguishable lower MAE; still diagnostic evidence",
        "space_means": means,
    }


def row_matches(
    row: Dict[str, str],
    scene: str,
    normal_key: str,
    iteration: int,
    mask_policy: str,
    normal_space: str,
) -> bool:
    return (
        row.get("scene") == scene
        and row.get("normal_key") == normal_key
        and str(row.get("iteration")) == str(iteration)
        and row.get("mask_policy") == mask_policy
        and row.get("normal_space") == normal_space
        and row.get("flip_preset") == "none"
        and row.get("absolute_dot") in ("False", "false", False, "")
    )


def select_rows(grid_rows: Sequence[Dict[str, str]], normal_space: str) -> List[Dict[str, object]]:
    scenes = sorted({r["scene"] for r in grid_rows if r.get("scene") and r.get("scene") != "__average__"})
    final_rows: List[Dict[str, object]] = []
    for iteration, checkpoint_role in ((30000, "final_paper_candidate"), (31000, "final_repro_checkpoint")):
        for normal_key in ("surf_normal", "rend_normal"):
            for scene in scenes:
                mask_policy = SCENE_MASK_POLICY.get(scene, "source_rgba_alpha")
                match = next((r for r in grid_rows if row_matches(r, scene, normal_key, iteration, mask_policy, normal_space)), None)
                if match is None and mask_policy != "auto":
                    match = next((r for r in grid_rows if row_matches(r, scene, normal_key, iteration, "auto", normal_space)), None)
                if match is None:
                    continue
                status = "protocol_uncertain"
                notes = [
                    "absolute_dot=false",
                    "normal key reported as candidate; paper key not public",
                    f"mask_policy={match.get('mask_policy')}",
                ]
                final_rows.append(
                    {
                        "dataset": match.get("dataset"),
                        "scene": scene,
                        "checkpoint_role": checkpoint_role,
                        "iteration": iteration,
                        "normal_key": normal_key,
                        "mask_policy": match.get("mask_policy"),
                        "normal_space": normal_space,
                        "absolute_dot": False,
                        "flip_preset": "none",
                        "normal_mae_deg": as_float(match.get("normal_mae_deg")),
                        "valid_pixel_ratio": as_float(match.get("valid_pixel_ratio")),
                        "valid_pixel_count": match.get("valid_pixel_count"),
                        "frame_count": match.get("frame_count"),
                        "missing_frame_count": match.get("missing_frame_count"),
                        "status": status,
                        "notes": "; ".join(notes),
                    }
                )
    for checkpoint_role in ("final_paper_candidate", "final_repro_checkpoint"):
        for normal_key in ("surf_normal", "rend_normal"):
            rows = [r for r in final_rows if r["checkpoint_role"] == checkpoint_role and r["normal_key"] == normal_key]
            values = [float(r["normal_mae_deg"]) for r in rows if r.get("normal_mae_deg") is not None]
            ratios = [float(r["valid_pixel_ratio"]) for r in rows if r.get("valid_pixel_ratio") is not None]
            if values:
                final_rows.append(
                    {
                        "dataset": "refnerf",
                        "scene": "__average__",
                        "checkpoint_role": checkpoint_role,
                        "iteration": 30000 if checkpoint_role == "final_paper_candidate" else 31000,
                        "normal_key": normal_key,
                        "mask_policy": "explicit_mask_if_available_else_source_rgba_alpha",
                        "normal_space": normal_space,
                        "absolute_dot": False,
                        "flip_preset": "none",
                        "normal_mae_deg": sum(values) / len(values),
                        "valid_pixel_ratio": sum(ratios) / len(ratios) if ratios else None,
                        "status": "protocol_uncertain",
                        "notes": f"average over {len(values)} scenes; not claimed as strict paper reproduction",
                    }
                )
    return final_rows


def select_exact_rows(
    grid_rows: Sequence[Dict[str, str]],
    normal_space: str,
    data_root: Path,
    output_root: Path,
) -> List[Dict[str, object]]:
    scenes = sorted({r["scene"] for r in grid_rows if r.get("scene") and r.get("scene") != "__average__"})
    final_rows: List[Dict[str, object]] = []
    for iteration, checkpoint_role in ((30000, "final_paper_candidate"), (31000, "final_repro_checkpoint")):
        for normal_key in ("surf_normal", "rend_normal"):
            for scene in scenes:
                mask_policy = SCENE_MASK_POLICY.get(scene, "source_rgba_alpha")
                row = evaluate_scene(
                    dataset="refnerf",
                    scene=scene,
                    data_root=data_root,
                    output_root=output_root,
                    iteration=iteration,
                    split="test",
                    metrics=("normal_mae",),
                    normal_space=normal_space,
                    mask_policy=mask_policy,
                    normal_source_key=normal_key,
                    flip_x=False,
                    flip_y=False,
                    flip_z=False,
                    absolute_dot=False,
                    protocol_name="final_normal_mae_exact",
                )
                final_rows.append(
                    {
                        "dataset": row.get("dataset"),
                        "scene": scene,
                        "checkpoint_role": checkpoint_role,
                        "iteration": iteration,
                        "normal_key": normal_key,
                        "mask_policy": mask_policy,
                        "normal_space": normal_space,
                        "absolute_dot": False,
                        "flip_preset": "none",
                        "normal_mae_deg": row.get("normal_mae_deg"),
                        "valid_pixel_ratio": row.get("valid_pixel_ratio"),
                        "valid_pixel_count": row.get("valid_pixel_count"),
                        "frame_count": row.get("frame_count"),
                        "missing_frame_count": row.get("missing_frame_count"),
                        "status": "protocol_uncertain",
                        "notes": "full-pixel exact eval for selected protocol; normal key/convention still not public",
                    }
                )
    for checkpoint_role in ("final_paper_candidate", "final_repro_checkpoint"):
        for normal_key in ("surf_normal", "rend_normal"):
            rows = [r for r in final_rows if r["checkpoint_role"] == checkpoint_role and r["normal_key"] == normal_key]
            values = [float(r["normal_mae_deg"]) for r in rows if r.get("normal_mae_deg") is not None]
            ratios = [float(r["valid_pixel_ratio"]) for r in rows if r.get("valid_pixel_ratio") is not None]
            if values:
                final_rows.append(
                    {
                        "dataset": "refnerf",
                        "scene": "__average__",
                        "checkpoint_role": checkpoint_role,
                        "iteration": 30000 if checkpoint_role == "final_paper_candidate" else 31000,
                        "normal_key": normal_key,
                        "mask_policy": "explicit_mask_if_available_else_source_rgba_alpha",
                        "normal_space": normal_space,
                        "absolute_dot": False,
                        "flip_preset": "none",
                        "normal_mae_deg": sum(values) / len(values),
                        "valid_pixel_ratio": sum(ratios) / len(ratios) if ratios else None,
                        "status": "protocol_uncertain",
                        "notes": f"full-pixel exact average over {len(values)} scenes; not claimed as strict paper reproduction",
                    }
                )
    return final_rows


def markdown_report(
    final_rows: Sequence[Dict[str, object]],
    grid_rows: Sequence[Dict[str, str]],
    space_choice: Dict[str, object],
    diagnosis: Dict[str, object],
) -> str:
    old_avg = diagnosis.get("reproduced_average_normal_mae_deg")
    old_scene = diagnosis.get("per_scene_normal_mae_deg", {})
    avg_rows = [r for r in final_rows if r.get("scene") == "__average__"]
    lines = [
        "# Normal MAE Protocol Report",
        "",
        "## Executive summary",
        "",
        f"- Paper Ref-GS ShinyB target used for comparison: {PAPER_NORMAL_MAE_DEG:.2f} deg.",
        f"- Previous reproduced Ref-NeRF/Shiny normal MAE: {old_avg:.6f} deg." if old_avg is not None else "- Previous reproduced normal MAE: unavailable.",
        "- Final rows keep `absolute_dot=false`; absolute-dot and convention-sweep rows are diagnostic only.",
        "- The public protocol still does not identify the exact normal key/convention, so final status remains `protocol_uncertain` unless separately confirmed.",
        "",
        "## Final protocol",
        "",
        "| Field | Value |",
        "|---|---|",
        "| normal_key | surf_normal and rend_normal reported separately |",
        "| mask_policy | explicit_mask if available, else source_rgba_alpha |",
        f"| normal_space | {space_choice.get('normal_space')} ({space_choice.get('reason')}) |",
        "| iteration | 30000 for paper candidate; 31000 for current reproduction checkpoint |",
        "| absolute_dot | false |",
        "",
        "## Dataset average",
        "",
        "| Checkpoint role | Iteration | Normal key | Avg normal MAE deg | Gap to old 8.826 | Gap to paper 2.21 | Status |",
        "|---|---:|---|---:|---:|---:|---|",
    ]
    for row in avg_rows:
        mae = row.get("normal_mae_deg")
        if mae is None:
            continue
        old_gap = float(mae) - float(old_avg) if old_avg is not None else None
        paper_gap = float(mae) - PAPER_NORMAL_MAE_DEG
        lines.append(
            f"| {row.get('checkpoint_role')} | {row.get('iteration')} | {row.get('normal_key')} | "
            f"{float(mae):.6f} | {old_gap:.6f} | {paper_gap:.6f} | {row.get('status')} |"
        )
    lines.extend(
        [
            "",
            "## Per-scene final normal MAE",
            "",
            "| Role | Iteration | Normal key | Scene | New MAE deg | Old MAE deg | Delta vs old | Valid ratio |",
            "|---|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in final_rows:
        if row.get("scene") == "__average__":
            continue
        mae = row.get("normal_mae_deg")
        old = old_scene.get(str(row.get("scene"))) if isinstance(old_scene, dict) else None
        delta = float(mae) - float(old) if mae is not None and old is not None else None
        valid_ratio = row.get("valid_pixel_ratio")
        lines.append(
            f"| {row.get('checkpoint_role')} | {row.get('iteration')} | {row.get('normal_key')} | {row.get('scene')} | "
            f"{'' if mae is None else f'{float(mae):.6f}'} | {'' if old is None else f'{float(old):.6f}'} | "
            f"{'' if delta is None else f'{delta:.6f}'} | {'' if valid_ratio is None else f'{float(valid_ratio):.6f}'} |"
        )
    lines.extend(
        [
            "",
            "## Ablation notes",
            "",
            "- `normal_mae_protocol_grid.csv` contains surf_normal vs rend_normal, 30000 vs 31000, mask policies, spaces, flips, and absolute-dot diagnostics.",
            "- `gt_normal_space_inference.csv` is evidence for GT space/convention only; lowest rows are not automatically selected.",
            "- Reaching the paper value requires both a public protocol match and a comparable MAE near 2.21 deg.",
            "",
            "## Paper-level conclusion",
            "",
            "This run must not be described as `已复现论文 normal MAE` while the normal key and GT convention remain uncertain or the average remains far from 2.21 deg.",
            "Remaining causes can include training geometry quality, unpublished paper evaluation details, normal-key ambiguity, and GT normal convention ambiguity.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid", type=Path, required=True)
    parser.add_argument("--space-inference", type=Path, required=True)
    parser.add_argument("--diagnosis", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=Path("/data/liuly/dataset/3DGS"))
    parser.add_argument("--output-root", type=Path, default=Path("output/normal_mae_protocol_debug"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    grid_rows = read_csv(args.grid)
    space_rows = read_csv(args.space_inference)
    with args.diagnosis.open(encoding="utf-8") as handle:
        diagnosis = json.load(handle)
    space_choice = choose_normal_space(space_rows)
    final_rows = select_exact_rows(grid_rows, str(space_choice["normal_space"]), args.data_root, args.output_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "final_normal_mae.csv", final_rows)
    (args.output_dir / "final_normal_mae.json").write_text(
        json.dumps({"space_choice": space_choice, "rows": final_rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "normal_mae_protocol_report.md").write_text(
        markdown_report(final_rows, grid_rows, space_choice, diagnosis),
        encoding="utf-8",
    )
    print(f"Wrote {args.output_dir / 'normal_mae_protocol_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
