import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.refgs_runner import DATASET_CONFIGS, DEFAULT_DATA_ROOT
from scripts.sparse_view_utils import SPARSE_DATASETS, SPARSE_STRATEGIES, generate_sparse_scene, iter_dataset_scene_specs


DEFAULT_OUTPUT_ROOT = DEFAULT_DATA_ROOT / "SparseViewGenerated"


def dataset_keys(value: str) -> List[str]:
    return list(SPARSE_DATASETS) if value == "all" else [value]


def sparse_scene_path(output_root: Path, dataset: str, strategy: str, views: int, seed: int, scene: str) -> Path:
    return output_root / dataset / strategy / f"views_{views}" / f"seed_{seed}" / scene


def generate_sparse_datasets(
    dataset: str,
    scenes: Optional[Sequence[str]],
    data_root: Path,
    source_subdir: Optional[str],
    output_root: Path,
    views: Sequence[int],
    strategy: str,
    seed: int,
    dry_run: bool = False,
    force: bool = False,
) -> List[dict]:
    manifests = []
    for dataset_key, config, scene in iter_dataset_scene_specs(dataset_keys(dataset), scenes):
        subdir = source_subdir or config.data_subdir
        source_scene = data_root / subdir / scene.source_dir
        for view_count in views:
            output_scene = sparse_scene_path(output_root, dataset_key, strategy, view_count, seed, scene.name)
            manifest = generate_sparse_scene(
                dataset=dataset_key,
                scene=scene.name,
                source_scene=source_scene,
                output_scene=output_scene,
                views=view_count,
                strategy=strategy,
                seed=seed,
                dry_run=dry_run,
                force=force,
            )
            manifests.append(manifest)
            status = manifest["status"]
            prefix = "DRY-RUN" if dry_run else "EXISTS" if manifest.get("reused_existing") else "WROTE"
            print(
                f"{prefix} {dataset_key}/{scene.name} views={view_count} strategy={strategy} "
                f"seed={seed} selected={manifest['train_frames_selected']}/"
                f"{manifest['train_frames_available']} status={status} -> {output_scene}"
            )
    return manifests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Blender-style sparse-view train splits for Ref-GS.")
    parser.add_argument("--dataset", choices=SPARSE_DATASETS + ("all",), required=True)
    parser.add_argument("--scene", nargs="+", default=None, help="Scene name(s). Omit for all scenes in the selected dataset.")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--source-subdir", default=None, help="Override source dataset subdirectory under --data-root.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--views", nargs="+", type=int, required=True)
    parser.add_argument("--strategy", choices=SPARSE_STRATEGIES, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_sparse_datasets(
        dataset=args.dataset,
        scenes=args.scene,
        data_root=args.data_root,
        source_subdir=args.source_subdir,
        output_root=args.output_root,
        views=args.views,
        strategy=args.strategy,
        seed=args.seed,
        dry_run=args.dry_run,
        force=args.force,
    )


if __name__ == "__main__":
    main()
