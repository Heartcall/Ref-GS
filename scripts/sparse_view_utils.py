import json
import math
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


SPARSE_DATASETS = ("refnerf", "glossy_synthetic", "nerf_synthetic")
SPARSE_STRATEGIES = ("random", "uniform_index", "uniform_pose", "farthest_pose")


@dataclass(frozen=True)
class SelectionResult:
    indices: List[int]
    frames: List[Dict]
    file_paths: List[str]
    status: str
    notes: str = ""


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def _uniform_positions(total: int, count: int) -> List[int]:
    if total <= 0 or count <= 0:
        return []
    if count >= total:
        return list(range(total))
    if count == 1:
        return [0]
    positions = [int(round(i * (total - 1) / float(count - 1))) for i in range(count)]
    seen = set(positions)
    if len(seen) == count:
        return positions

    # Rounding can collide for small totals. Fill gaps in original order.
    result = []
    for idx in positions:
        if idx not in result:
            result.append(idx)
    for idx in range(total):
        if len(result) == count:
            break
        if idx not in result:
            result.append(idx)
    return sorted(result)


def _camera_center(frame: Dict) -> Optional[Tuple[float, float, float]]:
    matrix = frame.get("transform_matrix")
    if not isinstance(matrix, list) or len(matrix) < 3:
        return None
    try:
        return (float(matrix[0][3]), float(matrix[1][3]), float(matrix[2][3]))
    except (TypeError, ValueError, IndexError):
        return None


def _all_camera_centers(frames: Sequence[Dict]) -> Optional[List[Tuple[float, float, float]]]:
    centers = [_camera_center(frame) for frame in frames]
    if any(center is None for center in centers):
        return None
    return [center for center in centers if center is not None]


def _squared_distance(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _select_indices(frames: Sequence[Dict], count: int, strategy: str, seed: int) -> Tuple[List[int], str]:
    total = len(frames)
    if count >= total:
        return list(range(total)), ""
    if strategy == "random":
        rng = random.Random(seed)
        return sorted(rng.sample(range(total), count)), ""
    if strategy == "uniform_index":
        return _uniform_positions(total, count), ""

    centers = _all_camera_centers(frames)
    if centers is None:
        return _uniform_positions(total, count), "missing transform_matrix; fell back to uniform_index"

    if strategy == "uniform_pose":
        ordered = sorted(range(total), key=lambda idx: math.atan2(centers[idx][0], centers[idx][2]))
        picked_in_pose_order = _uniform_positions(total, count)
        return sorted(ordered[pos] for pos in picked_in_pose_order), ""

    if strategy == "farthest_pose":
        selected = [seed % total]
        remaining = set(range(total))
        remaining.remove(selected[0])
        while len(selected) < count and remaining:
            best_idx = max(
                remaining,
                key=lambda idx: (
                    min(_squared_distance(centers[idx], centers[chosen]) for chosen in selected),
                    -idx,
                ),
            )
            selected.append(best_idx)
            remaining.remove(best_idx)
        return sorted(selected), ""

    raise ValueError(f"Unknown sparse-view strategy: {strategy}")


def select_frames(frames: Sequence[Dict], views: int, strategy: str, seed: int = 0) -> SelectionResult:
    if strategy not in SPARSE_STRATEGIES:
        raise ValueError(f"Unknown sparse-view strategy: {strategy}")
    if views <= 0:
        raise ValueError("--views values must be positive")

    total = len(frames)
    requested = views
    effective_views = min(requested, total)
    indices, notes = _select_indices(frames, effective_views, strategy, seed)
    status = "not_enough_frames" if total < requested else "ok"
    if status == "not_enough_frames":
        notes = "; ".join(part for part in [notes, f"requested {requested} views but only {total} train frames exist"] if part)
    selected = [frames[idx] for idx in indices]
    file_paths = [str(frame.get("file_path", "")) for frame in selected]
    return SelectionResult(indices=indices, frames=selected, file_paths=file_paths, status=status, notes=notes)


def _copy_or_link_child(source: Path, target: Path) -> None:
    if target.exists() or target.is_symlink():
        return
    try:
        target.symlink_to(source)
    except OSError:
        if source.is_dir():
            shutil.copytree(str(source), str(target), symlinks=True)
        else:
            shutil.copy2(str(source), str(target))


def mirror_scene_structure(source_scene: Path, output_scene: Path) -> None:
    output_scene.mkdir(parents=True, exist_ok=True)
    skipped = {"transforms_train.json", "transforms_test.json", "sparse_view_manifest.json"}
    for child in source_scene.iterdir():
        if child.name in skipped:
            continue
        _copy_or_link_child(child, output_scene / child.name)


def generate_sparse_scene(
    dataset: str,
    scene: str,
    source_scene: Path,
    output_scene: Path,
    views: int,
    strategy: str,
    seed: int = 0,
    dry_run: bool = False,
    force: bool = False,
) -> Dict:
    train_path = source_scene / "transforms_train.json"
    test_path = source_scene / "transforms_test.json"
    if not train_path.exists():
        raise FileNotFoundError(f"Missing transforms_train.json: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Missing transforms_test.json: {test_path}")

    train_json = load_json(train_path)
    test_json = load_json(test_path)
    frames = train_json.get("frames", [])
    if not isinstance(frames, list):
        raise ValueError(f"`frames` must be a list in {train_path}")

    selection = select_frames(frames, views=views, strategy=strategy, seed=seed)
    sparse_train = dict(train_json)
    sparse_train["frames"] = selection.frames

    manifest = {
        "dataset": dataset,
        "scene": scene,
        "source_scene": str(source_scene),
        "output_scene": str(output_scene),
        "strategy": strategy,
        "seed": seed,
        "requested_views": views,
        "train_frames_available": len(frames),
        "train_frames_selected": len(selection.frames),
        "test_frames": len(test_json.get("frames", [])) if isinstance(test_json.get("frames", []), list) else None,
        "selected_indices": selection.indices,
        "selected_file_paths": selection.file_paths,
        "status": selection.status,
        "notes": selection.notes,
        "dry_run": dry_run,
        "reused_existing": False,
    }

    if dry_run:
        return manifest

    if output_scene.exists() and not force:
        existing_train = output_scene / "transforms_train.json"
        existing_test = output_scene / "transforms_test.json"
        existing_manifest = output_scene / "sparse_view_manifest.json"
        if existing_train.exists() and existing_test.exists() and existing_manifest.exists():
            current = load_json(existing_manifest)
            same_request = (
                current.get("dataset") == dataset
                and current.get("scene") == scene
                and current.get("strategy") == strategy
                and current.get("seed") == seed
                and current.get("requested_views") == views
            )
            if same_request:
                current = dict(current)
                current["reused_existing"] = True
                return current
        if existing_train.exists() or existing_test.exists():
            raise FileExistsError(f"Sparse scene already exists, pass --force to overwrite JSON files: {output_scene}")

    mirror_scene_structure(source_scene, output_scene)
    write_json(output_scene / "transforms_train.json", sparse_train)
    shutil.copy2(str(test_path), str(output_scene / "transforms_test.json"))
    write_json(output_scene / "sparse_view_manifest.json", manifest)
    return manifest


def iter_dataset_scene_specs(dataset_keys: Iterable[str], scene_names: Optional[Sequence[str]] = None):
    from scripts.refgs_runner import DATASET_CONFIGS, selected_scenes

    for dataset_key in dataset_keys:
        config = DATASET_CONFIGS[dataset_key]
        scenes = selected_scenes(config, scene_names if scene_names else None)
        for scene in scenes:
            yield dataset_key, config, scene
