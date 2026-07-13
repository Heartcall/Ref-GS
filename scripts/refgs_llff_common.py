#!/usr/bin/env python3
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np


LLFF_SCENES = ("fern", "flower", "fortress", "horns", "leaves", "orchids", "room", "trex")
RESOLUTIONS = {"1_8": "images_8", "1_4": "images_4"}
ALLOWED_STATUSES = {
    "pending", "running", "completed", "failed", "missing",
    "blocked_cuda", "blocked_data", "blocked_pointcloud",
}
EXPECTED_TEST_COUNTS = {
    "fern": 3, "flower": 5, "fortress": 6, "horns": 8,
    "leaves": 4, "orchids": 4, "room": 6, "trex": 7,
}
EXPECTED_IMAGE_SIZES = {"1_8": (504, 378), "1_4": (1008, 756)}


def list_source_image_names(scene_path):
    image_dir = Path(scene_path) / "images"
    return sorted(
        path.name for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )


def select_llff_views(image_names, n_views=3, llffhold=8):
    ordered = sorted(image_names)
    test = [name for index, name in enumerate(ordered) if index % llffhold == 0]
    candidates = [name for index, name in enumerate(ordered) if index % llffhold != 0]
    if len(candidates) < n_views:
        raise ValueError("not enough candidate training images")
    indices = [round(float(value)) for value in np.linspace(0, len(candidates) - 1, n_views)]
    train = [candidates[index] for index in indices]
    if len(set(train)) != n_views:
        raise ValueError("three-view selection did not produce distinct images")
    return {"all": ordered, "candidate_train": candidates, "train": train, "test": test}


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest_payload(payload, expected_scene=None, expected_resolution=None):
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported Ref-GS LLFF manifest schema")
    if payload.get("experiment") != "Ref-GS under the FSGS LLFF 3-view protocol":
        raise ValueError("manifest experiment label mismatch")
    scene, resolution = payload.get("scene"), payload.get("resolution")
    if scene not in LLFF_SCENES or resolution not in RESOLUTIONS:
        raise ValueError("manifest scene/resolution is invalid")
    if expected_scene is not None and scene != expected_scene:
        raise ValueError("manifest scene mismatch")
    if expected_resolution is not None and resolution != expected_resolution:
        raise ValueError("manifest resolution mismatch")
    train, test = payload.get("train"), payload.get("test")
    if not isinstance(train, list) or len(train) != 3:
        raise ValueError("manifest must contain exactly three train records")
    if not isinstance(test, list) or len(test) != EXPECTED_TEST_COUNTS[scene]:
        raise ValueError("manifest test count mismatch")
    train_names = [record.get("source_image_name") for record in train]
    test_names = [record.get("source_image_name") for record in test]
    if None in train_names + test_names or len(set(train_names)) != 3 or len(set(test_names)) != len(test_names):
        raise ValueError("manifest contains missing or duplicate image names")
    if set(train_names) & set(test_names):
        raise ValueError("manifest train/test overlap")
    if any(record.get("pose_provenance") != "author_3_views_images_txt" for record in train):
        raise ValueError("manifest training pose provenance mismatch")
    if any(record.get("pose_provenance") != "original_llff_images_bin_test_only" for record in test):
        raise ValueError("manifest test pose provenance mismatch")
    expected_width, expected_height = EXPECTED_IMAGE_SIZES[resolution]
    for record in train + test:
        intrinsics = record.get("intrinsics", {})
        numeric = [intrinsics.get(key) for key in ("fx", "fy", "cx", "cy", "radial")]
        if (
            intrinsics.get("model") != "SIMPLE_RADIAL"
            or intrinsics.get("width") != expected_width
            or intrinsics.get("height") != expected_height
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in numeric)
            or intrinsics.get("fx", 0) <= 0 or intrinsics.get("fy", 0) <= 0
            or len(record.get("qvec", [])) != 4 or len(record.get("tvec", [])) != 3
            or np.asarray(record.get("rotation_w2c", [])).shape != (3, 3)
            or len(record.get("camera_center", [])) != 3
        ):
            raise ValueError("manifest scaled intrinsics or pose shape is invalid")
    pointcloud = payload.get("pointcloud", {})
    sha256 = pointcloud.get("sha256", "")
    if pointcloud.get("source_kind") != "author_fused_ply" or len(sha256) != 64:
        raise ValueError("manifest point-cloud provenance mismatch")
    if not str(pointcloud.get("path", "")).endswith("3_views/dense/fused.ply"):
        raise ValueError("manifest point-cloud path is not the author three-view fused PLY")
    if payload.get("full_scene_pointcloud_used") is not False:
        raise ValueError("manifest does not prohibit the full-scene point cloud")
    return True


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(str(temporary), str(path))


def finite_metrics(payload):
    if not isinstance(payload, dict):
        return None
    if "aggregate" in payload and isinstance(payload["aggregate"], dict):
        payload = payload["aggregate"]
    elif len(payload) == 1:
        only_key = next(iter(payload))
        if str(only_key).startswith("ours_") and isinstance(payload[only_key], dict):
            payload = payload[only_key]
    aliases = (("PSNR", "psnr"), ("SSIM", "ssim"), ("LPIPS", "lpips"))
    result = {}
    for upper, lower in aliases:
        value = payload.get(upper, payload.get(lower))
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            return None
        result[lower] = float(value)
    return result


def metric_means(rows):
    completed = [row for row in rows if row.get("status") == "completed"]
    if not completed:
        return None
    return {
        metric: sum(float(row[metric]) for row in completed) / len(completed)
        for metric in ("psnr", "ssim", "lpips")
    }


def _nonempty(path):
    path = Path(path)
    return path.is_file() and path.stat().st_size > 0


def stage_state(model_path, iteration, expected_names):
    model_path = Path(model_path)
    saves = [5000, iteration]
    checkpoint_exists = all(_nonempty(
        model_path / "point_cloud" / "iteration_{}".format(save) / "point_cloud.ply"
    ) for save in saves)
    base = model_path / "test" / "ours_{}".format(iteration)
    renders = {path.name for path in (base / "renders").glob("*.png")} if (base / "renders").is_dir() else set()
    gt = {path.name for path in (base / "gt").glob("*.png")} if (base / "gt").is_dir() else set()
    expected = set(expected_names or ())
    render_exists = bool(expected) and renders == expected and gt == expected
    metrics = finite_metrics(read_json(model_path / "results.json", {}))
    return {
        "checkpoint_exists": checkpoint_exists,
        "render_exists": render_exists,
        "metrics_exists": metrics is not None,
        "render_count": len(renders),
        "gt_count": len(gt),
        "metrics": metrics,
    }
