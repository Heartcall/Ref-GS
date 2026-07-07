import argparse
import json
import pickle
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from skimage.io import imread, imsave


def read_pickle(path: Path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def load_split(root: Path) -> Tuple[List[str], List[str]]:
    split_path = root / "synthetic_split_128.pkl"
    if not split_path.exists():
        raise FileNotFoundError(f"Missing split file: {split_path}")
    test_ids, train_ids = read_pickle(split_path)
    return [str(item) for item in train_ids], [str(item) for item in test_ids]


def camera_to_blender_frame(scene_root: Path, image_id: str) -> Tuple[Dict, np.ndarray]:
    camera = read_pickle(scene_root / f"{image_id}-camera.pkl")
    w2c = np.array(camera[0].tolist() + [[0, 0, 0, 1]], dtype=np.float64)
    c2w = np.linalg.inv(w2c)
    c2w[:3, 1:3] *= -1
    frame = {
        "file_path": str(Path("rgb") / image_id),
        "transform_matrix": c2w.tolist(),
    }
    return frame, np.asarray(camera[1])


def write_transforms(scene_root: Path, output_root: Path, train_ids: List[str], test_ids: List[str]) -> None:
    for split, ids in (("train", train_ids), ("test", test_ids)):
        frames = []
        intrinsics = None
        for image_id in ids:
            frame, intrinsics = camera_to_blender_frame(scene_root, image_id)
            frames.append(frame)
        if intrinsics is None:
            raise ValueError(f"No frames found for split {split} in {scene_root}")
        transforms = {
            "w": 800,
            "h": 800,
            "fl_x": float(intrinsics[0, 0]),
            "fl_y": float(intrinsics[1, 1]),
            "cx": 400,
            "cy": 400,
            "frames": frames,
        }
        with (output_root / f"transforms_{split}.json").open("w", encoding="utf-8") as handle:
            json.dump(transforms, handle, indent=2)


def write_rgba_images(scene_root: Path, output_root: Path, image_ids: List[str]) -> None:
    rgb_root = output_root / "rgb"
    rgb_root.mkdir(parents=True, exist_ok=True)
    for image_id in image_ids:
        depth_path = scene_root / f"{image_id}-depth.png"
        image_path = scene_root / f"{image_id}.png"
        if not depth_path.exists() or not image_path.exists():
            raise FileNotFoundError(f"Missing RGB/depth pair for image id {image_id} in {scene_root}")
        depth = imread(depth_path).astype(np.float32) / 65535.0 * 15.0
        alpha = ((depth < 14.5)[..., None] * 255).astype(np.uint8)
        image = imread(image_path)[..., :3]
        imsave(rgb_root / f"{image_id}.png", np.concatenate([image, alpha], axis=-1), check_contrast=False)


def convert_scene(raw_root: Path, scene: str, output_base: Optional[Path] = None, overwrite: bool = False) -> Path:
    scene_root = raw_root / scene
    if not scene_root.exists():
        raise FileNotFoundError(f"Raw Glossy Synthetic scene not found: {scene_root}")
    output_root = (output_base or raw_root) / f"{scene}_blender"
    if output_root.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_root}. Pass --overwrite to replace files in it.")
    output_root.mkdir(parents=True, exist_ok=True)

    train_ids, test_ids = load_split(raw_root)
    all_ids = sorted({*train_ids, *test_ids}, key=lambda item: int(item))
    write_transforms(scene_root, output_root, train_ids, test_ids)
    write_rgba_images(scene_root, output_root, all_ids)

    eval_points = scene_root / "eval_pts.ply"
    if eval_points.exists():
        shutil.copy2(eval_points, output_root / "eval_pts.ply")
        shutil.copy2(eval_points, output_root / "points.ply")
    return output_root


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert NeRO Glossy Synthetic scenes to the Blender JSON/RGBA layout used by Ref-GS."
    )
    parser.add_argument("--path", type=Path, required=True, help="Raw GlossySynthetic root containing scene folders and synthetic_split_128.pkl.")
    parser.add_argument("--scene", required=True, help="Raw scene name, for example bell, tbell, potion, teapot, luyu, or cat.")
    parser.add_argument("--output-root", type=Path, default=None, help="Optional destination root. Defaults to --path.")
    parser.add_argument("--overwrite", action="store_true", help="Allow writing into an existing <scene>_blender directory.")
    args = parser.parse_args()
    output = convert_scene(args.path, args.scene, args.output_root, overwrite=args.overwrite)
    print(f"[INFO] Converted {args.scene} to {output}")


if __name__ == "__main__":
    main()
