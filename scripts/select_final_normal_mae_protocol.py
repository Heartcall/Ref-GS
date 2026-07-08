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

import numpy as np

from scripts.eval_geometry import (
    dataset_scene_root,
    find_gt_normal,
    geometry_dir,
    list_prediction_frames,
    load_explicit_mask,
    resize_array,
    transform_for_declared_space,
)
from scripts.normal_mae_protocol import (
    build_eval_mask,
    load_gt_normal_alpha,
    load_normal,
    load_rgba_alpha_from_source_image,
    load_transforms_frames,
    normalize_normals,
)


PAPER_NORMAL_MAE_DEG = 2.21
SCENE_MASK_POLICY = {
    "ball": "source_rgba_alpha",
    "car": "source_rgba_alpha",
    "coffee": "source_rgba_alpha",
    "helmet": "source_rgba_alpha",
    "teapot": "source_rgba_alpha",
    "toaster": "source_rgba_alpha",
}


def _sample_pixels(
    pred: np.ndarray,
    gt: np.ndarray,
    mask: Optional[np.ndarray],
    max_pixels_per_frame: int,
    seed: int,
) -> tuple:
    total = int(pred.shape[0] * pred.shape[1])
    if max_pixels_per_frame <= 0 or total <= max_pixels_per_frame:
        return pred, gt, mask, total, total
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(total, size=max_pixels_per_frame, replace=False))
    pred_s = pred.reshape(-1, 3)[idx]
    gt_s = gt.reshape(-1, 3)[idx]
    mask_s = None if mask is None else np.asarray(mask, dtype=bool).reshape(-1)[idx]
    return pred_s, gt_s, mask_s, total, int(max_pixels_per_frame)


def _angle_sum_and_count(pred: np.ndarray, gt: np.ndarray, mask: Optional[np.ndarray]) -> tuple:
    pred_n = normalize_normals(pred)
    gt_n = normalize_normals(gt)
    valid = np.isfinite(pred_n).all(axis=-1) & np.isfinite(gt_n).all(axis=-1)
    valid &= np.linalg.norm(pred_n, axis=-1) > 1e-6
    valid &= np.linalg.norm(gt_n, axis=-1) > 1e-6
    if mask is not None:
        valid &= np.asarray(mask, dtype=bool)
    if not np.any(valid):
        return 0.0, 0
    dot = np.sum(pred_n[valid] * gt_n[valid], axis=-1)
    angles = np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))
    return float(np.sum(angles, dtype=np.float64)), int(valid.sum())


def _mask_with_fallback(
    preferred_policy: str,
    explicit_mask: Optional[np.ndarray],
    source_alpha: Optional[np.ndarray],
    gt_alpha: Optional[np.ndarray],
    gt: np.ndarray,
) -> tuple:
    policies = [preferred_policy]
    for fallback in ("gt_normal_alpha", "source_rgba_alpha", "gt_normal_nonzero"):
        if fallback not in policies:
            policies.append(fallback)
    for policy in policies:
        mask = build_eval_mask(
            mask_policy=policy,
            explicit_mask=explicit_mask,
            source_rgba_alpha=source_alpha,
            gt_normal_alpha=gt_alpha,
            gt_normal=gt,
            shape_hw=gt.shape[:2],
        )
        if mask is not None:
            return mask, policy
    return None, "none"


def evaluate_final_protocol_scene(
    scene: str,
    iteration: int,
    normal_key: str,
    mask_policy: str,
    normal_space: str,
    data_root: Path,
    output_root: Path,
    max_frames: int = 0,
    max_pixels_per_frame: int = 0,
) -> Dict[str, object]:
    scene_root = dataset_scene_root(data_root, "refnerf", scene)
    geom_dir = geometry_dir(output_root, "refnerf", scene, "test", iteration, normal_source_key=normal_key)
    frames = list_prediction_frames(geom_dir)
    original_frame_count = len(frames)
    if max_frames > 0:
        frames = frames[:max_frames]
    sampled = (max_frames > 0 and original_frame_count > len(frames)) or max_pixels_per_frame > 0
    if not frames:
        return {
            "dataset": "refnerf",
            "scene": scene,
            "iteration": iteration,
            "normal_key": normal_key,
            "mask_policy": mask_policy,
            "mask_policy_actual": None,
            "normal_space": normal_space,
            "absolute_dot": False,
            "flip_preset": "none",
            "normal_mae_deg": None,
            "valid_pixel_ratio": None,
            "valid_pixel_count": 0,
            "evaluated_pixel_count": 0,
            "frame_count": 0,
            "source_frame_count": original_frame_count,
            "missing_frame_count": 0,
            "eval_mode": "sampled" if sampled else "full",
            "status": "missing_prediction_normal",
            "notes": f"missing geometry normals under {geom_dir}",
        }
    try:
        transform_frames = load_transforms_frames(scene_root, "test")
    except Exception as exc:
        transform_frames = {}
        transform_note = f"missing_or_unreadable_transforms:{exc}"
    else:
        transform_note = ""

    angle_sum = 0.0
    valid_total = 0
    evaluated_total = 0
    missing = 0
    mask_actual_counts: Dict[str, int] = {}
    notes = []
    if transform_note:
        notes.append(transform_note)
    if sampled:
        notes.append("sampled_eval_not_full_result")
    if max_frames > 0 and original_frame_count > len(frames):
        notes.append(f"sampled_frames={len(frames)}_of_{original_frame_count}")
    if max_pixels_per_frame > 0:
        notes.append(f"sampled_max_pixels_per_frame={max_pixels_per_frame}")

    for frame in frames:
        pred_path = geom_dir / "normal" / f"{frame}.npy"
        gt_path = find_gt_normal(scene_root, "test", frame)
        if gt_path is None or not pred_path.exists():
            missing += 1
            continue
        pred = np.load(str(pred_path)).astype(np.float32)
        gt, gt_alpha = load_normal(gt_path)
        pred, resize_note = resize_array(pred, gt.shape[:2], is_normal=True)
        if resize_note and resize_note not in notes:
            notes.append(resize_note)
        frame_info = transform_frames.get(frame)
        R = None if frame_info is None else frame_info["R"]
        source_alpha = load_rgba_alpha_from_source_image(frame_info["frame"], scene_root) if frame_info else load_rgba_alpha_from_source_image(frame, scene_root)
        if gt_alpha is None:
            gt_alpha = load_gt_normal_alpha(gt_path)
        explicit_mask = load_explicit_mask(scene_root, "test", frame)
        mask, actual_policy = _mask_with_fallback(mask_policy, explicit_mask, source_alpha, gt_alpha, gt)
        mask_actual_counts[actual_policy] = mask_actual_counts.get(actual_policy, 0) + 1
        pred = transform_for_declared_space(pred, R, normal_space)
        gt = transform_for_declared_space(gt, R, normal_space)
        pred_eval, gt_eval, mask_eval, _original_pixels, evaluated_pixels = _sample_pixels(
            pred,
            gt,
            mask,
            max_pixels_per_frame,
            seed=hash(("final", scene, iteration, normal_key, frame)) & 0xFFFFFFFF,
        )
        frame_angle_sum, frame_valid = _angle_sum_and_count(pred_eval, gt_eval, mask_eval)
        angle_sum += frame_angle_sum
        valid_total += frame_valid
        evaluated_total += evaluated_pixels

    mae = float(angle_sum / valid_total) if valid_total else None
    eval_mode = "sampled" if sampled else "full"
    if mae is None:
        status = "no_valid_normal_pixels"
    elif sampled:
        status = "protocol_uncertain_sampled"
    else:
        status = "protocol_uncertain"
    actual_policy = ",".join(f"{key}:{value}" for key, value in sorted(mask_actual_counts.items())) or None
    return {
        "dataset": "refnerf",
        "scene": scene,
        "iteration": iteration,
        "normal_key": normal_key,
        "mask_policy": mask_policy,
        "mask_policy_actual": actual_policy,
        "normal_space": normal_space,
        "absolute_dot": False,
        "flip_preset": "none",
        "normal_mae_deg": mae,
        "valid_pixel_ratio": float(valid_total / evaluated_total) if evaluated_total else None,
        "valid_pixel_count": valid_total,
        "evaluated_pixel_count": evaluated_total,
        "frame_count": len(frames),
        "source_frame_count": original_frame_count,
        "missing_frame_count": missing,
        "eval_mode": eval_mode,
        "status": status,
        "notes": "; ".join(notes),
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
    max_frames: int = 0,
    max_pixels_per_frame: int = 0,
) -> List[Dict[str, object]]:
    scenes = sorted({r["scene"] for r in grid_rows if r.get("scene") and r.get("scene") != "__average__"})
    final_rows: List[Dict[str, object]] = []
    combos = [
        (30000, "final_paper_candidate", "surf_normal"),
        (30000, "final_paper_candidate", "rend_normal"),
        (31000, "final_repro_checkpoint", "surf_normal"),
        (31000, "final_repro_checkpoint", "rend_normal"),
    ]
    for scene in scenes:
        scene_root = dataset_scene_root(data_root, "refnerf", scene)
        mask_policy = SCENE_MASK_POLICY.get(scene, "source_rgba_alpha")
        try:
            transform_frames = load_transforms_frames(scene_root, "test")
            transform_note = ""
        except Exception as exc:
            transform_frames = {}
            transform_note = f"missing_or_unreadable_transforms:{exc}"

        combo_state: Dict[tuple, Dict[str, object]] = {}
        frame_to_keys: Dict[str, List[tuple]] = {}
        for iteration, checkpoint_role, normal_key in combos:
            key = (iteration, checkpoint_role, normal_key)
            geom = geometry_dir(output_root, "refnerf", scene, "test", iteration, normal_source_key=normal_key)
            frames = list_prediction_frames(geom)
            original_frame_count = len(frames)
            if max_frames > 0:
                frames = frames[:max_frames]
            sampled = (max_frames > 0 and original_frame_count > len(frames)) or max_pixels_per_frame > 0
            notes = []
            if transform_note:
                notes.append(transform_note)
            if sampled:
                notes.append("sampled_eval_not_full_result")
            if max_frames > 0 and original_frame_count > len(frames):
                notes.append(f"sampled_frames={len(frames)}_of_{original_frame_count}")
            if max_pixels_per_frame > 0:
                notes.append(f"sampled_max_pixels_per_frame={max_pixels_per_frame}")
            combo_state[key] = {
                "geom": geom,
                "frames": set(frames),
                "original_frame_count": original_frame_count,
                "sampled": sampled,
                "angle_sum": 0.0,
                "valid_total": 0,
                "evaluated_total": 0,
                "missing": 0,
                "mask_actual_counts": {},
                "notes": notes,
            }
            for frame in frames:
                frame_to_keys.setdefault(frame, []).append(key)

        for frame, keys_for_frame in sorted(frame_to_keys.items()):
            gt_path = find_gt_normal(scene_root, "test", frame)
            if gt_path is None:
                for key in keys_for_frame:
                    combo_state[key]["missing"] = int(combo_state[key]["missing"]) + 1
                continue
            gt, gt_alpha = load_normal(gt_path)
            if gt_alpha is None:
                gt_alpha = load_gt_normal_alpha(gt_path)
            frame_info = transform_frames.get(frame)
            R = None if frame_info is None else frame_info["R"]
            source_alpha = (
                load_rgba_alpha_from_source_image(frame_info["frame"], scene_root)
                if frame_info
                else load_rgba_alpha_from_source_image(frame, scene_root)
            )
            explicit_mask = load_explicit_mask(scene_root, "test", frame)
            mask, actual_policy = _mask_with_fallback(mask_policy, explicit_mask, source_alpha, gt_alpha, gt)
            gt_eval_space = transform_for_declared_space(gt, R, normal_space)

            for key in keys_for_frame:
                iteration, _checkpoint_role, normal_key = key
                state = combo_state[key]
                pred_path = state["geom"] / "normal" / f"{frame}.npy"
                if not pred_path.exists():
                    state["missing"] = int(state["missing"]) + 1
                    continue
                pred = np.load(str(pred_path)).astype(np.float32)
                pred, resize_note = resize_array(pred, gt.shape[:2], is_normal=True)
                if resize_note and resize_note not in state["notes"]:
                    state["notes"].append(resize_note)
                pred_eval_space = transform_for_declared_space(pred, R, normal_space)
                pred_eval, gt_eval, mask_eval, _original_pixels, evaluated_pixels = _sample_pixels(
                    pred_eval_space,
                    gt_eval_space,
                    mask,
                    max_pixels_per_frame,
                    seed=hash(("final", scene, iteration, normal_key, frame)) & 0xFFFFFFFF,
                )
                frame_angle_sum, frame_valid = _angle_sum_and_count(pred_eval, gt_eval, mask_eval)
                state["angle_sum"] = float(state["angle_sum"]) + frame_angle_sum
                state["valid_total"] = int(state["valid_total"]) + frame_valid
                state["evaluated_total"] = int(state["evaluated_total"]) + evaluated_pixels
                mask_counts = state["mask_actual_counts"]
                mask_counts[actual_policy] = mask_counts.get(actual_policy, 0) + 1

        for iteration, checkpoint_role, normal_key in combos:
            key = (iteration, checkpoint_role, normal_key)
            state = combo_state[key]
            frames = state["frames"]
            valid_total = int(state["valid_total"])
            evaluated_total = int(state["evaluated_total"])
            mae = float(state["angle_sum"] / valid_total) if valid_total else None
            eval_mode = "sampled" if state["sampled"] else "full"
            if len(frames) == 0:
                status = "missing_prediction_normal"
                state["notes"].append(f"missing geometry normals under {state['geom']}")
            elif mae is None:
                status = "no_valid_normal_pixels"
            elif state["sampled"]:
                status = "protocol_uncertain_sampled"
            else:
                status = "protocol_uncertain"
            mask_counts = state["mask_actual_counts"]
            mask_actual = ",".join(f"{key}:{value}" for key, value in sorted(mask_counts.items())) or None
            final_rows.append(
                {
                    "dataset": "refnerf",
                    "scene": scene,
                    "checkpoint_role": checkpoint_role,
                    "iteration": iteration,
                    "normal_key": normal_key,
                    "mask_policy": mask_policy,
                    "mask_policy_actual": mask_actual,
                    "normal_space": normal_space,
                    "absolute_dot": False,
                    "flip_preset": "none",
                    "normal_mae_deg": mae,
                    "valid_pixel_ratio": float(valid_total / evaluated_total) if evaluated_total else None,
                    "valid_pixel_count": valid_total,
                    "evaluated_pixel_count": evaluated_total,
                    "frame_count": len(frames),
                    "source_frame_count": state["original_frame_count"],
                    "missing_frame_count": state["missing"],
                    "eval_mode": eval_mode,
                    "status": status,
                    "notes": "; ".join(
                        n
                        for n in (
                            "selected protocol eval",
                            "normal key/convention still not public",
                            *state["notes"],
                        )
                        if n
                    ),
                }
            )
    for checkpoint_role in ("final_paper_candidate", "final_repro_checkpoint"):
        for normal_key in ("surf_normal", "rend_normal"):
            rows = [r for r in final_rows if r["checkpoint_role"] == checkpoint_role and r["normal_key"] == normal_key]
            values = [float(r["normal_mae_deg"]) for r in rows if r.get("normal_mae_deg") is not None]
            ratios = [float(r["valid_pixel_ratio"]) for r in rows if r.get("valid_pixel_ratio") is not None]
            eval_modes = sorted({str(r.get("eval_mode")) for r in rows if r.get("eval_mode")})
            statuses = sorted({str(r.get("status")) for r in rows if r.get("status")})
            if values:
                final_rows.append(
                    {
                        "dataset": "refnerf",
                        "scene": "__average__",
                        "checkpoint_role": checkpoint_role,
                        "iteration": 30000 if checkpoint_role == "final_paper_candidate" else 31000,
                        "normal_key": normal_key,
                        "mask_policy": "source_rgba_alpha_with_alpha_fallback",
                        "normal_space": normal_space,
                        "absolute_dot": False,
                        "flip_preset": "none",
                        "normal_mae_deg": sum(values) / len(values),
                        "valid_pixel_ratio": sum(ratios) / len(ratios) if ratios else None,
                        "eval_mode": ",".join(eval_modes),
                        "status": "protocol_uncertain_sampled" if "sampled" in eval_modes else "protocol_uncertain",
                        "notes": f"average over {len(values)} scenes; row statuses={','.join(statuses)}; not claimed as strict paper reproduction",
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
    chosen_space = str(space_choice.get("normal_space"))

    def fmt(value: object, digits: int = 6) -> str:
        number = as_float(value)
        return "" if number is None else f"{number:.{digits}f}"

    def grid_average_rows(
        *,
        iteration: Optional[int] = None,
        normal_key: Optional[str] = None,
        mask_policy: Optional[str] = None,
        normal_space: Optional[str] = None,
        flip_preset: str = "none",
        absolute_dot: str = "False",
    ) -> List[Dict[str, str]]:
        rows = []
        for row in grid_rows:
            if row.get("scene") != "__average__":
                continue
            if iteration is not None and str(row.get("iteration")) != str(iteration):
                continue
            if normal_key is not None and row.get("normal_key") != normal_key:
                continue
            if mask_policy is not None and row.get("mask_policy") != mask_policy:
                continue
            if normal_space is not None and row.get("normal_space") != normal_space:
                continue
            if row.get("flip_preset") != flip_preset:
                continue
            if row.get("absolute_dot") not in (absolute_dot, absolute_dot.lower()):
                continue
            if as_float(row.get("normal_mae_deg")) is None:
                continue
            rows.append(row)
        return sorted(
            rows,
            key=lambda row: (
                int(row.get("iteration", 0)),
                row.get("normal_key", ""),
                row.get("mask_policy", ""),
                row.get("normal_space", ""),
                row.get("flip_preset", ""),
            ),
        )

    def average_lookup(iteration: int, normal_key: str) -> Optional[float]:
        for row in avg_rows:
            if str(row.get("iteration")) == str(iteration) and row.get("normal_key") == normal_key:
                return as_float(row.get("normal_mae_deg"))
        return None

    paper_surf = average_lookup(30000, "surf_normal")
    paper_rend = average_lookup(30000, "rend_normal")
    if paper_surf is not None and paper_rend is not None:
        if paper_surf <= paper_rend:
            lowest_candidate = ("surf_normal", paper_surf)
        else:
            lowest_candidate = ("rend_normal", paper_rend)
    elif paper_surf is not None:
        lowest_candidate = ("surf_normal", paper_surf)
    elif paper_rend is not None:
        lowest_candidate = ("rend_normal", paper_rend)
    else:
        lowest_candidate = (None, None)

    lines = [
        "# Normal MAE Protocol Report",
        "",
        "## Executive summary",
        "",
        f"- Paper Ref-GS ShinyB target used for comparison: {PAPER_NORMAL_MAE_DEG:.2f} deg.",
        f"- Previous reproduced Ref-NeRF/Shiny normal MAE: {old_avg:.6f} deg." if old_avg is not None else "- Previous reproduced normal MAE: unavailable.",
        f"- Lowest 30000-step protocol candidate in this report: {lowest_candidate[0]} = {lowest_candidate[1]:.6f} deg." if lowest_candidate[1] is not None else "- Lowest 30000-step protocol candidate: unavailable.",
        "- Final rows keep `absolute_dot=false`; absolute-dot and convention-sweep rows are diagnostic only.",
        "- The public protocol still does not identify the exact normal key/convention, so final status remains `protocol_uncertain` unless separately confirmed.",
        "",
        "## Final protocol",
        "",
        "| Field | Value |",
        "|---|---|",
        "| normal_key | surf_normal and rend_normal reported separately |",
        "| mask_policy | source_rgba_alpha preferred; gt_normal_alpha/source alpha fallback; gt_normal_nonzero only last fallback |",
        f"| normal_space | {chosen_space} ({space_choice.get('reason')}) |",
        "| iteration | 30000 for paper candidate; 31000 for current reproduction checkpoint |",
        "| absolute_dot | false |",
        "| flip_preset | none |",
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
            "## Surf normal vs rend normal",
            "",
            "| Iteration | surf_normal avg | rend_normal avg | rend - surf |",
            "|---:|---:|---:|---:|",
        ]
    )
    for iteration in (30000, 31000):
        surf = average_lookup(iteration, "surf_normal")
        rend = average_lookup(iteration, "rend_normal")
        delta = None if surf is None or rend is None else rend - surf
        lines.append(f"| {iteration} | {fmt(surf)} | {fmt(rend)} | {fmt(delta)} |")
    lines.extend(
        [
            "",
            "## 30000 vs 31000",
            "",
            "| Normal key | iter30000 avg | iter31000 avg | iter31000 - iter30000 |",
            "|---|---:|---:|---:|",
        ]
    )
    for normal_key in ("surf_normal", "rend_normal"):
        v30000 = average_lookup(30000, normal_key)
        v31000 = average_lookup(31000, normal_key)
        delta = None if v30000 is None or v31000 is None else v31000 - v30000
        lines.append(f"| {normal_key} | {fmt(v30000)} | {fmt(v31000)} | {fmt(delta)} |")
    lines.extend(
        [
            "",
            "## Mask policy ablation",
            "",
            "Diagnostic grid rows are sampled by default; they are used for protocol evidence, not as the final full-pixel result.",
            "",
            "| Iteration | Normal key | Mask policy | Space | Avg MAE deg | Valid ratio | Notes |",
            "|---:|---|---|---|---:|---:|---|",
        ]
    )
    mask_rows = []
    for mask_policy in ("source_rgba_alpha", "gt_normal_alpha", "gt_normal_nonzero", "auto"):
        mask_rows.extend(
            grid_average_rows(
                iteration=30000,
                mask_policy=mask_policy,
                normal_space=chosen_space,
            )
        )
    for row in mask_rows:
        lines.append(
            f"| {row.get('iteration')} | {row.get('normal_key')} | {row.get('mask_policy')} | {row.get('normal_space')} | "
            f"{fmt(row.get('normal_mae_deg'))} | {fmt(row.get('valid_pixel_ratio'))} | {row.get('notes', '')} |"
        )
    lines.extend(
        [
            "",
            "## Normal-space and convention ablation",
            "",
            "These rows keep mask_policy=source_rgba_alpha and absolute_dot=false. Flip rows are diagnostic only and are not selected as the final protocol.",
            "",
            "| Iteration | Normal key | Space | Flip | Avg MAE deg | Notes |",
            "|---:|---|---|---|---:|---|",
        ]
    )
    convention_rows = []
    for normal_space in ("as_saved", "camera", "world"):
        convention_rows.extend(
            grid_average_rows(
                iteration=30000,
                mask_policy="source_rgba_alpha",
                normal_space=normal_space,
            )
        )
    for flip_preset in ("flip_y", "flip_z", "flip_yz"):
        convention_rows.extend(
            grid_average_rows(
                iteration=30000,
                mask_policy="source_rgba_alpha",
                normal_space=chosen_space,
                flip_preset=flip_preset,
            )
        )
    for row in convention_rows:
        lines.append(
            f"| {row.get('iteration')} | {row.get('normal_key')} | {row.get('normal_space')} | {row.get('flip_preset')} | "
            f"{fmt(row.get('normal_mae_deg'))} | {row.get('notes', '')} |"
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
            "## Evidence files",
            "",
            "- `normal_mae_protocol_grid.csv` contains sampled surf_normal/rend_normal, 30000/31000, mask-policy, space, flip, and absolute-dot diagnostics.",
            "- `gt_normal_space_inference.csv` is evidence for GT space/convention only; lowest rows are not automatically selected.",
            "- `final_normal_mae.csv` is the selected protocol table. Rows marked `sampled` must not be presented as full-pixel results.",
            "- Reaching the paper value requires both a public protocol match and a comparable MAE near 2.21 deg.",
            "",
            "## Paper-level conclusion",
            "",
            "This run must not be described as `已复现论文 normal MAE` while the normal key and GT convention remain uncertain or the average remains far from 2.21 deg.",
            "",
            "Remaining causes, in priority order:",
            "",
            "1. Training geometry quality of the available reproduction checkpoint is still worse than the paper target.",
            "2. The paper protocol does not publicly identify whether `surf_normal` or `rend_normal` is the reported key.",
            "3. GT normal coordinate convention remains uncertain because space hypotheses are not clearly separable.",
            "4. Mask details are now alpha-based and traceable, but the exact paper mask policy is still not public.",
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
    parser.add_argument("--max-frames", type=int, default=0, help="Debug only; <=0 evaluates all frames.")
    parser.add_argument("--max-pixels-per-frame", type=int, default=0, help="Debug only; <=0 evaluates all pixels.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    grid_rows = read_csv(args.grid)
    space_rows = read_csv(args.space_inference)
    with args.diagnosis.open(encoding="utf-8") as handle:
        diagnosis = json.load(handle)
    space_choice = choose_normal_space(space_rows)
    final_rows = select_exact_rows(
        grid_rows,
        str(space_choice["normal_space"]),
        args.data_root,
        args.output_root,
        max_frames=args.max_frames,
        max_pixels_per_frame=args.max_pixels_per_frame,
    )
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
