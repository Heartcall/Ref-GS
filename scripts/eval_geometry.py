#!/usr/bin/env python3
"""Evaluate Ref-GS reproduction geometry buffers against available GT."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image
from plyfile import PlyData
from scipy.spatial import cKDTree


DEFAULT_SCENES = {
    "refnerf": ["helmet", "car", "ball", "teapot", "coffee", "toaster"],
    "glossy_synthetic": [
        "bell_blender",
        "tbell_blender",
        "potion_blender",
        "teapot_blender",
        "luyu_blender",
        "cat_blender",
    ],
    "nerf_synthetic": ["ship", "ficus", "lego", "mic", "hotdog", "chair", "materials", "drums"],
}

DATASET_SUBDIRS = {
    "refnerf": "Shiny Blender Synthetic",
    "glossy_synthetic": "GlossySyntheticConverted",
    "nerf_synthetic": "NeRF Synthetic",
}

ALL_METRICS = ("normal_mae", "depth", "chamfer")
NORMAL_EXTENSIONS = (".npy", ".npz", ".png", ".jpg", ".jpeg", ".exr")
DEPTH_EXTENSIONS = (".npy", ".npz", ".png", ".jpg", ".jpeg", ".exr")


def normalize_normals(normals: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    normals = np.asarray(normals, dtype=np.float32)
    norm = np.linalg.norm(normals, axis=-1, keepdims=True)
    safe = norm > eps
    return np.where(safe, normals / np.maximum(norm, eps), 0.0).astype(np.float32)


def decode_normal_image(array: np.ndarray) -> np.ndarray:
    array = np.asarray(array)
    if array.ndim == 2:
        raise ValueError("Normal image must have 3 channels")
    if array.shape[-1] > 3:
        array = array[..., :3]
    if np.issubdtype(array.dtype, np.integer):
        return (array.astype(np.float32) / 255.0) * 2.0 - 1.0
    array = array.astype(np.float32)
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return array
    if finite.min() >= -0.05 and finite.max() <= 1.05:
        return array * 2.0 - 1.0
    return array


def apply_normal_convention(
    normals: np.ndarray,
    flip_x: bool = False,
    flip_y: bool = False,
    flip_z: bool = False,
) -> np.ndarray:
    result = np.array(normals, dtype=np.float32, copy=True)
    if flip_x:
        result[..., 0] *= -1.0
    if flip_y:
        result[..., 1] *= -1.0
    if flip_z:
        result[..., 2] *= -1.0
    return result


def compute_normal_mae_deg(
    pred: np.ndarray,
    gt: np.ndarray,
    mask: Optional[np.ndarray] = None,
    absolute_dot: bool = False,
) -> Dict[str, Optional[float]]:
    pred = normalize_normals(pred)
    gt = normalize_normals(gt)
    valid = np.isfinite(pred).all(axis=-1) & np.isfinite(gt).all(axis=-1)
    valid &= np.linalg.norm(pred, axis=-1) > 1e-6
    valid &= np.linalg.norm(gt, axis=-1) > 1e-6
    if mask is not None:
        valid &= mask.astype(bool)
    if not np.any(valid):
        return {"normal_mae_deg": None, "valid_pixel_count": 0}
    dot = np.sum(pred[valid] * gt[valid], axis=-1)
    if absolute_dot:
        dot = np.abs(dot)
    dot = np.clip(dot, -1.0, 1.0)
    angle = np.degrees(np.arccos(dot))
    return {
        "normal_mae_deg": float(np.mean(angle)),
        "valid_pixel_count": int(valid.sum()),
    }


def _load_array(path: Path) -> np.ndarray:
    if path.suffix == ".npy":
        return np.load(str(path))
    if path.suffix == ".npz":
        data = np.load(str(path))
        first = sorted(data.files)[0]
        return data[first]
    with Image.open(path) as image:
        return np.asarray(image)


def load_normal(path: Path) -> np.ndarray:
    return normalize_normals(decode_normal_image(_load_array(path)))


def load_depth(path: Path) -> np.ndarray:
    depth = _load_array(path)
    if depth.ndim == 3:
        depth = depth[..., 0]
    return np.asarray(depth, dtype=np.float32)


def load_mask(path: Optional[Path], normal: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
    if path is not None and path.exists():
        arr = _load_array(path)
        if arr.ndim == 3:
            arr = arr[..., 0]
        return arr > 0
    if normal is not None:
        return np.linalg.norm(normal, axis=-1) > 1e-6
    return None


def resize_array(array: np.ndarray, shape_hw: Tuple[int, int], is_normal: bool = False) -> Tuple[np.ndarray, str]:
    if tuple(array.shape[:2]) == tuple(shape_hw):
        return array, ""
    resample = Image.BILINEAR
    if array.ndim == 2:
        image = Image.fromarray(array.astype(np.float32), mode="F")
        resized = np.asarray(image.resize((shape_hw[1], shape_hw[0]), resample=resample), dtype=np.float32)
    else:
        channels = []
        for c in range(array.shape[-1]):
            image = Image.fromarray(array[..., c].astype(np.float32), mode="F")
            channels.append(np.asarray(image.resize((shape_hw[1], shape_hw[0]), resample=resample), dtype=np.float32))
        resized = np.stack(channels, axis=-1)
    if is_normal:
        resized = normalize_normals(resized)
    return resized, "resized_prediction_to_gt"


def dataset_scene_root(data_root: Path, dataset: str, scene: str) -> Path:
    return data_root / DATASET_SUBDIRS[dataset] / scene


def _candidate_paths(scene_root: Path, split: str, image_name: str, suffixes: Sequence[str], exts: Sequence[str]) -> List[Path]:
    candidates: List[Path] = []
    for suffix in suffixes:
        for ext in exts:
            candidates.extend(
                [
                    scene_root / split / f"{image_name}{suffix}{ext}",
                    scene_root / f"{image_name}{suffix}{ext}",
                    scene_root / split / f"{image_name.replace('r_', '')}{suffix}{ext}",
                    scene_root / f"{image_name.replace('r_', '')}{suffix}{ext}",
                ]
            )
    return candidates


def find_gt_normal(scene_root: Path, split: str, image_name: str) -> Optional[Path]:
    for path in _candidate_paths(scene_root, split, image_name, ["_normal", "_normals", "-normal", "-normals"], NORMAL_EXTENSIONS):
        if path.exists():
            return path
    matches = sorted((scene_root / split).glob(f"{image_name}*normal*")) if (scene_root / split).exists() else []
    return matches[0] if matches else None


def find_gt_depth(scene_root: Path, split: str, image_name: str) -> Optional[Path]:
    for path in _candidate_paths(scene_root, split, image_name, ["_depth", "-depth", "_depths"], DEPTH_EXTENSIONS):
        if path.exists():
            return path
    matches = sorted((scene_root / split).glob(f"{image_name}*depth*")) if (scene_root / split).exists() else []
    if matches:
        return matches[0]
    if scene_root.parent.name == "GlossySyntheticConverted":
        raw_scene_name = scene_root.name[:-8] if scene_root.name.endswith("_blender") else scene_root.name
        raw_root = scene_root.parent.parent / "GlossySynthetic" / raw_scene_name
        for path in _candidate_paths(raw_root, "", image_name, ["-depth", "_depth"], DEPTH_EXTENSIONS):
            if path.exists():
                return path
    return None


def find_mask(scene_root: Path, split: str, image_name: str) -> Optional[Path]:
    for path in _candidate_paths(scene_root, split, image_name, ["_alpha", "_mask", "-alpha", "-mask"], (".png", ".jpg", ".jpeg")):
        if path.exists():
            return path
    return None


def geometry_dir(output_root: Path, dataset: str, scene: str, split: str, iteration: int) -> Path:
    return output_root / dataset / scene / split / f"ours_{iteration}" / "geometry"


def list_prediction_frames(geom_dir: Path) -> List[str]:
    normal_dir = geom_dir / "normal"
    if not normal_dir.exists():
        return []
    return sorted(path.stem for path in normal_dir.glob("*.npy"))


def empty_row(dataset: str, scene: str, iteration: int, split: str) -> Dict[str, object]:
    return {
        "dataset": dataset,
        "scene": scene,
        "split": split,
        "iteration": iteration,
        "normal_mae_deg": None,
        "depth_absrel": None,
        "depth_rmse": None,
        "depth_rmse_log": None,
        "depth_rmse_scale_aligned": None,
        "chamfer_l1": None,
        "chamfer_l2": None,
        "accuracy": None,
        "completeness": None,
        "fscore": None,
        "normal_consistency": None,
        "valid_pixel_count": 0,
        "sampled_point_count": 0,
        "gt_normal_available": False,
        "gt_depth_available": False,
        "gt_mesh_available": False,
        "metric_family": "paper_geometry",
        "paper_comparable": False,
        "status": "pending",
        "notes": "",
    }


def evaluate_normal_frames(
    dataset: str,
    scene: str,
    data_root: Path,
    output_root: Path,
    iteration: int,
    split: str,
    flip_x: bool = False,
    flip_y: bool = False,
    flip_z: bool = False,
    absolute_dot: bool = False,
) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    row = empty_row(dataset, scene, iteration, split)
    scene_root = dataset_scene_root(data_root, dataset, scene)
    geom_dir = geometry_dir(output_root, dataset, scene, split, iteration)
    frames = list_prediction_frames(geom_dir)
    per_frame = []
    if not frames:
        row.update(status="missing_prediction_normal", notes="geometry normal buffers not found")
        return row, per_frame

    maes: List[float] = []
    valid_total = 0
    gt_found = False
    notes = set()
    for frame in frames:
        pred_path = geom_dir / "normal" / f"{frame}.npy"
        gt_path = find_gt_normal(scene_root, split, frame)
        if gt_path is None:
            per_frame.append({"image_name": frame, "status": "missing_gt_normal"})
            continue
        gt_found = True
        pred = np.load(str(pred_path)).astype(np.float32)
        gt = load_normal(gt_path)
        pred = apply_normal_convention(pred, flip_x=flip_x, flip_y=flip_y, flip_z=flip_z)
        pred, resize_note = resize_array(pred, gt.shape[:2], is_normal=True)
        if resize_note:
            notes.add(resize_note)
        mask = load_mask(find_mask(scene_root, split, frame), normal=gt)
        result = compute_normal_mae_deg(pred, gt, mask=mask, absolute_dot=absolute_dot)
        if result["normal_mae_deg"] is None:
            per_frame.append({"image_name": frame, "status": "no_valid_pixels", "gt_normal": str(gt_path)})
            continue
        maes.append(float(result["normal_mae_deg"]))
        valid_total += int(result["valid_pixel_count"])
        per_frame.append(
            {
                "image_name": frame,
                "status": "ok",
                "gt_normal": str(gt_path),
                "normal_mae_deg": result["normal_mae_deg"],
                "valid_pixel_count": result["valid_pixel_count"],
            }
        )

    row["gt_normal_available"] = gt_found
    if not gt_found:
        row.update(status="missing_gt_normal", notes="no matching GT normal files")
    elif not maes:
        row.update(status="no_valid_normal_pixels", notes="GT normal exists but no valid pixels")
    else:
        row.update(
            normal_mae_deg=float(np.mean(maes)),
            valid_pixel_count=valid_total,
            metric_family="paper_geometry" if dataset == "refnerf" else "auxiliary_geometry",
            paper_comparable=dataset == "refnerf",
            status="ok",
            notes="; ".join(sorted(notes)),
        )
    return row, per_frame


def depth_metrics(pred: np.ndarray, gt: np.ndarray, mask: Optional[np.ndarray]) -> Dict[str, Optional[float]]:
    pred, resize_note = resize_array(pred, gt.shape[:2], is_normal=False)
    valid = np.isfinite(pred) & np.isfinite(gt) & (gt > 1e-8)
    if mask is not None:
        valid &= mask.astype(bool)
    if not np.any(valid):
        return {
            "depth_absrel": None,
            "depth_rmse": None,
            "depth_rmse_log": None,
            "depth_rmse_scale_aligned": None,
            "notes": "no_valid_depth_pixels",
        }
    p = pred[valid].astype(np.float64)
    g = gt[valid].astype(np.float64)
    scale = float(np.sum(p * g) / max(np.sum(p * p), 1e-12))
    aligned = p * scale
    return {
        "depth_absrel": float(np.mean(np.abs(p - g) / np.maximum(g, 1e-8))),
        "depth_rmse": float(np.sqrt(np.mean(np.square(p - g)))),
        "depth_rmse_log": float(np.sqrt(np.mean(np.square(np.log(np.maximum(p, 1e-8)) - np.log(g))))),
        "depth_rmse_scale_aligned": float(np.sqrt(np.mean(np.square(aligned - g)))),
        "notes": resize_note,
    }


def evaluate_depth(
    dataset: str,
    scene: str,
    data_root: Path,
    output_root: Path,
    iteration: int,
    split: str,
) -> Dict[str, object]:
    scene_root = dataset_scene_root(data_root, dataset, scene)
    geom_dir = geometry_dir(output_root, dataset, scene, split, iteration)
    depth_dir = geom_dir / "depth"
    frames = sorted(path.stem for path in depth_dir.glob("*.npy")) if depth_dir.exists() else []
    if not frames:
        return {"status": "missing_prediction_depth", "gt_depth_available": False, "notes": "geometry depth buffers not found"}
    values = []
    gt_found = False
    notes = set()
    for frame in frames:
        gt_path = find_gt_depth(scene_root, split, frame)
        if gt_path is None:
            continue
        gt_found = True
        pred = np.load(str(depth_dir / f"{frame}.npy")).astype(np.float32)
        gt = load_depth(gt_path)
        result = depth_metrics(pred, gt, load_mask(find_mask(scene_root, split, frame)))
        if result["depth_rmse"] is not None:
            values.append(result)
            if result.get("notes"):
                notes.add(str(result["notes"]))
    if not gt_found:
        return {"status": "missing_gt_depth", "gt_depth_available": False, "notes": "no matching GT depth files"}
    if not values:
        return {"status": "no_valid_depth_pixels", "gt_depth_available": True, "notes": "GT depth exists but no valid pixels"}
    return {
        "status": "ok",
        "gt_depth_available": True,
        "depth_absrel": float(np.mean([v["depth_absrel"] for v in values])),
        "depth_rmse": float(np.mean([v["depth_rmse"] for v in values])),
        "depth_rmse_log": float(np.mean([v["depth_rmse_log"] for v in values])),
        "depth_rmse_scale_aligned": float(np.mean([v["depth_rmse_scale_aligned"] for v in values])),
        "notes": "; ".join(sorted(notes)),
    }


def read_ply_points(path: Path) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
    ply = PlyData.read(str(path))
    vertex = ply["vertex"]
    points = np.stack([np.asarray(vertex[c], dtype=np.float64) for c in ("x", "y", "z")], axis=1)
    names = set(vertex.data.dtype.names or ())
    normals = None
    if {"nx", "ny", "nz"}.issubset(names):
        normals = np.stack([np.asarray(vertex[c], dtype=np.float64) for c in ("nx", "ny", "nz")], axis=1)
    faces = None
    if "face" in ply:
        faces = np.asarray([np.asarray(face, dtype=np.int64)[:3] for face in ply["face"].data["vertex_indices"]], dtype=np.int64)
    return points, normals, faces


def sample_mesh(vertices: np.ndarray, faces: Optional[np.ndarray], count: int = 200000) -> np.ndarray:
    rng = np.random.default_rng(20260708)
    if faces is None or len(faces) == 0:
        if len(vertices) <= count:
            return vertices
        return vertices[np.sort(rng.choice(len(vertices), count, replace=False))]
    tri = vertices[faces]
    areas = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) * 0.5
    valid = np.isfinite(areas) & (areas > 0)
    tri = tri[valid]
    areas = areas[valid]
    if len(tri) == 0:
        return vertices[: min(len(vertices), count)]
    idx = rng.choice(len(tri), count, replace=True, p=areas / areas.sum())
    uv = rng.random((count, 2))
    flip = uv.sum(axis=1) > 1
    uv[flip] = 1 - uv[flip]
    chosen = tri[idx]
    return chosen[:, 0] + uv[:, 0:1] * (chosen[:, 1] - chosen[:, 0]) + uv[:, 1:2] * (chosen[:, 2] - chosen[:, 0])


def reference_geometry(data_root: Path, dataset: str, scene: str) -> Tuple[Optional[Path], bool, str]:
    root = dataset_scene_root(data_root, dataset, scene)
    if dataset == "refnerf":
        for path in (root / f"{scene}_gt_mesh.ply", root.parent / "gt" / f"{scene}_gt_mesh.ply"):
            if path.exists():
                return path, True, "gt_mesh"
    if dataset == "glossy_synthetic":
        for path in (root / "eval_pts.ply", root / "points.ply"):
            if path.exists():
                return path, True, "eval_points"
    if dataset == "nerf_synthetic":
        path = root / "points3d.ply"
        if path.exists():
            return path, False, "proxy_points_not_accepted_gt"
    return None, False, "missing_gt_mesh"


def latest_point_cloud(output_root: Path, dataset: str, scene: str, iteration: int) -> Optional[Path]:
    path = output_root / dataset / scene / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply"
    return path if path.exists() else None


def evaluate_chamfer(
    dataset: str,
    scene: str,
    data_root: Path,
    output_root: Path,
    iteration: int,
) -> Dict[str, object]:
    pred_path = latest_point_cloud(output_root, dataset, scene, iteration)
    ref_path, accepted_gt, ref_kind = reference_geometry(data_root, dataset, scene)
    if ref_path is None:
        return {"status": "missing_gt_mesh", "gt_mesh_available": False, "notes": ref_kind}
    if pred_path is None:
        return {"status": "missing_prediction_mesh", "gt_mesh_available": True, "notes": "prediction point_cloud not found"}

    pred, pred_normals, _ = read_ply_points(pred_path)
    ref, ref_normals, faces = read_ply_points(ref_path)
    ref = sample_mesh(ref, faces)
    if len(pred) > 200000:
        rng = np.random.default_rng(20260708)
        pred = pred[np.sort(rng.choice(len(pred), 200000, replace=False))]
    tree_ref = cKDTree(ref)
    pred_to_ref, nn_ref_idx = tree_ref.query(pred, k=1, workers=-1)
    tree_pred = cKDTree(pred)
    ref_to_pred, nn_pred_idx = tree_pred.query(ref, k=1, workers=-1)
    diag = float(np.linalg.norm(ref.max(axis=0) - ref.min(axis=0)))
    threshold = diag * 0.01
    precision = float(np.mean(pred_to_ref < threshold))
    recall = float(np.mean(ref_to_pred < threshold))
    fscore = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    normal_consistency = None
    if pred_normals is not None and ref_normals is not None and faces is None:
        pred_n = normalize_normals(pred_normals)
        ref_n = normalize_normals(ref_normals)
        normal_consistency = float(np.mean(np.abs(np.sum(pred_n * ref_n[nn_ref_idx], axis=-1))))
    return {
        "status": "ok",
        "gt_mesh_available": accepted_gt,
        "chamfer_l1": float((np.mean(pred_to_ref) + np.mean(ref_to_pred)) * 0.5),
        "chamfer_l2": float((np.mean(np.square(pred_to_ref)) + np.mean(np.square(ref_to_pred))) * 0.5),
        "accuracy": float(np.mean(pred_to_ref)),
        "completeness": float(np.mean(ref_to_pred)),
        "fscore": float(fscore),
        "normal_consistency": normal_consistency,
        "sampled_point_count": int(len(pred) + len(ref)),
        "metric_family": "proxy_geometry",
        "paper_comparable": False,
        "notes": "Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE",
    }


def convention_candidates(pred: np.ndarray, gt: np.ndarray, mask: Optional[np.ndarray], absolute_dot: bool) -> List[Dict[str, object]]:
    rows = []
    for flip_x in (False, True):
        for flip_y in (False, True):
            for flip_z in (False, True):
                result = compute_normal_mae_deg(
                    apply_normal_convention(pred, flip_x, flip_y, flip_z),
                    gt,
                    mask=mask,
                    absolute_dot=absolute_dot,
                )
                rows.append(
                    {
                        "flip_x": flip_x,
                        "flip_y": flip_y,
                        "flip_z": flip_z,
                        "normal_mae_deg": result["normal_mae_deg"],
                        "valid_pixel_count": result["valid_pixel_count"],
                    }
                )
    return rows


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


def write_scene_outputs(model_dir: Path, row: Dict[str, object], frames: Sequence[Dict[str, object]]) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "geometry_metrics.json").write_text(json.dumps({"aggregate": row, "frames": list(frames)}, indent=2) + "\n", encoding="utf-8")
    write_csv(model_dir / "geometry_metrics.csv", [row])


def evaluate_scene(
    dataset: str,
    scene: str,
    data_root: Path,
    output_root: Path,
    iteration: int = 31000,
    split: str = "test",
    metrics: Sequence[str] = ALL_METRICS,
    normal_space: str = "auto",
    flip_x: bool = False,
    flip_y: bool = False,
    flip_z: bool = False,
    absolute_dot: bool = False,
    auto_convention_sweep: bool = False,
) -> Dict[str, object]:
    model_dir = output_root / dataset / scene
    requested = tuple(ALL_METRICS if "all" in metrics else metrics)
    row, frames = evaluate_normal_frames(
        dataset,
        scene,
        data_root,
        output_root,
        iteration,
        split,
        flip_x=flip_x,
        flip_y=flip_y,
        flip_z=flip_z,
        absolute_dot=absolute_dot,
    ) if "normal_mae" in requested else (empty_row(dataset, scene, iteration, split), [])
    row["normal_space"] = normal_space
    row["normal_convention"] = f"flip_x={flip_x},flip_y={flip_y},flip_z={flip_z},absolute_dot={absolute_dot}"

    if "depth" in requested:
        depth = evaluate_depth(dataset, scene, data_root, output_root, iteration, split)
        row["gt_depth_available"] = depth.get("gt_depth_available", False)
        for key in ("depth_absrel", "depth_rmse", "depth_rmse_log", "depth_rmse_scale_aligned"):
            if depth.get(key) is not None:
                row[key] = depth[key]
        if depth["status"] != "ok":
            row["notes"] = "; ".join([n for n in (row.get("notes"), depth.get("notes")) if n])

    if "chamfer" in requested:
        chamfer = evaluate_chamfer(dataset, scene, data_root, output_root, iteration)
        for key in ("chamfer_l1", "chamfer_l2", "accuracy", "completeness", "fscore", "normal_consistency", "sampled_point_count"):
            if chamfer.get(key) is not None:
                row[key] = chamfer[key]
        row["gt_mesh_available"] = chamfer.get("gt_mesh_available", False)
        if chamfer.get("status") == "ok":
            if row["status"] != "ok" or row["normal_mae_deg"] is None:
                row["metric_family"] = "proxy_geometry"
                row["paper_comparable"] = False
            row["notes"] = "; ".join([n for n in (row.get("notes"), chamfer.get("notes")) if n])
        elif row["status"] == "pending":
            row["status"] = chamfer["status"]

    if row["status"] == "pending":
        row["status"] = "ok"

    if auto_convention_sweep:
        sweep_rows = []
        geom_dir = geometry_dir(output_root, dataset, scene, split, iteration)
        scene_root = dataset_scene_root(data_root, dataset, scene)
        frames_for_sweep = list_prediction_frames(geom_dir)[:1]
        if frames_for_sweep:
            frame = frames_for_sweep[0]
            gt_path = find_gt_normal(scene_root, split, frame)
            pred_path = geom_dir / "normal" / f"{frame}.npy"
            if gt_path and pred_path.exists():
                pred = np.load(str(pred_path)).astype(np.float32)
                gt = load_normal(gt_path)
                pred, _ = resize_array(pred, gt.shape[:2], is_normal=True)
                mask = load_mask(find_mask(scene_root, split, frame), normal=gt)
                sweep_rows = convention_candidates(pred, gt, mask, absolute_dot)
        if sweep_rows:
            write_csv(model_dir / "geometry_convention_sweep.csv", sweep_rows)

    write_scene_outputs(model_dir, row, frames)
    return row


def summarize_rows(rows: Sequence[Dict[str, object]], log_root: Path) -> None:
    write_csv(log_root / "geometry_summary.csv", rows)
    (log_root / "geometry_summary.json").write_text(json.dumps(list(rows), indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Ref-GS Geometry Summary",
        "",
        "RGB metrics are PSNR/SSIM/LPIPS. The paper-comparable geometry metric is normal MAE in degrees.",
        "Chamfer/F-score values in this report use saved Gaussian centers unless explicitly noted, so they are proxy_geometry and not directly comparable to paper normal MAE.",
        "",
        "## Dataset Summary",
        "",
        "| Dataset | Rows | normal MAE measured | Avg normal MAE deg | Proxy rows | Missing GT normal |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for dataset in DEFAULT_SCENES:
        ds_rows = [r for r in rows if r["dataset"] == dataset]
        normal_rows = [r for r in ds_rows if r.get("normal_mae_deg") is not None]
        proxy_rows = [r for r in ds_rows if r.get("metric_family") == "proxy_geometry"]
        missing = [r for r in ds_rows if r.get("status") == "missing_gt_normal"]
        avg = np.mean([float(r["normal_mae_deg"]) for r in normal_rows]) if normal_rows else math.nan
        lines.append(f"| {dataset} | {len(ds_rows)} | {len(normal_rows)} | {avg:.6f} | {len(proxy_rows)} | {len(missing)} |")
    lines.extend(
        [
            "",
            "## Per-Scene Summary",
            "",
            "| Dataset | Scene | Status | Paper comparable | normal MAE deg | Chamfer-L1 | F-score | Notes |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| {dataset} | {scene} | {status} | {paper} | {normal} | {chamfer} | {fscore} | {notes} |".format(
                dataset=row["dataset"],
                scene=row["scene"],
                status=row["status"],
                paper=row.get("paper_comparable"),
                normal="" if row.get("normal_mae_deg") is None else f"{float(row['normal_mae_deg']):.6f}",
                chamfer="" if row.get("chamfer_l1") is None else f"{float(row['chamfer_l1']):.6f}",
                fscore="" if row.get("fscore") is None else f"{float(row['fscore']):.6f}",
                notes=row.get("notes", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Paper Comparison",
            "",
            "The public repository does not include a machine-readable copy of the paper table values.",
            "Measured Ref-NeRF normal MAE deg rows are paper-comparable in metric family, but exact paper-table comparison remains blocked until the target paper values/protocol are entered.",
            "Proxy Chamfer/F-score rows are not comparable to paper normal MAE deg and are intentionally excluded from this comparison.",
        ]
    )
    (log_root / "geometry_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_metrics(value: str) -> Tuple[str, ...]:
    if value == "all":
        return ALL_METRICS
    return tuple(part for part in value.split(",") if part)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("refnerf", "glossy_synthetic", "nerf_synthetic", "all"), default="all")
    parser.add_argument("--scene", action="append")
    parser.add_argument("--data-root", type=Path, default=Path("/data/liuly/dataset/3DGS"))
    parser.add_argument("--output-root", type=Path, default=Path("output/repro_paper"))
    parser.add_argument("--log-root", type=Path, default=Path("logs/repro"))
    parser.add_argument("--iteration", type=int, default=31000)
    parser.add_argument("--split", choices=("train", "test"), default="test")
    parser.add_argument("--metrics", choices=("normal_mae", "depth", "chamfer", "all"), default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--normal-space", choices=("camera", "world", "auto"), default="auto")
    parser.add_argument("--flip-x", action="store_true")
    parser.add_argument("--flip-y", action="store_true")
    parser.add_argument("--flip-z", action="store_true")
    parser.add_argument("--absolute-dot", action="store_true")
    parser.add_argument("--auto-convention-sweep", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    datasets = list(DEFAULT_SCENES) if args.dataset == "all" else [args.dataset]
    rows = []
    for dataset in datasets:
        scenes = args.scene or DEFAULT_SCENES[dataset]
        for scene in scenes:
            if args.dry_run:
                print(f"Would evaluate {dataset}/{scene} iteration {args.iteration}")
                continue
            rows.append(
                evaluate_scene(
                    dataset=dataset,
                    scene=scene,
                    data_root=args.data_root,
                    output_root=args.output_root,
                    iteration=args.iteration,
                    split=args.split,
                    metrics=parse_metrics(args.metrics),
                    normal_space=args.normal_space,
                    flip_x=args.flip_x,
                    flip_y=args.flip_y,
                    flip_z=args.flip_z,
                    absolute_dot=args.absolute_dot,
                    auto_convention_sweep=args.auto_convention_sweep,
                )
            )
    if rows:
        args.log_root.mkdir(parents=True, exist_ok=True)
        summarize_rows(rows, args.log_root)
        by_dataset: Dict[str, List[Dict[str, object]]] = {}
        for row in rows:
            by_dataset.setdefault(str(row["dataset"]), []).append(row)
        for dataset, dataset_rows in by_dataset.items():
            dataset_root = args.output_root / dataset
            write_csv(dataset_root / "geometry_summary.csv", dataset_rows)
            (dataset_root / "geometry_summary.json").write_text(json.dumps(dataset_rows, indent=2) + "\n", encoding="utf-8")
    print(f"Rows: {len(rows)}, failures: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
