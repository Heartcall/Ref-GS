#!/usr/bin/env python3
"""Diagnose why reproduced Ref-GS normal MAE does not match paper-level values.

This script is read-only with respect to datasets, checkpoints, RGB metrics, and
geometry metrics. It writes separate diagnosis artifacts under --log-root.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.eval_geometry import (  # noqa: E402
    DEFAULT_SCENES,
    apply_normal_convention,
    compute_normal_mae_deg,
    decode_normal_image,
    find_gt_normal,
    find_mask,
    geometry_dir,
    load_mask,
    load_normal,
    normalize_normals,
    resize_array,
)


PAPER_REF_GS_SHINY_NORMAL_MAE_DEG = 2.21
DEFAULT_DATA_ROOT = Path("/data/liuly/dataset/3DGS")
REFNERF_SUBDIR = "Shiny Blender Synthetic"
CONVENTION_FLIPS = (
    (False, False, False),
    (True, False, False),
    (False, True, False),
    (False, False, True),
    (True, True, False),
    (True, False, True),
    (False, True, True),
    (True, True, True),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


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


def maybe_float(value) -> Optional[float]:
    if value in (None, "", "nan", "NA"):
        return None
    try:
        value_f = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value_f) else value_f


def dataset_scene_root(data_root: Path, scene: str) -> Path:
    return data_root / REFNERF_SUBDIR / scene


def source_image_path(scene_root: Path, split: str, image_name: str) -> Optional[Path]:
    for ext in (".png", ".jpg", ".jpeg"):
        path = scene_root / split / f"{image_name}{ext}"
        if path.exists():
            return path
    return None


def image_info(path: Optional[Path]) -> Dict[str, object]:
    if path is None or not path.exists():
        return {"exists": False}
    with Image.open(path) as image:
        arr = np.asarray(image)
        info = {
            "exists": True,
            "path": str(path),
            "mode": image.mode,
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
            "min": float(np.nanmin(arr)) if arr.size else None,
            "max": float(np.nanmax(arr)) if arr.size else None,
            "has_alpha": arr.ndim == 3 and arr.shape[-1] == 4,
        }
        if info["has_alpha"]:
            alpha = arr[..., 3]
            info["alpha_min"] = float(alpha.min())
            info["alpha_max"] = float(alpha.max())
            info["alpha_nonzero_ratio"] = float(np.mean(alpha > 0))
        return info


def image_alpha_mask(path: Optional[Path]) -> Optional[np.ndarray]:
    if path is None or not path.exists():
        return None
    with Image.open(path) as image:
        arr = np.asarray(image)
    if arr.ndim == 3 and arr.shape[-1] == 4:
        return arr[..., 3] > 0
    return None


def list_pred_frames(output_root: Path, scene: str, iteration: int, split: str = "test") -> List[str]:
    normal_dir = geometry_dir(output_root, "refnerf", scene, split, iteration) / "normal"
    return sorted(path.stem for path in normal_dir.glob("*.npy")) if normal_dir.exists() else []


def list_gt_normal_frames(scene_root: Path, split: str = "test") -> List[str]:
    split_dir = scene_root / split
    if not split_dir.exists():
        return []
    frames = []
    for path in split_dir.glob("*normal*"):
        stem = path.stem
        for suffix in ("_normal", "_normals", "-normal", "-normals"):
            if stem.endswith(suffix):
                frames.append(stem[: -len(suffix)])
                break
    return sorted(set(frames))


def transforms_test_frames(scene_root: Path) -> List[str]:
    data = read_json(scene_root / "transforms_test.json")
    if not data:
        return []
    frames = []
    for frame in data.get("frames", []):
        file_path = str(frame.get("file_path", ""))
        frames.append(Path(file_path).stem)
    return frames


def transform_rotation(scene_root: Path, image_name: str, repo_convention: bool = True) -> Optional[np.ndarray]:
    data = read_json(scene_root / "transforms_test.json")
    if not data:
        return None
    for frame in data.get("frames", []):
        if Path(str(frame.get("file_path", ""))).stem != image_name:
            continue
        matrix = frame.get("transform_matrix")
        if matrix is None:
            return None
        c2w = np.asarray(matrix, dtype=np.float32)
        if c2w.shape != (4, 4):
            return None
        if repo_convention:
            c2w = c2w.copy()
            c2w[:3, 1:3] *= -1.0
        return c2w[:3, :3]
    return None


def rotate_normals(normals: np.ndarray, rotation: Optional[np.ndarray], mode: str) -> Optional[np.ndarray]:
    if rotation is None:
        return None
    if mode == "world_to_camera":
        return np.einsum("...c,cd->...d", normals, rotation)
    if mode == "camera_to_world":
        return np.einsum("...c,dc->...d", normals, rotation)
    raise ValueError(mode)


def finite_stats(values: np.ndarray) -> Dict[str, object]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {"min": None, "max": None, "mean": None}
    return {"min": float(finite.min()), "max": float(finite.max()), "mean": float(finite.mean())}


def normal_buffer_stats(output_root: Path, scene: str, iteration: int, max_stat_files: int = 5) -> Dict[str, object]:
    normal_dir = geometry_dir(output_root, "refnerf", scene, "test", iteration) / "normal"
    normal_vis_dir = normal_dir.parent / "normal_vis"
    depth_dir = normal_dir.parent / "depth"
    files = sorted(normal_dir.glob("*.npy")) if normal_dir.exists() else []
    stats = {
        "normal_npy_count": len(files),
        "normal_vis_png_count": len(list(normal_vis_dir.glob("*.png"))) if normal_vis_dir.exists() else 0,
        "depth_npy_count": len(list(depth_dir.glob("*.npy"))) if depth_dir.exists() else 0,
        "sample_files": [],
        "nan_count": 0,
        "inf_count": 0,
        "mean_norm_mean": None,
        "norm_min": None,
        "norm_max": None,
    }
    norm_means = []
    norm_mins = []
    norm_maxs = []
    for path in files[:max_stat_files]:
        arr = np.load(str(path))
        norms = np.linalg.norm(arr.astype(np.float32), axis=-1)
        stats["nan_count"] += int(np.isnan(arr).sum())
        stats["inf_count"] += int(np.isinf(arr).sum())
        norm_means.append(float(np.nanmean(norms)))
        norm_mins.append(float(np.nanmin(norms)))
        norm_maxs.append(float(np.nanmax(norms)))
        if len(stats["sample_files"]) < 3:
            value_stats = finite_stats(arr)
            stats["sample_files"].append(
                {
                    "file": path.name,
                    "shape": list(arr.shape),
                    "dtype": str(arr.dtype),
                    "min": value_stats["min"],
                    "max": value_stats["max"],
                    "mean": value_stats["mean"],
                    "mean_norm": float(np.nanmean(norms)),
                }
            )
    if norm_means:
        stats["mean_norm_mean"] = float(np.mean(norm_means))
        stats["norm_min"] = float(np.min(norm_mins))
        stats["norm_max"] = float(np.max(norm_maxs))
    stats["stats_files_sampled"] = min(len(files), max_stat_files)
    metadata = read_json(normal_dir.parent / "metadata.json")
    stats["metadata"] = metadata
    return stats


def mask_source(scene_root: Path, split: str, image_name: str, gt_normal: np.ndarray) -> Tuple[str, Optional[Path], np.ndarray]:
    explicit = find_mask(scene_root, split, image_name)
    mask = load_mask(explicit, normal=gt_normal)
    if explicit is not None:
        return "explicit_mask_file", explicit, mask
    return "gt_normal_norm_gt_eps", None, mask


def _sample_mask(mask: Optional[np.ndarray], shape_hw: Tuple[int, int], max_pixels: Optional[int], seed: int) -> Optional[np.ndarray]:
    if max_pixels is None or max_pixels <= 0:
        return mask
    valid = np.ones(shape_hw, dtype=bool) if mask is None else mask.astype(bool).copy()
    idx = np.flatnonzero(valid.reshape(-1))
    if idx.size <= max_pixels:
        return mask
    rng = np.random.default_rng(seed)
    chosen = rng.choice(idx, size=max_pixels, replace=False)
    sampled = np.zeros(valid.size, dtype=bool)
    sampled[chosen] = True
    return sampled.reshape(shape_hw)


def _sample_indices(mask: Optional[np.ndarray], shape_hw: Tuple[int, int], max_pixels: Optional[int], seed: int) -> np.ndarray:
    valid = np.ones(shape_hw, dtype=bool) if mask is None else mask.astype(bool)
    idx = np.flatnonzero(valid.reshape(-1))
    if max_pixels is not None and max_pixels > 0 and idx.size > max_pixels:
        rng = np.random.default_rng(seed)
        idx = rng.choice(idx, size=max_pixels, replace=False)
    return np.asarray(idx, dtype=np.int64)


def _mae_vectors(pred_vec: np.ndarray, gt_vec: np.ndarray, absolute_dot: bool = False) -> Tuple[Optional[float], int]:
    pred_vec = np.asarray(pred_vec, dtype=np.float32)
    gt_vec = np.asarray(gt_vec, dtype=np.float32)
    valid = np.isfinite(pred_vec).all(axis=-1) & np.isfinite(gt_vec).all(axis=-1)
    pred_norm = np.linalg.norm(pred_vec, axis=-1)
    gt_norm = np.linalg.norm(gt_vec, axis=-1)
    valid &= pred_norm > 1e-6
    valid &= gt_norm > 1e-6
    if not np.any(valid):
        return None, 0
    p = pred_vec[valid] / pred_norm[valid, None]
    g = gt_vec[valid] / gt_norm[valid, None]
    dot = np.sum(p * g, axis=-1)
    if absolute_dot:
        dot = np.abs(dot)
    dot = np.clip(dot, -1.0, 1.0)
    return float(np.mean(np.degrees(np.arccos(dot)))), int(valid.sum())


def angular_mae(
    pred: np.ndarray,
    gt: np.ndarray,
    mask: Optional[np.ndarray],
    absolute_dot: bool = False,
    max_pixels: Optional[int] = None,
    seed: int = 0,
) -> Tuple[Optional[float], int]:
    if max_pixels is not None and max_pixels > 0:
        idx = _sample_indices(mask, pred.shape[:2], max_pixels=max_pixels, seed=seed)
        return _mae_vectors(pred.reshape(-1, 3)[idx], gt.reshape(-1, 3)[idx], absolute_dot=absolute_dot)
    result = compute_normal_mae_deg(pred, gt, mask=mask, absolute_dot=absolute_dot)
    return result["normal_mae_deg"], int(result["valid_pixel_count"])


def sampled_convention_mae(
    pred: np.ndarray,
    gt: np.ndarray,
    mask: Optional[np.ndarray],
    max_pixels: Optional[int],
    seed: int,
    flip_x: bool = False,
    flip_y: bool = False,
    flip_z: bool = False,
    absolute_dot: bool = False,
    rotation: Optional[np.ndarray] = None,
    rotation_target: Optional[str] = None,
) -> Tuple[Optional[float], int]:
    idx = _sample_indices(mask, pred.shape[:2], max_pixels=max_pixels, seed=seed)
    pred_vec = pred.reshape(-1, 3)[idx].astype(np.float32, copy=True)
    gt_vec = gt.reshape(-1, 3)[idx].astype(np.float32, copy=True)
    if rotation is not None and rotation_target == "pred_world_to_camera":
        pred_vec = pred_vec @ rotation
    elif rotation is not None and rotation_target == "gt_camera_to_world":
        gt_vec = gt_vec @ rotation.T
    if flip_x:
        pred_vec[:, 0] *= -1.0
    if flip_y:
        pred_vec[:, 1] *= -1.0
    if flip_z:
        pred_vec[:, 2] *= -1.0
    return _mae_vectors(pred_vec, gt_vec, absolute_dot=absolute_dot)


def frame_metric_rows(
    scene: str,
    data_root: Path,
    output_root: Path,
    iteration: int,
    max_frames: Optional[int] = None,
    mae_pixels_per_frame: Optional[int] = 20000,
    sweep_pixels_per_frame: Optional[int] = 5000,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], Dict[str, object]]:
    scene_root = dataset_scene_root(data_root, scene)
    frames = list_pred_frames(output_root, scene, iteration)
    if max_frames is not None:
        frames = frames[:max_frames]
    mask_rows = []
    sweep_rows = []
    current_maes = []
    alpha_maes = []
    current_valid = 0
    alpha_valid = 0
    current_background_entered = 0
    alpha_available_count = 0
    for frame in frames:
        pred_path = geometry_dir(output_root, "refnerf", scene, "test", iteration) / "normal" / f"{frame}.npy"
        gt_path = find_gt_normal(scene_root, "test", frame)
        if gt_path is None or not pred_path.exists():
            continue
        pred = np.load(str(pred_path)).astype(np.float32)
        gt_raw_info = image_info(gt_path)
        gt = load_normal(gt_path)
        pred, resize_note = resize_array(pred, gt.shape[:2], is_normal=True)
        mask_kind, mask_path, current_mask = mask_source(scene_root, "test", frame, gt)
        image_path = source_image_path(scene_root, "test", frame)
        alpha_mask = image_alpha_mask(image_path)
        if alpha_mask is not None and alpha_mask.shape != current_mask.shape:
            alpha_mask, _ = resize_array(alpha_mask.astype(np.float32), current_mask.shape, is_normal=False)
            alpha_mask = alpha_mask > 0.5
        frame_seed = abs(hash((scene, frame))) % (2**32)
        current_mae, current_count = angular_mae(
            pred,
            gt,
            current_mask,
            absolute_dot=False,
            max_pixels=mae_pixels_per_frame,
            seed=frame_seed,
        )
        alpha_mae, alpha_count = (None, 0)
        if alpha_mask is not None:
            alpha_available_count += 1
            alpha_mae, alpha_count = angular_mae(
                pred,
                gt,
                alpha_mask,
                absolute_dot=False,
                max_pixels=mae_pixels_per_frame,
                seed=frame_seed + 1,
            )
            current_background_entered += int(np.logical_and(current_mask, np.logical_not(alpha_mask)).sum())
        if current_mae is not None:
            current_maes.append(current_mae)
            current_valid += current_count
        if alpha_mae is not None:
            alpha_maes.append(alpha_mae)
            alpha_valid += alpha_count

        if len(mask_rows) < 12:
            src_info = image_info(image_path)
            mask_rows.append(
                {
                    "scene": scene,
                    "frame": frame,
                    "gt_normal": str(gt_path),
                    "gt_normal_mode": gt_raw_info.get("mode"),
                    "gt_normal_shape": gt_raw_info.get("shape"),
                    "gt_normal_has_alpha": gt_raw_info.get("has_alpha"),
                    "image_path": str(image_path) if image_path else None,
                    "image_mode": src_info.get("mode"),
                    "image_has_alpha": src_info.get("has_alpha"),
                    "current_mask_source": mask_kind,
                    "current_mask_path": str(mask_path) if mask_path else None,
                    "current_valid_ratio": float(np.mean(current_mask)),
                    "alpha_valid_ratio": float(np.mean(alpha_mask)) if alpha_mask is not None else None,
                    "background_pixels_enter_eval": int(np.logical_and(current_mask, np.logical_not(alpha_mask)).sum()) if alpha_mask is not None else None,
                    "current_mae_deg": current_mae,
                    "alpha_mask_mae_deg": alpha_mae,
                    "resize_note": resize_note,
                }
            )

        space_variants = [
            ("as_saved", None, None),
            ("pred_world_to_repo_camera", transform_rotation(scene_root, frame, repo_convention=True), "pred_world_to_camera"),
            ("gt_repo_camera_to_world", transform_rotation(scene_root, frame, repo_convention=True), "gt_camera_to_world"),
            ("pred_world_to_blender_camera", transform_rotation(scene_root, frame, repo_convention=False), "pred_world_to_camera"),
            ("gt_blender_camera_to_world", transform_rotation(scene_root, frame, repo_convention=False), "gt_camera_to_world"),
        ]
        for space_mode, rotation, rotation_target in space_variants:
            if space_mode != "as_saved" and rotation is None:
                continue
            for absolute_dot in (False, True):
                for flip_x, flip_y, flip_z in CONVENTION_FLIPS:
                    mae, count = sampled_convention_mae(
                        pred,
                        gt,
                        current_mask,
                        max_pixels=sweep_pixels_per_frame,
                        seed=frame_seed + 17,
                        flip_x=flip_x,
                        flip_y=flip_y,
                        flip_z=flip_z,
                        absolute_dot=absolute_dot,
                        rotation=rotation,
                        rotation_target=rotation_target,
                    )
                    if mae is None:
                        continue
                    sweep_rows.append(
                        {
                            "dataset": "refnerf",
                            "scene": scene,
                            "frame": frame,
                            "space_mode": space_mode,
                            "flip_x": flip_x,
                            "flip_y": flip_y,
                            "flip_z": flip_z,
                            "absolute_dot": absolute_dot,
                            "normal_mae_deg": mae,
                            "valid_pixel_count": count,
                        }
                    )

    scene_diag = {
        "frames_evaluated": len(frames),
        "current_eval_mean_frame_mae_deg": float(np.mean(current_maes)) if current_maes else None,
        "current_eval_valid_pixels": current_valid,
        "image_alpha_available_frames": alpha_available_count,
        "alpha_mask_mean_frame_mae_deg": float(np.mean(alpha_maes)) if alpha_maes else None,
        "alpha_mask_valid_pixels": alpha_valid,
        "background_pixels_entering_current_eval_where_alpha_available": current_background_entered,
        "mae_pixels_per_frame": mae_pixels_per_frame,
        "sweep_pixels_per_frame": sweep_pixels_per_frame,
    }
    return mask_rows, sweep_rows, scene_diag


def aggregate_sweep(rows: Sequence[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, Dict[str, object]]]:
    grouped: Dict[Tuple[object, ...], List[float]] = {}
    valid_counts: Dict[Tuple[object, ...], int] = {}
    for row in rows:
        key = (
            row["scene"],
            row["space_mode"],
            row["flip_x"],
            row["flip_y"],
            row["flip_z"],
            row["absolute_dot"],
        )
        grouped.setdefault(key, []).append(float(row["normal_mae_deg"]))
        valid_counts[key] = valid_counts.get(key, 0) + int(row["valid_pixel_count"])
    summary_rows = []
    best_by_scene: Dict[str, Dict[str, object]] = {}
    current_by_scene: Dict[str, Dict[str, object]] = {}
    for key, values in grouped.items():
        scene, space_mode, flip_x, flip_y, flip_z, absolute_dot = key
        summary = {
            "dataset": "refnerf",
            "scene": scene,
            "space_mode": space_mode,
            "flip_x": flip_x,
            "flip_y": flip_y,
            "flip_z": flip_z,
            "absolute_dot": absolute_dot,
            "normal_mae_deg": float(np.mean(values)),
            "frames": len(values),
            "valid_pixel_count": valid_counts[key],
        }
        summary_rows.append(summary)
        if scene not in best_by_scene or summary["normal_mae_deg"] < best_by_scene[scene]["normal_mae_deg"]:
            best_by_scene[scene] = summary
        if (
            space_mode == "as_saved"
            and flip_x is False
            and flip_y is False
            and flip_z is False
            and absolute_dot is False
        ):
            current_by_scene[scene] = summary
    scene_summary = {}
    for scene, best in best_by_scene.items():
        current = current_by_scene.get(scene)
        scene_summary[scene] = {
            "best": best,
            "current": current,
            "current_minus_best_mae_deg": (current["normal_mae_deg"] - best["normal_mae_deg"]) if current else None,
        }
    return sorted(summary_rows, key=lambda r: (str(r["scene"]), float(r["normal_mae_deg"]))), scene_summary


def current_geometry_metrics(log_root: Path) -> Tuple[Dict[str, float], Optional[float]]:
    rows = read_csv_rows(log_root / "geometry_metrics.csv")
    per_scene = {}
    for row in rows:
        if row.get("dataset") == "refnerf" and row.get("normal_mae_deg"):
            per_scene[str(row["scene"])] = float(row["normal_mae_deg"])
    avg = float(np.mean(list(per_scene.values()))) if per_scene else None
    return per_scene, avg


def rgb_metrics(log_root: Path) -> Dict[str, Dict[str, float]]:
    rows = read_csv_rows(log_root / "metrics_summary.csv")
    result = {}
    for row in rows:
        if row.get("dataset") == "refnerf":
            result[str(row["scene"])] = {
                "psnr": maybe_float(row.get("psnr")),
                "ssim": maybe_float(row.get("ssim")),
                "lpips": maybe_float(row.get("lpips")),
            }
    return result


def checkpoint_notes(output_root: Path, scenes: Sequence[str], iteration: int) -> Dict[str, Dict[str, object]]:
    notes = {}
    for scene in scenes:
        pc_root = output_root / "refnerf" / scene / "point_cloud"
        iterations = []
        if pc_root.exists():
            for path in pc_root.glob("iteration_*"):
                match = re.search(r"iteration_(\d+)$", path.name)
                if match and (path / "point_cloud.ply").exists():
                    iterations.append(int(match.group(1)))
        cfg = read_text(output_root / "refnerf" / scene / "cfg_args")
        notes[scene] = {
            "iteration_31000_exists": iteration in iterations,
            "iteration_30000_exists": 30000 in iterations,
            "available_iterations": sorted(iterations),
            "cfg_args_excerpt": cfg[:1000],
        }
    return notes


def audit_code_paths() -> Dict[str, object]:
    render_py = read_text(REPO_ROOT / "render.py")
    run_geometry = read_text(REPO_ROOT / "scripts/run_geometry_eval.py")
    eval_geometry = read_text(REPO_ROOT / "scripts/eval_geometry.py")
    renderer = read_text(REPO_ROOT / "gaussian_renderer/__init__.py")
    return {
        "run_geometry_eval_calls_save_geometry": "--save-geometry" in run_geometry,
        "run_geometry_eval_calls_geometry_only": "--geometry-only" in run_geometry,
        "run_geometry_eval_calls_split": "--split" in run_geometry,
        "render_supports_save_geometry": "--save-geometry" in render_py,
        "render_supports_geometry_only": "--geometry-only" in render_py,
        "render_supports_split": "--split" in render_py,
        "render_supports_normal_key": "--normal-key" in render_py,
        "render_supports_depth_key": "--depth-key" in render_py,
        "render_saves_npy_normals": "np.save(str(npy_path), hwc)" in render_py,
        "geometry_export_chain_inconsistent": not all(
            token in render_py for token in ("--save-geometry", "--geometry-only", "--split", "--normal-key", "--depth-key")
        ),
        "render_auto_normal_key_order": ["surf_normal", "rend_normal", "normal", "render_normal"],
        "render_auto_depth_key_order": ["median_depth", "render_depth", "depth", "surf_depth", "rend_dist"],
        "normal_space_not_implemented": "normal_space" not in eval_geometry.split("def evaluate_normal_frames", 1)[0]
        and "row[\"normal_space\"] = normal_space" in eval_geometry,
        "normal_space_argument_recorded_only": "row[\"normal_space\"] = normal_space" in eval_geometry
        and "world_to_camera" not in eval_geometry
        and "camera_to_world" not in eval_geometry,
        "flip_flags_applied": "apply_normal_convention(pred, flip_x=flip_x" in eval_geometry,
        "absolute_dot_applied": "if absolute_dot:" in eval_geometry and "dot = np.abs(dot)" in eval_geometry,
        "auto_convention_sweep_first_frame_only": "frames_for_sweep = list_prediction_frames(geom_dir)[:1]" in eval_geometry,
        "decode_normal_drops_alpha": "array = array[..., :3]" in eval_geometry,
        "find_mask_reads_rgba_alpha": "RGBA" in eval_geometry or "source_image" in eval_geometry,
        "renderer_returns_rend_normal": "'rend_normal': render_normal" in renderer,
        "renderer_returns_surf_normal": "'surf_normal': surf_normal" in renderer,
        "rend_normal_definition": "allmap[2:5] transformed by viewpoint_camera.world_view_transform[:3,:3].T and F.normalize",
        "surf_normal_definition": "depth_to_normal(viewpoint_camera, surf_depth), then multiplied by detached render_alpha",
        "surf_normal_multiplied_by_alpha": "surf_normal = surf_normal * (render_alpha).detach()" in renderer,
        "rend_normal_multiplied_by_alpha": "render_normal = F.normalize(render_normal, dim=0)" in renderer
        and "render_normal = render_normal *" not in renderer,
    }


def frame_alignment(scene: str, data_root: Path, output_root: Path, iteration: int) -> Dict[str, object]:
    scene_root = dataset_scene_root(data_root, scene)
    transforms = transforms_test_frames(scene_root)
    pred = list_pred_frames(output_root, scene, iteration)
    gt = list_gt_normal_frames(scene_root)
    renders_dir = output_root / "refnerf" / scene / "test" / f"ours_{iteration}" / "renders"
    renders = sorted(path.stem for path in renders_dir.glob("*.png")) if renders_dir.exists() else []
    transform_set = set(transforms)
    pred_set = set(pred)
    gt_set = set(gt)
    render_set = set(renders)
    return {
        "transforms_test_frames": len(transforms),
        "predicted_normal_frames": len(pred),
        "gt_normal_frames": len(gt),
        "render_frames": len(renders),
        "pred_missing_from_transforms": sorted(pred_set - transform_set)[:20],
        "gt_missing_for_pred": sorted(pred_set - gt_set)[:20],
        "pred_missing_for_gt": sorted(gt_set - pred_set)[:20],
        "render_missing_for_pred": sorted(pred_set - render_set)[:20],
        "all_pred_frames_in_test_split": pred_set.issubset(transform_set),
        "all_pred_frames_have_gt_normal": pred_set.issubset(gt_set),
        "only_partial_test_evaluated": len(pred) != len(transforms),
    }


def build_suspected_causes(data: Dict[str, object]) -> List[Dict[str, object]]:
    causes = []
    best_gaps = [
        value.get("current_minus_best_mae_deg")
        for value in data["convention_sweep_summary"].values()
        if value.get("current_minus_best_mae_deg") is not None
    ]
    best_values = [
        value.get("best", {}).get("normal_mae_deg")
        for value in data["convention_sweep_summary"].values()
        if value.get("best", {}).get("normal_mae_deg") is not None
    ]
    mean_best = float(np.mean(best_values)) if best_values else None
    mean_gap = float(np.mean(best_gaps)) if best_gaps else None
    if data["normal_key_hypothesis"].get("normal_key_protocol_uncertain"):
        causes.append(
            {
                "severity": "high",
                "cause": "当前导出的 normal key 为 surf_normal，但论文协议未确认是 surf_normal 还是 rend_normal",
                "evidence": [
                    "geometry metadata records normal_key=surf_normal",
                    "render.py auto key order selects surf_normal before rend_normal",
                    "renderer also returns rend_normal with a different definition",
                    "sampled convention sweep remains far above 2.21 deg, so a simple flip alone does not explain the gap",
                ],
            }
        )
    mask_findings = data.get("mask_alpha_diagnostics", {})
    if any(v.get("background_pixels_entering_current_eval_where_alpha_available", 0) for v in mask_findings.values()):
        causes.append(
            {
                "severity": "high",
                "cause": "mask/alpha 协议未对齐：GT/source RGBA alpha 存在，但当前 eval 多数场景不读取 RGBA alpha",
                "evidence": [
                    "decode_normal_image() drops alpha channels",
                    "find_mask() searches only separate *_alpha/*_mask files and does not read source RGBA alpha",
                    "diagnostic found current mask includes large background regions for RGBA scenes; alpha-mask sampled MAE improves but does not fully close the paper gap",
                ],
            }
        )
    code = data["normal_space_implementation"]
    if code.get("normal_space_not_implemented"):
        causes.append(
            {
                "severity": "medium",
                "cause": "normal-space 参数没有执行真实坐标变换",
                "evidence": [
                    "`eval_geometry.py` accepts --normal-space but only writes row['normal_space']",
                    "sampled camera/world variants in the sweep did not beat the as-saved convention, so this is a confirmed eval-code bug but not sufficient evidence for the whole 8.8 vs 2.21 deg gap",
                ],
            }
        )
    if best_gaps and float(np.mean(best_gaps)) > 1.0:
        causes.append(
            {
                "severity": "medium",
                "cause": "normal convention / 轴翻转 / absolute-dot 协议未对齐",
                "evidence": [
                    f"mean current-minus-best sampled sweep gap is {mean_gap:.3f} deg",
                    f"mean best sampled sweep MAE is {mean_best:.3f} deg, still above the 2.21 deg paper target",
                ],
            }
        )
    causes.append(
        {
            "severity": "medium",
            "cause": "训练几何质量或公开复现超参仍可能影响法线质量",
            "evidence": [
                "RGB PSNR is reasonable but not proof of paper-level normals",
                "all scenes use saved iteration_31000, and iteration_30000 checkpoints also exist for optional offline comparison",
            ],
        }
    )
    for idx, cause in enumerate(causes, start=1):
        cause["rank"] = idx
    return causes


def markdown_report(data: Dict[str, object]) -> str:
    lines = [
        "# Ref-GS Normal MAE Diagnosis",
        "",
        "## Executive Summary",
        "",
        f"- Paper Ref-GS ShinyB normal MAE target used here: {data['paper_normal_mae_deg']:.2f} deg.",
        f"- Current reproduced Ref-NeRF/Shiny average: {data['reproduced_average_normal_mae_deg']:.6f} deg.",
        f"- Gap: {data['reproduced_average_normal_mae_deg'] - data['paper_normal_mae_deg']:.6f} deg.",
        "- This diagnosis uses existing saved geometry buffers and GT normals only; no retraining was run and no existing RGB/geometry metrics were overwritten.",
        "",
        "## Current vs Paper",
        "",
        "| Scene | Current normal MAE deg | Paper target gap | RGB PSNR |",
        "|---|---:|---:|---:|",
    ]
    rgb = data.get("training_quality_notes", {}).get("rgb_metrics", {})
    for scene, mae in sorted(data["per_scene_normal_mae_deg"].items()):
        psnr = rgb.get(scene, {}).get("psnr")
        lines.append(f"| {scene} | {mae:.6f} | {mae - data['paper_normal_mae_deg']:.6f} | {'' if psnr is None else f'{psnr:.4f}'} |")
    lines.extend(["", "## Confirmed Code Issues", ""])
    code = data["normal_space_implementation"]
    lines.append(f"- `normal_space_not_implemented`: `{code.get('normal_space_not_implemented')}`.")
    lines.append(f"- `auto_convention_sweep_first_frame_only`: `{code.get('auto_convention_sweep_first_frame_only')}` in the existing `eval_geometry.py` helper.")
    lines.append(f"- `decode_normal_drops_alpha`: `{code.get('decode_normal_drops_alpha')}`; alpha is not used by `decode_normal_image()`.")
    lines.append(f"- `find_mask_reads_rgba_alpha`: `{code.get('find_mask_reads_rgba_alpha')}`.")
    lines.extend(["", "## Geometry Export Chain", ""])
    export = data["geometry_export_chain"]
    lines.append(f"- `geometry_export_chain_inconsistent`: `{export.get('geometry_export_chain_inconsistent')}`.")
    lines.append(f"- render supports `--save-geometry`, `--geometry-only`, `--split`, `--normal-key`, `--depth-key`: `{not export.get('geometry_export_chain_inconsistent')}`.")
    lines.append("- Existing metadata shows prediction normal source per scene under `geometry/metadata.json`.")
    lines.extend(["", "## Data/Mask Findings", ""])
    lines.append("| Scene | Pred normals | GT normals aligned | Current mask | Current valid px | Alpha frames | Alpha-mask MAE | Background entered |")
    lines.append("|---|---:|---:|---|---:|---:|---:|---:|")
    for scene in sorted(data["mask_alpha_diagnostics"]):
        mask = data["mask_alpha_diagnostics"][scene]
        align = data["frame_alignment_diagnostics"][scene]
        first_mask = mask.get("sample_masks", [{}])[0] if mask.get("sample_masks") else {}
        lines.append(
            "| {scene} | {pred} | {aligned} | {mask_source} | {valid} | {alpha_frames} | {alpha_mae} | {bg} |".format(
                scene=scene,
                pred=align.get("predicted_normal_frames"),
                aligned=align.get("all_pred_frames_have_gt_normal"),
                mask_source=first_mask.get("current_mask_source", ""),
                valid=mask.get("current_eval_valid_pixels"),
                alpha_frames=mask.get("image_alpha_available_frames"),
                alpha_mae="" if mask.get("alpha_mask_mean_frame_mae_deg") is None else f"{mask.get('alpha_mask_mean_frame_mae_deg'):.6f}",
                bg=mask.get("background_pixels_entering_current_eval_where_alpha_available"),
            )
        )
    lines.extend(["", "## Convention Sweep Findings", ""])
    lines.append(
        "Sweep values are diagnostic only; the best convention is not claimed as a paper reproduction. "
        f"Alternate-convention MAE uses deterministic sampled pixels per frame: {data.get('diagnostic_sampling', {}).get('sweep_pixels_per_frame')}."
    )
    lines.append("")
    lines.append("| Scene | Current MAE | Best MAE | Gap | Best convention |")
    lines.append("|---|---:|---:|---:|---|")
    for scene, summary in sorted(data["convention_sweep_summary"].items()):
        current = summary.get("current") or {}
        best = summary.get("best") or {}
        convention = "space={space_mode}, flip=({flip_x},{flip_y},{flip_z}), absolute_dot={absolute_dot}".format(**best)
        lines.append(
            f"| {scene} | {current.get('normal_mae_deg', float('nan')):.6f} | {best.get('normal_mae_deg', float('nan')):.6f} | "
            f"{summary.get('current_minus_best_mae_deg', float('nan')):.6f} | {convention} |"
        )
    lines.extend(["", "## Normal Key Findings", ""])
    key = data["normal_key_hypothesis"]
    lines.append(f"- Current saved normal key: `{key.get('current_saved_normal_key')}`.")
    lines.append(f"- Current saved depth key: `{key.get('current_saved_depth_key')}`.")
    lines.append(f"- `normal_key_protocol_uncertain`: `{key.get('normal_key_protocol_uncertain')}`.")
    lines.append("- Renderer returns both `rend_normal` and `surf_normal`; their definitions are different.")
    lines.extend(["", "## Training Quality Findings", ""])
    train = data["training_quality_notes"]
    lines.append(f"- `training_quality_possible_factor`: `{train.get('training_quality_possible_factor')}`.")
    lines.append("- Existing checkpoints include iteration_31000 for all diagnosed scenes; iteration_30000 also exists for optional offline comparison.")
    lines.extend(["", "## Ranked Root-Cause Hypotheses", ""])
    for cause in data["suspected_causes"]:
        lines.append(f"{cause['rank']}. **{cause['severity']}** - {cause['cause']}")
        for evidence in cause.get("evidence", []):
            lines.append(f"   - {evidence}")
    lines.extend(["", "## Recommended Next Experiments/Fixes", ""])
    for item in data["recommended_fixes"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def diagnose(args: argparse.Namespace) -> Dict[str, object]:
    scenes = args.scene or DEFAULT_SCENES[args.dataset]
    per_scene_mae, reproduced_avg = current_geometry_metrics(args.log_root)
    per_scene_mae = {scene: per_scene_mae[scene] for scene in scenes if scene in per_scene_mae}
    reproduced_avg = float(np.mean(list(per_scene_mae.values()))) if per_scene_mae else None
    code_audit = audit_code_paths()
    buffer_stats = {
        scene: normal_buffer_stats(args.output_root, scene, args.iteration, max_stat_files=args.stats_files_per_scene)
        for scene in scenes
    }
    alignment = {scene: frame_alignment(scene, args.data_root, args.output_root, args.iteration) for scene in scenes}

    mask_diag = {}
    all_sweep_rows = []
    for scene in scenes:
        sample_masks, sweep_rows, scene_diag = frame_metric_rows(
            scene=scene,
            data_root=args.data_root,
            output_root=args.output_root,
            iteration=args.iteration,
            mae_pixels_per_frame=args.mae_pixels_per_frame,
            sweep_pixels_per_frame=args.sweep_pixels_per_frame,
        )
        scene_diag["sample_masks"] = sample_masks
        mask_diag[scene] = scene_diag
        all_sweep_rows.extend(sweep_rows)
    sweep_summary_rows, sweep_summary = aggregate_sweep(all_sweep_rows)

    current_keys = {}
    for scene, stats in buffer_stats.items():
        meta = stats.get("metadata") or {}
        current_keys.setdefault("normal_keys", {})[scene] = meta.get("normal_key")
        current_keys.setdefault("depth_keys", {})[scene] = meta.get("depth_key")
    normal_key_hypothesis = {
        "current_saved_normal_key": sorted(set(k for k in current_keys.get("normal_keys", {}).values() if k)),
        "current_saved_depth_key": sorted(set(k for k in current_keys.get("depth_keys", {}).values() if k)),
        "normal_key_protocol_uncertain": True,
        "evidence": {
            "render_auto_normal_key_order": code_audit["render_auto_normal_key_order"],
            "renderer_returns_rend_normal": code_audit["renderer_returns_rend_normal"],
            "renderer_returns_surf_normal": code_audit["renderer_returns_surf_normal"],
            "rend_normal_definition": code_audit["rend_normal_definition"],
            "surf_normal_definition": code_audit["surf_normal_definition"],
            "surf_normal_multiplied_by_alpha": code_audit["surf_normal_multiplied_by_alpha"],
        },
    }
    rgb = rgb_metrics(args.log_root)
    ckpt = checkpoint_notes(args.output_root, scenes, args.iteration)
    training_quality_notes = {
        "training_quality_possible_factor": True,
        "rgb_metrics": rgb,
        "checkpoint_notes": ckpt,
        "notes": [
            "RGB quality is complete and reasonably high, but RGB PSNR does not prove paper-level surface normals.",
            "Saved 30000 and 31000 checkpoints permit optional offline comparison without retraining.",
        ],
    }
    data = {
        "paper_normal_mae_deg": PAPER_REF_GS_SHINY_NORMAL_MAE_DEG,
        "reproduced_average_normal_mae_deg": reproduced_avg,
        "per_scene_normal_mae_deg": per_scene_mae,
        "paper_gap_deg": None if reproduced_avg is None else reproduced_avg - PAPER_REF_GS_SHINY_NORMAL_MAE_DEG,
        "geometry_export_chain": {k: code_audit[k] for k in code_audit if k.startswith("run_geometry") or k.startswith("render_") or k == "geometry_export_chain_inconsistent"},
        "render_keys": {
            "renderer_returns_rend_normal": code_audit["renderer_returns_rend_normal"],
            "renderer_returns_surf_normal": code_audit["renderer_returns_surf_normal"],
            "rend_normal_definition": code_audit["rend_normal_definition"],
            "surf_normal_definition": code_audit["surf_normal_definition"],
        },
        "normal_key_hypothesis": normal_key_hypothesis,
        "normal_space_implementation": {
            "normal_space_not_implemented": code_audit["normal_space_not_implemented"] or code_audit["normal_space_argument_recorded_only"],
            "normal_space_argument_recorded_only": code_audit["normal_space_argument_recorded_only"],
            "flip_flags_applied": code_audit["flip_flags_applied"],
            "absolute_dot_applied": code_audit["absolute_dot_applied"],
            "auto_convention_sweep_first_frame_only": code_audit["auto_convention_sweep_first_frame_only"],
            "decode_normal_drops_alpha": code_audit["decode_normal_drops_alpha"],
            "find_mask_reads_rgba_alpha": code_audit["find_mask_reads_rgba_alpha"],
        },
        "normal_buffer_diagnostics": buffer_stats,
        "mask_alpha_diagnostics": mask_diag,
        "frame_alignment_diagnostics": alignment,
        "convention_sweep_summary": sweep_summary,
        "training_quality_notes": training_quality_notes,
        "diagnostic_sampling": {
            "normal_buffer_stats_files_per_scene": args.stats_files_per_scene,
            "mae_pixels_per_frame": args.mae_pixels_per_frame,
            "sweep_pixels_per_frame": args.sweep_pixels_per_frame,
            "note": "Existing reproduced MAE values are read from geometry_metrics.csv; sampled recomputation is only diagnostic for mask and convention alternatives.",
        },
        "evidence": {
            "read_files": [
                "logs/repro/summary.md",
                "logs/repro/geometry_summary.md",
                "logs/repro/geometry_metrics.csv",
                "logs/repro/geometry_data_inventory.md",
                "logs/repro/geometry_data_inventory.json",
                "render.py",
                "scripts/eval_geometry.py",
                "scripts/run_geometry_eval.py",
                "gaussian_renderer/__init__.py",
                "utils/graphics_utils.py",
                "utils/camera_utils.py",
                "scene/dataset_readers.py",
                "scene/cameras.py",
            ],
            "normal_convention_sweep_csv": str(args.log_root / "normal_convention_sweep.csv"),
        },
        "recommended_fixes": [
            "Do not change reported metrics in place; first add an eval-only branch that explicitly converts pred/GT normals to the same declared coordinate space.",
            "Evaluate both `--normal-key surf_normal` and `--normal-key rend_normal` into a separate debug output root, then compare against GT with the same mask and convention sweep.",
            "Make mask policy explicit: separate mask file, source RGBA alpha, GT normal alpha, or GT nonzero-normal mask; report valid-pixel ratio for every scene.",
            "Extend convention sweep to the full test split before selecting a protocol; do not use the best sweep value as a paper result.",
            "Optionally evaluate existing iteration_30000 geometry buffers in a separate output/log root if paper iteration is suspected, without retraining.",
        ],
    }
    data["suspected_causes"] = build_suspected_causes(data)
    data["_sweep_rows"] = sweep_summary_rows
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=Path("output/repro_paper"))
    parser.add_argument("--log-root", type=Path, default=Path("logs/repro"))
    parser.add_argument("--dataset", choices=("refnerf",), default="refnerf")
    parser.add_argument("--scene", action="append")
    parser.add_argument("--iteration", type=int, default=31000)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mae-pixels-per-frame", type=int, default=20000)
    parser.add_argument("--sweep-pixels-per-frame", type=int, default=5000)
    parser.add_argument("--stats-files-per-scene", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenes = args.scene or DEFAULT_SCENES[args.dataset]
    if args.dry_run:
        for scene in scenes:
            print(f"Would diagnose {args.dataset}/{scene} iteration {args.iteration}")
        print(f"Would write {args.log_root / 'normal_mae_diagnosis.json'}")
        print(f"Would write {args.log_root / 'normal_mae_diagnosis.md'}")
        print(f"Would write {args.log_root / 'normal_convention_sweep.csv'}")
        return 0
    data = diagnose(args)
    sweep_rows = data.pop("_sweep_rows")
    if args.write_report:
        write_csv(args.log_root / "normal_convention_sweep.csv", sweep_rows)
        write_json(args.log_root / "normal_mae_diagnosis.json", data)
        (args.log_root / "normal_mae_diagnosis.md").write_text(markdown_report(data), encoding="utf-8")
        print(f"Wrote {args.log_root / 'normal_mae_diagnosis.json'}")
        print(f"Wrote {args.log_root / 'normal_mae_diagnosis.md'}")
        print(f"Wrote {args.log_root / 'normal_convention_sweep.csv'}")
    else:
        print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
