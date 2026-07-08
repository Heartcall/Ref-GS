#!/usr/bin/env python3
"""Evaluate a normal-MAE protocol grid over exported normal-key buffers."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.eval_geometry import (
    DEFAULT_SCENES,
    dataset_scene_root,
    find_gt_normal,
    geometry_dir,
    list_prediction_frames,
    load_explicit_mask,
    resize_array,
    transform_for_declared_space,
)
from scripts.normal_mae_protocol import (
    apply_axis_flip,
    build_eval_mask,
    load_gt_normal_alpha,
    load_normal,
    load_rgba_alpha_from_source_image,
    load_transforms_frames,
    normalize_normals,
)


FLIP_PRESETS = {
    "none": (False, False, False),
    "flip_y": (False, True, False),
    "flip_z": (False, False, True),
    "flip_yz": (False, True, True),
}
MASK_POLICIES = ("source_rgba_alpha", "gt_normal_alpha", "gt_normal_nonzero", "auto")
NORMAL_SPACES = ("as_saved", "camera", "world")


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


def init_stats() -> Dict[str, float]:
    return {"mae_sum": 0.0, "ok_frames": 0, "valid_pixels": 0, "total_pixels": 0, "missing_frames": 0}


def base_dot_and_valid(pred: np.ndarray, gt: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    pred_n = normalize_normals(pred)
    gt_n = normalize_normals(gt)
    valid = np.isfinite(pred_n).all(axis=-1) & np.isfinite(gt_n).all(axis=-1)
    valid &= np.linalg.norm(pred_n, axis=-1) > 1e-6
    valid &= np.linalg.norm(gt_n, axis=-1) > 1e-6
    dot = np.sum(pred_n * gt_n, axis=-1)
    return dot, valid


def angle_stats_from_dot(dot: np.ndarray, base_valid: np.ndarray, mask: Optional[np.ndarray], absolute_dot: bool) -> Tuple[Optional[float], int]:
    valid = base_valid
    if mask is not None:
        valid = valid & np.asarray(mask, dtype=bool)
    if not np.any(valid):
        return None, 0
    selected = dot[valid]
    if absolute_dot:
        selected = np.abs(selected)
    angles = np.degrees(np.arccos(np.clip(selected, -1.0, 1.0)))
    return float(np.mean(angles)), int(valid.sum())


def sample_frame_inputs(
    pred: np.ndarray,
    gt: np.ndarray,
    masks: Dict[str, Optional[np.ndarray]],
    max_pixels: int,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Optional[np.ndarray]], int, int]:
    total = int(pred.shape[0] * pred.shape[1])
    if max_pixels <= 0 or total <= max_pixels:
        return pred, gt, masks, total, total
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(total, size=max_pixels, replace=False))
    sampled_masks = {}
    for key, mask in masks.items():
        sampled_masks[key] = None if mask is None else np.asarray(mask, dtype=bool).reshape(-1)[idx]
    return pred.reshape(-1, 3)[idx], gt.reshape(-1, 3)[idx], sampled_masks, total, max_pixels


def empty_scene_row(
    dataset: str,
    scene: str,
    iteration: int,
    normal_key: str,
    mask_policy: str,
    normal_space: str,
    flip_name: str,
    absolute_dot: bool,
    status: str,
    notes: str,
) -> Dict[str, object]:
    flips = FLIP_PRESETS[flip_name]
    return {
        "dataset": dataset,
        "scene": scene,
        "split": "test",
        "iteration": iteration,
        "normal_key": normal_key,
        "mask_policy": mask_policy,
        "normal_space": normal_space,
        "absolute_dot": absolute_dot,
        "flip_x": flips[0],
        "flip_y": flips[1],
        "flip_z": flips[2],
        "flip_preset": flip_name,
        "normal_mae_deg": None,
        "valid_pixel_count": 0,
        "valid_pixel_ratio": None,
        "frame_count": 0,
        "missing_frame_count": 0,
        "status": status,
        "notes": notes,
        "diagnostic_only": bool(absolute_dot),
    }


def evaluate_scene_grid(
    dataset: str,
    scene: str,
    data_root: Path,
    output_root: Path,
    iteration: int,
    normal_key: str,
    max_pixels_per_frame: int,
    max_frames: int,
) -> List[Dict[str, object]]:
    scene_root = dataset_scene_root(data_root, dataset, scene)
    geom_dir = geometry_dir(output_root, dataset, scene, "test", iteration, normal_source_key=normal_key)
    frames = list_prediction_frames(geom_dir)
    original_frame_count = len(frames)
    if max_frames > 0:
        frames = frames[:max_frames]
    combo_stats: Dict[Tuple[str, str, str, bool], Dict[str, float]] = {}
    for mask_policy in MASK_POLICIES:
        for normal_space in NORMAL_SPACES:
            for flip_name in FLIP_PRESETS:
                for absolute_dot in (False, True):
                    combo_stats[(mask_policy, normal_space, flip_name, absolute_dot)] = init_stats()
    if not frames:
        return [
            empty_scene_row(dataset, scene, iteration, normal_key, mask_policy, normal_space, flip_name, absolute_dot, "missing_prediction_normal", "geometry normal buffers not found")
            for mask_policy in MASK_POLICIES
            for normal_space in NORMAL_SPACES
            for flip_name in FLIP_PRESETS
            for absolute_dot in (False, True)
        ]
    try:
        transform_frames = load_transforms_frames(scene_root, "test")
    except Exception as exc:
        transform_frames = {}
        transform_note = f"missing_or_unreadable_transforms:{exc}"
    else:
        transform_note = ""

    for frame in frames:
        pred_path = geom_dir / "normal" / f"{frame}.npy"
        gt_path = find_gt_normal(scene_root, "test", frame)
        if gt_path is None:
            for stats in combo_stats.values():
                stats["missing_frames"] += 1
            continue
        pred = np.load(str(pred_path)).astype(np.float32)
        gt, gt_alpha = load_normal(gt_path)
        pred, _ = resize_array(pred, gt.shape[:2], is_normal=True)
        frame_info = transform_frames.get(frame)
        R = None if frame_info is None else frame_info["R"]
        source_alpha = load_rgba_alpha_from_source_image(frame_info["frame"], scene_root) if frame_info else load_rgba_alpha_from_source_image(frame, scene_root)
        if gt_alpha is None:
            gt_alpha = load_gt_normal_alpha(gt_path)
        explicit_mask = load_explicit_mask(scene_root, "test", frame)
        masks = {}
        for mask_policy in MASK_POLICIES:
            try:
                masks[mask_policy] = build_eval_mask(
                    mask_policy=mask_policy,
                    explicit_mask=explicit_mask,
                    source_rgba_alpha=source_alpha,
                    gt_normal_alpha=gt_alpha,
                    gt_normal=gt,
                    shape_hw=gt.shape[:2],
                )
            except ValueError:
                masks[mask_policy] = None
        total_pixels = int(gt.shape[0] * gt.shape[1])
        pred_eval, gt_eval, masks_eval, original_pixels, evaluated_pixels = sample_frame_inputs(
            pred,
            gt,
            masks,
            max_pixels_per_frame,
            seed=hash((dataset, scene, iteration, normal_key, frame)) & 0xFFFFFFFF,
        )
        for normal_space in NORMAL_SPACES:
            gt_space = transform_for_declared_space(gt_eval, R, normal_space)
            for flip_name, flips in FLIP_PRESETS.items():
                pred_variant = apply_axis_flip(pred_eval, *flips)
                pred_space = transform_for_declared_space(pred_variant, R, normal_space)
                dot, base_valid = base_dot_and_valid(pred_space, gt_space)
                for mask_policy, mask in masks_eval.items():
                    for absolute_dot in (False, True):
                        mae, valid = angle_stats_from_dot(dot, base_valid, mask, absolute_dot)
                        stats = combo_stats[(mask_policy, normal_space, flip_name, absolute_dot)]
                        stats["total_pixels"] += evaluated_pixels if max_pixels_per_frame > 0 else original_pixels
                        if mae is not None:
                            stats["mae_sum"] += mae
                            stats["ok_frames"] += 1
                            stats["valid_pixels"] += valid
    rows: List[Dict[str, object]] = []
    for (mask_policy, normal_space, flip_name, absolute_dot), stats in combo_stats.items():
        flips = FLIP_PRESETS[flip_name]
        if stats["ok_frames"] == 0:
            mae = None
            status = "no_valid_normal_pixels"
        else:
            mae = stats["mae_sum"] / stats["ok_frames"]
            status = "ok"
        notes = transform_note
        if max_pixels_per_frame > 0:
            notes = "; ".join([n for n in (notes, f"diagnostic_grid_sampled_max_pixels_per_frame={max_pixels_per_frame}") if n])
        if max_frames > 0 and original_frame_count > len(frames):
            notes = "; ".join([n for n in (notes, f"diagnostic_grid_sampled_frames={len(frames)}_of_{original_frame_count}") if n])
        if mask_policy == "explicit_mask" and scene != "ball":
            notes = "; ".join([n for n in (notes, "explicit mask may be unavailable for this scene") if n])
        rows.append(
            {
                "dataset": dataset,
                "scene": scene,
                "split": "test",
                "iteration": iteration,
                "normal_key": normal_key,
                "mask_policy": mask_policy,
                "normal_space": normal_space,
                "absolute_dot": absolute_dot,
                "flip_x": flips[0],
                "flip_y": flips[1],
                "flip_z": flips[2],
                "flip_preset": flip_name,
                "normal_mae_deg": mae,
                "valid_pixel_count": int(stats["valid_pixels"]),
                "valid_pixel_ratio": (float(stats["valid_pixels"]) / float(stats["total_pixels"])) if stats["total_pixels"] else None,
                "frame_count": len(frames),
                "missing_frame_count": int(stats["missing_frames"]),
                "status": status,
                "notes": notes,
                "diagnostic_only": bool(absolute_dot),
            }
        )
    return rows


def aggregate_rows(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    valid = [r for r in rows if r.get("normal_mae_deg") is not None]
    base = dict(rows[0]) if rows else {}
    base["scene"] = "__average__"
    base["status"] = "ok" if len(valid) == len(rows) else "partial"
    base["normal_mae_deg"] = sum(float(r["normal_mae_deg"]) for r in valid) / len(valid) if valid else None
    ratios = [float(r["valid_pixel_ratio"]) for r in valid if r.get("valid_pixel_ratio") is not None]
    base["valid_pixel_ratio"] = sum(ratios) / len(ratios) if ratios else None
    base["frame_count"] = sum(int(r.get("frame_count") or 0) for r in rows)
    base["missing_frame_count"] = sum(int(r.get("missing_frame_count") or 0) for r in rows)
    base["valid_pixel_count"] = sum(int(r.get("valid_pixel_count") or 0) for r in rows)
    base["notes"] = f"dataset_average_over_{len(valid)}_valid_scenes"
    return base


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("refnerf",), required=True)
    parser.add_argument("--scene", nargs="+")
    parser.add_argument("--iteration", nargs="+", type=int, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("output/normal_mae_protocol_debug"))
    parser.add_argument("--data-root", type=Path, default=Path("/data/liuly/dataset/3DGS"))
    parser.add_argument("--log-root", type=Path, default=Path("logs/repro/normal_mae_protocol_debug"))
    parser.add_argument("--max-pixels-per-frame", type=int, default=500, help="Deterministic per-frame sample for the diagnostic grid; use <=0 for full pixels.")
    parser.add_argument("--max-frames", type=int, default=20, help="First N frames for diagnostic grid; use <=0 for all frames.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenes = args.scene or DEFAULT_SCENES[args.dataset]
    all_rows: List[Dict[str, object]] = []
    for normal_key in ("surf_normal", "rend_normal"):
        for iteration in args.iteration:
            combo_bucket: Dict[Tuple[str, str, str, bool], List[Dict[str, object]]] = {}
            for scene in scenes:
                scene_rows = evaluate_scene_grid(
                    args.dataset,
                    scene,
                    args.data_root,
                    args.output_root,
                    iteration,
                    normal_key,
                    args.max_pixels_per_frame,
                    args.max_frames,
                )
                all_rows.extend(scene_rows)
                for row in scene_rows:
                    key = (str(row["mask_policy"]), str(row["normal_space"]), str(row["flip_preset"]), bool(row["absolute_dot"]))
                    combo_bucket.setdefault(key, []).append(row)
                print(f"[grid] evaluated {args.dataset}/{scene} iter={iteration} key={normal_key}")
            for key, rows in combo_bucket.items():
                avg = aggregate_rows(rows)
                all_rows.append(avg)
                print(f"[grid] avg key={normal_key} iter={iteration} mask={key[0]} space={key[1]} flip={key[2]} abs={key[3]} mae={avg['normal_mae_deg']}")
    args.log_root.mkdir(parents=True, exist_ok=True)
    write_csv(args.log_root / "normal_mae_protocol_grid.csv", all_rows)
    (args.log_root / "normal_mae_protocol_grid.json").write_text(json.dumps(all_rows, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.log_root / 'normal_mae_protocol_grid.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
