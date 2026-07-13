#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from plyfile import PlyData

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scene.colmap_loader import (
    qvec2rotmat,
    read_extrinsics_binary,
    read_extrinsics_text,
    read_intrinsics_binary,
)
from scripts.refgs_llff_common import (
    EXPECTED_TEST_COUNTS,
    LLFF_SCENES,
    RESOLUTIONS,
    file_sha256,
    list_source_image_names,
    select_llff_views,
    validate_manifest_payload,
    write_json,
)


DEFAULT_DATA_ROOT = Path("/data1/liuly/FSGS_LLFF/dataset/nerf_llff_data")
DEFAULT_AUTHOR_ROOT = Path("/data1/liuly/FSGS_LLFF/author_preprocessed")
DEFAULT_PREPARED_ROOT = Path("/data1/liuly/RefGS_LLFF/prepared")
DEFAULT_LOG_ROOT = Path(__file__).resolve().parents[1] / "logs" / "refgs_llff"


def _author_scene(author_root, scene):
    candidates = (Path(author_root) / "nerf_llff_data" / scene, Path(author_root) / scene)
    return next((path for path in candidates if path.is_dir()), candidates[0])


def _camera_center(record):
    rotation = qvec2rotmat(record.qvec)
    return -(rotation.T @ np.asarray(record.tvec))


def _pose_error(author, original):
    delta = qvec2rotmat(author.qvec) - qvec2rotmat(original.qvec)
    return {
        "image_name": author.name,
        "rotation_frobenius": float(np.linalg.norm(delta)),
        "rotation_max_abs": float(np.max(np.abs(delta))),
        "camera_center_l2": float(np.linalg.norm(_camera_center(author) - _camera_center(original))),
    }


def _audit_ply(path):
    try:
        vertex = PlyData.read(str(path))["vertex"]
    except Exception as exc:
        raise RuntimeError("blocked_pointcloud: cannot read author fused.ply: {}".format(exc))
    required = ("x", "y", "z", "nx", "ny", "nz", "red", "green", "blue")
    names = tuple(vertex.data.dtype.names or ())
    if any(name not in names for name in required):
        raise RuntimeError("blocked_pointcloud: fused.ply lacks required properties")
    xyz = np.column_stack([vertex[name] for name in ("x", "y", "z")]).astype(np.float64)
    if not len(xyz) or not np.isfinite(xyz).all():
        raise RuntimeError("blocked_pointcloud: fused.ply has no finite vertices")
    return {
        "source_kind": "author_fused_ply",
        "path": str(Path(path).resolve()),
        "sha256": file_sha256(path),
        "vertex_count": int(len(xyz)),
        "bbox_min": xyz.min(axis=0).tolist(),
        "bbox_max": xyz.max(axis=0).tolist(),
        "properties": list(names),
    }


def _resolution_mapping(extrinsics, resolution_dir):
    records = sorted(extrinsics.values(), key=lambda record: record.id)
    paths = sorted(
        path for path in Path(resolution_dir).iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if len(records) != len(paths):
        raise RuntimeError("blocked_data: COLMAP/image count mismatch")
    return {record.name: path for record, path in zip(records, paths)}


def _intrinsic_audit(camera, actual_size):
    if camera.model != "SIMPLE_RADIAL" or len(camera.params) != 4:
        raise RuntimeError("blocked_data: expected one SIMPLE_RADIAL LLFF camera")
    width, height = actual_size
    focal, cx, cy, radial = [float(value) for value in camera.params]
    sx = float(width) / float(camera.width)
    sy = float(height) / float(camera.height)
    return {
        "original": {
            "camera_id": camera.id, "model": camera.model,
            "width": camera.width, "height": camera.height,
            "fx": focal, "fy": focal, "cx": cx, "cy": cy, "radial": radial,
        },
        "scaled": {
            "camera_id": camera.id, "model": camera.model,
            "width": width, "height": height,
            "fx": focal * sx, "fy": focal * sy,
            "cx": cx * sx, "cy": cy * sy, "radial": radial,
            "scale_x": sx, "scale_y": sy,
        },
    }


def _record_payload(record, image_name, image_path, intrinsics, provenance):
    rotation = qvec2rotmat(record.qvec)
    return {
        "image_name": Path(image_name).stem,
        "source_image_name": image_name,
        "image_path": str(Path(image_path).resolve()),
        "pose_provenance": provenance,
        "qvec": np.asarray(record.qvec).tolist(),
        "tvec": np.asarray(record.tvec).tolist(),
        "rotation_w2c": rotation.tolist(),
        "camera_center": _camera_center(record).tolist(),
        "intrinsics": intrinsics,
    }


def _source_payload(scene, resolution, data_root=DEFAULT_DATA_ROOT, author_root=DEFAULT_AUTHOR_ROOT):
    if scene not in LLFF_SCENES or resolution not in RESOLUTIONS:
        raise ValueError("unsupported LLFF scene or resolution")
    source = Path(data_root) / scene
    author = _author_scene(author_root, scene) / "3_views"
    fused = author / "dense" / "fused.ply"
    author_images = author / "triangulated" / "images.txt"
    if not fused.is_file():
        raise RuntimeError("blocked_pointcloud: author fused.ply is missing")
    if not author_images.is_file():
        raise RuntimeError("blocked_data: author images.txt is missing")
    split = select_llff_views(list_source_image_names(source))
    original_extrinsics = read_extrinsics_binary(str(source / "sparse" / "0" / "images.bin"))
    original_by_name = {record.name: record for record in original_extrinsics.values()}
    author_extrinsics = read_extrinsics_text(str(author_images))
    author_by_name = {record.name: record for record in author_extrinsics.values()}
    if sorted(author_by_name) != sorted(split["train"]):
        raise RuntimeError("blocked_data: author images.txt does not match selected training images")
    missing = [name for name in split["train"] + split["test"] if name not in original_by_name]
    if missing:
        raise RuntimeError("blocked_data: images missing from original COLMAP model: {}".format(missing))
    cameras = read_intrinsics_binary(str(source / "sparse" / "0" / "cameras.bin"))
    if len(cameras) != 1:
        raise RuntimeError("blocked_data: expected exactly one LLFF camera")
    mapping = _resolution_mapping(original_extrinsics, source / RESOLUTIONS[resolution])
    with Image.open(str(mapping[split["train"][0]])) as image:
        actual_size = image.size
    intrinsics = _intrinsic_audit(next(iter(cameras.values())), actual_size)
    pose_audit = [_pose_error(author_by_name[name], original_by_name[name]) for name in split["train"]]
    if any(item["rotation_max_abs"] > 1e-9 or item["camera_center_l2"] > 1e-9 for item in pose_audit):
        raise RuntimeError("blocked_data: author and original training poses differ")
    centers = np.column_stack([_camera_center(author_by_name[name]) for name in split["train"]])
    center = centers.mean(axis=1)
    radius = float(np.max(np.linalg.norm(centers - center[:, None], axis=0)) * 1.1)
    audit = {
        "schema_version": 1,
        "experiment": "Ref-GS under the FSGS LLFF 3-view protocol",
        "scene": scene,
        "resolution": resolution,
        "resolution_directory": RESOLUTIONS[resolution],
        "train_images": split["train"],
        "test_images": split["test"],
        "candidate_train_count": len(split["candidate_train"]),
        "train_test_overlap": sorted(set(split["train"]) & set(split["test"])),
        "training_pose_audit": pose_audit,
        "intrinsics": intrinsics,
        "normalization": {"translate": (-center).tolist(), "radius": radius, "source": "three_training_cameras_only"},
        "pointcloud": _audit_ply(fused),
        "author_images_txt": str(author_images.resolve()),
        "original_cameras_bin": str((source / "sparse" / "0" / "cameras.bin").resolve()),
        "original_images_bin": str((source / "sparse" / "0" / "images.bin").resolve()),
        "full_scene_pointcloud_used": False,
    }
    train_records = [
        _record_payload(author_by_name[name], name, mapping[name], intrinsics["scaled"], "author_3_views_images_txt")
        for name in split["train"]
    ]
    test_records = [
        _record_payload(original_by_name[name], name, mapping[name], intrinsics["scaled"], "original_llff_images_bin_test_only")
        for name in split["test"]
    ]
    return audit, train_records, test_records


def audit_source_scene(scene, resolution, data_root=DEFAULT_DATA_ROOT, author_root=DEFAULT_AUTHOR_ROOT):
    audit, _, _ = _source_payload(scene, resolution, data_root, author_root)
    return audit


def _ensure_symlink(source, destination):
    source = Path(source).resolve()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() and destination.resolve() == source:
        return
    if destination.exists() or destination.is_symlink():
        raise RuntimeError("blocked_data: prepared path conflicts with approved source: {}".format(destination))
    os.symlink(str(source), str(destination))


def prepare_scene(scene, resolution, data_root=DEFAULT_DATA_ROOT, author_root=DEFAULT_AUTHOR_ROOT,
                  prepared_path=None, audit_path=None):
    audit, train_records, test_records = _source_payload(scene, resolution, data_root, author_root)
    prepared = Path(prepared_path or (DEFAULT_PREPARED_ROOT / resolution / scene))
    prepared.mkdir(parents=True, exist_ok=True)
    for record in train_records + test_records:
        link = prepared / "images" / (record["image_name"] + ".png")
        _ensure_symlink(record["image_path"], link)
        record["prepared_image_path"] = str(link.resolve(strict=False))
    expected_links = {record["image_name"] + ".png" for record in train_records + test_records}
    actual_links = {path.name for path in (prepared / "images").iterdir()}
    if actual_links != expected_links:
        raise RuntimeError("blocked_data: prepared images contain unlisted files")
    ply_link = prepared / "input" / "fused.ply"
    _ensure_symlink(audit["pointcloud"]["path"], ply_link)
    manifest = {
        "schema_version": 1,
        "experiment": audit["experiment"],
        "scene": scene,
        "resolution": resolution,
        "train": train_records,
        "test": test_records,
        "normalization": audit["normalization"],
        "pointcloud": dict(audit["pointcloud"], prepared_path=str(ply_link)),
        "full_scene_pointcloud_used": False,
    }
    validate_manifest_payload(manifest, scene, resolution)
    write_json(prepared / "refgs_llff_manifest.json", manifest)
    if audit_path is not None:
        write_json(audit_path, audit)
    return audit


def build_parser():
    parser = argparse.ArgumentParser(description="Prepare Ref-GS for the FSGS LLFF three-view protocol")
    parser.add_argument("--scene", required=True, choices=LLFF_SCENES)
    parser.add_argument("--resolution", required=True, choices=tuple(RESOLUTIONS))
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--author-preprocessed-root", type=Path, default=DEFAULT_AUTHOR_ROOT)
    parser.add_argument("--prepared-root", type=Path, default=DEFAULT_PREPARED_ROOT)
    parser.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    prepared = args.prepared_root / args.resolution / args.scene
    audit_path = args.log_root / args.resolution / args.scene / "data_audit.json"
    try:
        audit = prepare_scene(args.scene, args.resolution, args.data_root,
                              args.author_preprocessed_root, prepared, audit_path)
    except (OSError, ValueError, RuntimeError) as exc:
        status = "blocked_pointcloud" if "blocked_pointcloud" in str(exc) else "blocked_data"
        write_json(args.log_root / args.resolution / args.scene / "status.json", {
            "scene": args.scene, "resolution": args.resolution,
            "status": status, "failure_reason": str(exc),
        })
        print(str(exc), file=sys.stderr)
        return 2
    cell_log = args.log_root / args.resolution / args.scene
    for stage in ("train", "render", "eval"):
        (cell_log / stage).mkdir(parents=True, exist_ok=True)
    status_path = cell_log / "status.json"
    previous = json.loads(status_path.read_text(encoding="utf-8")) if status_path.is_file() else {}
    if previous.get("status") != "completed":
        write_json(status_path, {
            "scene": args.scene, "resolution": args.resolution,
            "status": "pending", "train_images": audit["train_images"],
            "test_images": audit["test_images"], "pointcloud": audit["pointcloud"],
            "checkpoint_exists": False, "render_exists": False,
            "metrics_exists": False, "metrics": None,
        })
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
