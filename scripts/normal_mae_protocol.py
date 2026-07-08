#!/usr/bin/env python3
"""Normal-MAE protocol helpers shared by evaluation and diagnostics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np
from PIL import Image


ArrayLike = Union[np.ndarray, object]


def _load_array(path: Path) -> np.ndarray:
    path = Path(path)
    if path.suffix == ".npy":
        return np.load(str(path))
    if path.suffix == ".npz":
        data = np.load(str(path))
        return data[sorted(data.files)[0]]
    with Image.open(path) as image:
        return np.asarray(image)


def decode_normal_rgb(arr: ArrayLike) -> np.ndarray:
    """Decode RGB normal arrays into [-1, 1] without normalizing length."""
    array = np.asarray(arr)
    if array.ndim == 2 or array.shape[-1] < 3:
        raise ValueError("Normal image must have at least 3 channels")
    array = array[..., :3]
    if np.issubdtype(array.dtype, np.integer):
        return (array.astype(np.float32) / 255.0) * 2.0 - 1.0
    array = array.astype(np.float32, copy=False)
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return array.astype(np.float32, copy=False)
    if float(finite.min()) >= -0.05 and float(finite.max()) <= 1.05:
        return array * 2.0 - 1.0
    return array


def normalize_normals(arr: ArrayLike, eps: float = 1e-6) -> np.ndarray:
    normals = np.asarray(arr, dtype=np.float32)
    norm = np.linalg.norm(normals, axis=-1, keepdims=True)
    valid = norm > eps
    return np.where(valid, normals / np.maximum(norm, eps), 0.0).astype(np.float32)


def load_normal(path: Path) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """Load a normal image/buffer and return `(normal, alpha_mask_or_None)`."""
    raw = _load_array(Path(path))
    alpha = None
    if raw.ndim == 3 and raw.shape[-1] >= 4:
        alpha = raw[..., 3]
        alpha = np.asarray(alpha > (0.5 if np.issubdtype(alpha.dtype, np.floating) else 0))
    return normalize_normals(decode_normal_rgb(raw)), alpha


def load_gt_normal_alpha(path: Path) -> Optional[np.ndarray]:
    raw = _load_array(Path(path))
    if raw.ndim == 3 and raw.shape[-1] >= 4:
        alpha = raw[..., 3]
        return np.asarray(alpha > (0.5 if np.issubdtype(alpha.dtype, np.floating) else 0))
    return None


def _as_bool_mask(mask: Optional[ArrayLike], shape_hw: Optional[Tuple[int, int]] = None) -> Optional[np.ndarray]:
    if mask is None:
        return None
    arr = np.asarray(mask)
    if arr.ndim == 3:
        arr = arr[..., 0]
    result = arr > (0.5 if np.issubdtype(arr.dtype, np.floating) else 0)
    if shape_hw is not None and tuple(result.shape[:2]) != tuple(shape_hw):
        raise ValueError(f"Mask shape {result.shape[:2]} does not match expected {shape_hw}")
    return np.asarray(result, dtype=bool)


def _candidate_image_paths(scene_dir: Path, frame: Union[str, Dict[str, object]]) -> Tuple[Path, ...]:
    if isinstance(frame, dict):
        file_path = str(frame.get("file_path", ""))
    else:
        file_path = str(frame)
    path = Path(file_path)
    stem = file_path if path.suffix == "" else file_path[: -len(path.suffix)]
    names = [stem]
    if "/" not in stem:
        names.append(f"test/{stem}")
    candidates = []
    for name in names:
        for ext in (".png", ".jpg", ".jpeg"):
            candidates.append(scene_dir / f"{name}{ext}")
    return tuple(candidates)


def load_rgba_alpha_from_source_image(frame: Union[str, Dict[str, object]], scene_dir: Path) -> Optional[np.ndarray]:
    scene_dir = Path(scene_dir)
    for image_path in _candidate_image_paths(scene_dir, frame):
        if not image_path.exists():
            continue
        with Image.open(image_path) as image:
            if image.mode in ("RGBA", "LA") or len(image.getbands()) >= 4:
                return np.asarray(image)[..., 3] > 0
        alpha_path = image_path.with_name(f"{image_path.stem}_alpha{image_path.suffix}")
        if alpha_path.exists():
            with Image.open(alpha_path) as alpha_image:
                arr = np.asarray(alpha_image)
                if arr.ndim == 3:
                    arr = arr[..., 0]
                return arr > 0
    return None


def build_eval_mask(
    mask_policy: str,
    explicit_mask: Optional[ArrayLike] = None,
    source_rgba_alpha: Optional[ArrayLike] = None,
    gt_normal_alpha: Optional[ArrayLike] = None,
    gt_normal: Optional[ArrayLike] = None,
    shape_hw: Optional[Tuple[int, int]] = None,
) -> Optional[np.ndarray]:
    explicit = _as_bool_mask(explicit_mask, shape_hw)
    source = _as_bool_mask(source_rgba_alpha, shape_hw)
    gt_alpha = _as_bool_mask(gt_normal_alpha, shape_hw)
    gt_nonzero = None
    if gt_normal is not None:
        gt_nonzero = np.linalg.norm(np.asarray(gt_normal, dtype=np.float32), axis=-1) > 1e-6
        if shape_hw is not None and tuple(gt_nonzero.shape[:2]) != tuple(shape_hw):
            raise ValueError(f"GT normal shape {gt_nonzero.shape[:2]} does not match expected {shape_hw}")

    if mask_policy == "explicit_mask":
        return explicit
    if mask_policy == "source_rgba_alpha":
        return source
    if mask_policy == "gt_normal_alpha":
        return gt_alpha
    if mask_policy == "gt_normal_nonzero":
        return gt_nonzero
    if mask_policy == "union_alpha":
        masks = [m for m in (explicit, source, gt_alpha) if m is not None]
        return np.logical_or.reduce(masks) if masks else gt_nonzero
    if mask_policy == "intersection_alpha":
        masks = [m for m in (explicit, source, gt_alpha) if m is not None]
        return np.logical_and.reduce(masks) if masks else gt_nonzero
    if mask_policy == "auto":
        for mask in (explicit, source, gt_alpha, gt_nonzero):
            if mask is not None:
                return mask
        return None
    raise ValueError(f"Unknown mask_policy: {mask_policy}")


def compute_normal_mae_deg(
    pred: ArrayLike,
    gt: ArrayLike,
    mask: Optional[ArrayLike] = None,
    absolute_dot: bool = False,
) -> Dict[str, Optional[float]]:
    pred_n = normalize_normals(pred)
    gt_n = normalize_normals(gt)
    valid = np.isfinite(pred_n).all(axis=-1) & np.isfinite(gt_n).all(axis=-1)
    valid &= np.linalg.norm(pred_n, axis=-1) > 1e-6
    valid &= np.linalg.norm(gt_n, axis=-1) > 1e-6
    if mask is not None:
        valid &= np.asarray(mask, dtype=bool)
    if not np.any(valid):
        return {"normal_mae_deg": None, "valid_pixel_count": 0}
    dot = np.sum(pred_n[valid] * gt_n[valid], axis=-1)
    if absolute_dot:
        dot = np.abs(dot)
    angle = np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))
    return {"normal_mae_deg": float(np.mean(angle)), "valid_pixel_count": int(valid.sum())}


def apply_axis_flip(normal: ArrayLike, flip_x: bool, flip_y: bool, flip_z: bool) -> np.ndarray:
    result = np.array(normal, dtype=np.float32, copy=True)
    if flip_x:
        result[..., 0] *= -1.0
    if flip_y:
        result[..., 1] *= -1.0
    if flip_z:
        result[..., 2] *= -1.0
    return result


def transform_normals(normal: ArrayLike, R: ArrayLike, direction: str) -> np.ndarray:
    """Transform normals using this repo's CameraInfo R convention.

    CameraInfo stores `R = w2c[:3, :3].T`, so row-vector normals use:
    world_to_camera: n @ R
    camera_to_world: n @ R.T
    """
    normals = np.asarray(normal, dtype=np.float32)
    rot = np.asarray(R, dtype=np.float32)
    if direction == "identity":
        return normals.astype(np.float32, copy=True)
    if direction == "world_to_camera":
        return normalize_normals(np.einsum("...j,jk->...k", normals, rot))
    if direction == "camera_to_world":
        return normalize_normals(np.einsum("...j,kj->...k", normals, rot))
    raise ValueError(f"Unknown normal transform direction: {direction}")


def load_transforms_frames(scene_dir: Path, split: str = "test") -> Dict[str, Dict[str, object]]:
    path = Path(scene_dir) / f"transforms_{split}.json"
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    frames = {}
    for frame in data.get("frames", []):
        image_name = Path(str(frame.get("file_path", ""))).stem
        c2w = np.asarray(frame["transform_matrix"], dtype=np.float32)
        c2w = c2w.copy()
        c2w[:3, 1:3] *= -1
        w2c = np.linalg.inv(c2w)
        frames[image_name] = {
            "image_name": image_name,
            "frame": frame,
            "R": w2c[:3, :3].T.astype(np.float32),
            "T": w2c[:3, 3].astype(np.float32),
        }
    return frames
