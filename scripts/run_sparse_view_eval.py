import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.make_sparse_view_dataset import DEFAULT_OUTPUT_ROOT as DEFAULT_SPARSE_DATA_ROOT
from scripts.make_sparse_view_dataset import generate_sparse_datasets, sparse_scene_path
from scripts.refgs_runner import DATASET_CONFIGS, DEFAULT_DATA_ROOT, Job, selected_scenes
from scripts.sparse_view_utils import SPARSE_DATASETS, SPARSE_STRATEGIES


ERROR_MARKERS = (
    "CUDA out of memory",
    "RuntimeError:",
    "Traceback",
    "KeyboardInterrupt",
    "No space left on device",
    "FileNotFoundError:",
    "ValueError:",
    "ImportError:",
)


def _dataset_keys(dataset: str) -> List[str]:
    return list(SPARSE_DATASETS) if dataset == "all" else [dataset]


def sparse_model_path(output_root: Path, dataset: str, strategy: str, views: int, seed: int, scene: str) -> Path:
    return output_root / dataset / strategy / f"views_{views}" / f"seed_{seed}" / scene


def sparse_log_path(log_root: Path, dataset: str, strategy: str, views: int, seed: int, scene: str, action: str) -> Path:
    return log_root / dataset / strategy / f"views_{views}" / f"seed_{seed}" / scene / action


def should_skip_action(action: str, model_path: Path, iteration: int) -> bool:
    split_dir = model_path / "test" / f"ours_{iteration}"
    if action == "train":
        return (model_path / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply").exists()
    if action == "render":
        render_dir = split_dir / "renders"
        return render_dir.exists() and any(render_dir.iterdir())
    if action == "eval":
        return (split_dir / "results.json").exists() or (model_path / "results.json").exists()
    raise ValueError(f"Unknown action: {action}")


def extract_failure_reason(log_path: Optional[Path]) -> str:
    if log_path is None or not log_path.exists():
        return ""
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"could not read log: {exc}"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for marker in ERROR_MARKERS:
        for line in reversed(lines):
            if marker in line:
                return line[-500:]
    return lines[-1][-500:] if lines else ""


def _nearest_existing(path: Path) -> Path:
    current = path.resolve() if path.exists() else path.absolute()
    while not current.exists() and current.parent != current:
        current = current.parent
    return current


def _disk_record(label: str, path: Path) -> dict:
    existing = _nearest_existing(path)
    usage = shutil.disk_usage(str(existing))
    return {
        "label": label,
        "path": str(path),
        "checked_path": str(existing),
        "total_gb": round(usage.total / (1024**3), 3),
        "used_gb": round(usage.used / (1024**3), 3),
        "free_gb": round(usage.free / (1024**3), 3),
    }


def write_disk_preflight(log_root: Path, output_root: Path, data_root: Path, storage_root: Path) -> dict:
    report = {
        "output_root": str(output_root),
        "data_root": str(data_root),
        "storage_root": str(storage_root),
        "filesystems": [
            _disk_record("output_root", output_root),
            _disk_record("data_root", data_root),
            _disk_record("storage_root", storage_root),
        ],
    }
    log_root.mkdir(parents=True, exist_ok=True)
    with (log_root / "disk_preflight.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    return report


def maybe_relocate_output_root(output_root: Path, storage_root: Path, min_free_gb: float, log_root: Path, data_root: Path) -> Path:
    report = write_disk_preflight(log_root, output_root, data_root, storage_root)
    output_free = report["filesystems"][0]["free_gb"]
    if output_free >= min_free_gb or output_root.is_symlink():
        return output_root

    target = storage_root
    target.parent.mkdir(parents=True, exist_ok=True)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    if output_root.exists():
        if target.exists():
            raise FileExistsError(f"Cannot relocate {output_root}: target already exists: {target}")
        shutil.move(str(output_root), str(target))
    else:
        target.mkdir(parents=True, exist_ok=True)
    output_root.symlink_to(target, target_is_directory=True)
    report["relocated_output_root"] = {"link": str(output_root), "target": str(target), "reason": f"free_gb {output_free} < {min_free_gb}"}
    with (log_root / "disk_preflight.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    return output_root


def build_sparse_jobs(
    dataset_key: str,
    scenes: Optional[Sequence[str]],
    views: Sequence[int],
    strategy: str,
    seed: int,
    sparse_data_root: Path,
    output_root: Path,
    log_root: Path,
    gpu: Optional[str],
    actions: Iterable[str],
    python: str,
    iteration: int,
    extra_train_args: Sequence[str] = (),
    extra_render_args: Sequence[str] = (),
) -> List[Job]:
    config = DATASET_CONFIGS[dataset_key]
    env = {"CUDA_VISIBLE_DEVICES": gpu} if gpu is not None else {}
    jobs = []
    for scene in selected_scenes(config, scenes):
        for view_count in views:
            source_path = sparse_scene_path(sparse_data_root, dataset_key, strategy, view_count, seed, scene.name)
            model_path = sparse_model_path(output_root, dataset_key, strategy, view_count, seed, scene.name)
            for action in actions:
                log_path = sparse_log_path(log_root, dataset_key, strategy, view_count, seed, scene.name, action)
                if action == "train":
                    command = [
                        python,
                        config.train_script,
                        "-s",
                        str(source_path),
                        "-m",
                        str(model_path),
                        *scene.train_args,
                        *extra_train_args,
                    ]
                elif action in {"render", "eval"}:
                    command = [
                        python,
                        config.render_script,
                        "-s",
                        str(source_path),
                        "-m",
                        str(model_path),
                        "--iteration",
                        str(iteration),
                        *config.render_args,
                        "--skip_train",
                        *extra_render_args,
                    ]
                    if action == "eval":
                        command.extend(["--eval", "--metrics"])
                        command.extend(config.eval_args)
                else:
                    raise ValueError(f"Unknown action: {action}")
                jobs.append(Job(action=action, scene=scene.name, command=command, env=env, log_path=log_path))
    return jobs


def _check_sparse_scene(job: Job) -> Optional[str]:
    if "-s" not in job.command:
        return None
    source = Path(job.command[job.command.index("-s") + 1])
    missing = [name for name in ("transforms_train.json", "transforms_test.json") if not (source / name).exists()]
    if missing:
        return f"missing sparse scene files under {source}: {', '.join(missing)}"
    return None


def _model_path_from_job(job: Job) -> Path:
    return Path(job.command[job.command.index("-m") + 1])


def _write_status(log_root: Path, records: List[dict]) -> None:
    log_root.mkdir(parents=True, exist_ok=True)
    with (log_root / "run_status.json").open("w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)
        handle.write("\n")


def run_jobs(jobs: Sequence[Job], iteration: int, skip_existing: bool, dry_run: bool, log_root: Path) -> List[dict]:
    records = []
    failed_cells = set()
    for job in jobs:
        model_path = _model_path_from_job(job)
        cell_key = str(model_path)
        record = {
            "action": job.action,
            "scene": job.scene,
            "model_path": str(model_path),
            "log_path": str(job.log_path) if job.log_path else None,
            "command": job.display(),
            "status": "pending",
            "returncode": None,
            "notes": "",
            "failure_reason": "",
        }
        if job.action in {"render", "eval"} and cell_key in failed_cells:
            record["status"] = "failed"
            record["notes"] = "skipped because an earlier action failed for this cell"
            record["failure_reason"] = record["notes"]
            records.append(record)
            _write_status(log_root, records)
            print(f"FAILED dependency {job.action} {job.scene}: {record['notes']}")
            continue
        missing = _check_sparse_scene(job)
        if missing:
            record["status"] = "failed"
            record["notes"] = missing
            record["failure_reason"] = missing
            failed_cells.add(cell_key)
            print(f"FAILED precheck {job.action} {job.scene}: {missing}")
            records.append(record)
            _write_status(log_root, records)
            continue
        if skip_existing and should_skip_action(job.action, model_path, iteration):
            record["status"] = "skipped_existing"
            print(f"SKIP existing {job.action} {job.scene}: {model_path}")
            records.append(record)
            _write_status(log_root, records)
            continue

        print(job.display())
        if dry_run:
            record["status"] = "dry_run"
            records.append(record)
            _write_status(log_root, records)
            continue

        if job.log_path is not None:
            job.log_path.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(job.env)
        try:
            if job.log_path is None:
                completed = subprocess.run(job.command, check=False, env=env)
            else:
                with job.log_path.open("w", encoding="utf-8") as log_file:
                    completed = subprocess.run(job.command, check=False, env=env, stdout=log_file, stderr=subprocess.STDOUT)
            record["returncode"] = completed.returncode
            record["status"] = "ok" if completed.returncode == 0 else "failed"
            if completed.returncode != 0:
                record["failure_reason"] = extract_failure_reason(job.log_path)
                record["notes"] = f"{record['failure_reason']}; see log: {job.log_path}" if record["failure_reason"] else f"see log: {job.log_path}"
                failed_cells.add(cell_key)
                print(f"FAILED {job.action} {job.scene}, log: {job.log_path}")
        except Exception as exc:
            record["status"] = "failed"
            record["failure_reason"] = f"{type(exc).__name__}: {exc}"
            record["notes"] = f"{record['failure_reason']}; log: {job.log_path}"
            failed_cells.add(cell_key)
            print(f"FAILED {job.action} {job.scene}: {record['notes']}")
        records.append(record)
        _write_status(log_root, records)
    _write_status(log_root, records)
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sparse-view Ref-GS train/render/eval jobs.")
    parser.add_argument("--dataset", choices=SPARSE_DATASETS + ("all",), required=True)
    parser.add_argument("--scene", nargs="+", default=None)
    parser.add_argument("--views", nargs="+", type=int, required=True)
    parser.add_argument("--strategy", choices=SPARSE_STRATEGIES, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--gpu", default="1")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--sparse-data-root", type=Path, default=DEFAULT_SPARSE_DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=Path("output/sparse_view"))
    parser.add_argument("--log-root", type=Path, default=Path("logs/sparse_view"))
    parser.add_argument("--iteration", type=int, default=31000)
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--make-data", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--extra-train-arg", action="append", default=[])
    parser.add_argument("--extra-render-arg", action="append", default=[])
    parser.add_argument("--force-data", action="store_true", help="Overwrite generated sparse JSON files when --make-data is used.")
    parser.add_argument("--storage-root", type=Path, default=Path("/data/liuly/refgs_sparse_view_storage"))
    parser.add_argument("--min-output-free-gb", type=float, default=40.0)
    parser.add_argument("--no-auto-relocate-output", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    actions = [name for name in ("train", "render", "eval") if getattr(args, name)]
    if not actions:
        if args.dry_run:
            actions = ["train", "render", "eval"]
        else:
            raise SystemExit("Choose at least one action: --train, --render, --eval, or use --dry-run.")

    if args.no_auto_relocate_output:
        write_disk_preflight(args.log_root, args.output_root, args.data_root, args.storage_root)
    else:
        args.output_root = maybe_relocate_output_root(
            output_root=args.output_root,
            storage_root=args.storage_root,
            min_free_gb=args.min_output_free_gb,
            log_root=args.log_root,
            data_root=args.data_root,
        )

    if args.make_data:
        generate_sparse_datasets(
            dataset=args.dataset,
            scenes=args.scene,
            data_root=args.data_root,
            source_subdir=None,
            output_root=args.sparse_data_root,
            views=args.views,
            strategy=args.strategy,
            seed=args.seed,
            dry_run=args.dry_run,
            force=args.force_data,
            continue_on_error=True,
        )

    all_jobs = []
    for dataset_key in _dataset_keys(args.dataset):
        all_jobs.extend(
            build_sparse_jobs(
                dataset_key=dataset_key,
                scenes=args.scene,
                views=args.views,
                strategy=args.strategy,
                seed=args.seed,
                sparse_data_root=args.sparse_data_root,
                output_root=args.output_root,
                log_root=args.log_root,
                gpu=args.gpu,
                actions=actions,
                python=args.python,
                iteration=args.iteration,
                extra_train_args=args.extra_train_arg,
                extra_render_args=args.extra_render_arg,
            )
        )
    run_jobs(all_jobs, iteration=args.iteration, skip_existing=args.skip_existing, dry_run=args.dry_run, log_root=args.log_root)


if __name__ == "__main__":
    main()
