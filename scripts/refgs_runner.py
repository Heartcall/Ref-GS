import argparse
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_DATA_ROOT = Path("/data/liuly/dataset/3DGS")


@dataclass(frozen=True)
class SceneConfig:
    name: str
    source_name: Optional[str] = None
    train_args: Tuple[str, ...] = ()

    @property
    def source_dir(self) -> str:
        return self.source_name or self.name


@dataclass(frozen=True)
class DatasetConfig:
    key: str
    data_subdir: str
    output_subdir: str
    train_script: str
    render_script: str
    scenes: Tuple[SceneConfig, ...]
    render_args: Tuple[str, ...] = ()
    eval_args: Tuple[str, ...] = ()
    converted_hint: Optional[str] = None

    def scene_map(self) -> Dict[str, SceneConfig]:
        return {scene.name: scene for scene in self.scenes}


@dataclass(frozen=True)
class Job:
    action: str
    scene: str
    command: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    log_path: Optional[Path] = None

    def display(self) -> str:
        env_prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in sorted(self.env.items()))
        command = " ".join(shlex.quote(str(part)) for part in self.command)
        if env_prefix:
            command = f"{env_prefix} {command}"
        if self.log_path is not None:
            command = f"{command} > {shlex.quote(str(self.log_path))} 2>&1"
        return command


def _scene(name: str, *args: str, source_name: Optional[str] = None) -> SceneConfig:
    return SceneConfig(name=name, source_name=source_name, train_args=tuple(args))


COMMON_REFNERF_ARGS = ("--eval", "--run_dim", "256", "--albedo_bias", "0")
COMMON_NERF_ARGS = ("--eval", "--run_dim", "64", "--albedo_bias", "0")
COMMON_GLOSSY_ARGS = (
    "--eval",
    "--run_dim",
    "256",
    "--albedo_bias",
    "2",
    "--albedo_lr",
    "0.0005",
    "--init_until_iter",
    "3000",
)
COMMON_REAL_ARGS = ("--eval", "--run_dim", "256", "--albedo_bias", "2", "--albedo_lr", "0.0005")


DATASET_CONFIGS: Dict[str, DatasetConfig] = {
    "refnerf": DatasetConfig(
        key="refnerf",
        data_subdir="Shiny Blender Synthetic",
        output_subdir="refnerf",
        train_script="train.py",
        render_script="render.py",
        scenes=(
            _scene("helmet", *COMMON_REFNERF_ARGS),
            _scene("car", *COMMON_REFNERF_ARGS),
            _scene("ball", *COMMON_REFNERF_ARGS),
            _scene("teapot", *COMMON_REFNERF_ARGS),
            _scene("coffee", *COMMON_REFNERF_ARGS, "--albedo_lr", "0.002"),
            _scene("toaster", *COMMON_REFNERF_ARGS),
        ),
        render_args=("--renderer", "refgs"),
    ),
    "nerf_synthetic": DatasetConfig(
        key="nerf_synthetic",
        data_subdir="NeRF Synthetic",
        output_subdir="nerf_synthetic",
        train_script="train-NeRF.py",
        render_script="render.py",
        scenes=(
            _scene("ship", *COMMON_NERF_ARGS, "--gsrgb_loss", "--albedo_lr", "0.002"),
            _scene("ficus", *COMMON_NERF_ARGS, "--gsrgb_loss", "--albedo_lr", "0.002"),
            _scene("lego", *COMMON_NERF_ARGS, "--gsrgb_loss", "--albedo_lr", "0.002"),
            _scene("mic", *COMMON_NERF_ARGS, "--gsrgb_loss", "--albedo_lr", "0.002"),
            _scene("hotdog", *COMMON_NERF_ARGS, "--gsrgb_loss", "--albedo_lr", "0.002"),
            _scene("chair", *COMMON_NERF_ARGS, "--gsrgb_loss", "--albedo_lr", "0.002"),
            _scene("materials", "--eval", "--run_dim", "256", "--albedo_bias", "0"),
            _scene("drums", *COMMON_NERF_ARGS, "--albedo_lr", "0.002"),
        ),
        render_args=("--renderer", "nerf"),
    ),
    "glossy_synthetic": DatasetConfig(
        key="glossy_synthetic",
        data_subdir="GlossySyntheticConverted",
        output_subdir="glossy_synthetic",
        train_script="train-NeRO.py",
        render_script="render.py",
        scenes=(
            _scene("bell_blender", *COMMON_GLOSSY_ARGS),
            _scene("tbell_blender", *COMMON_GLOSSY_ARGS),
            _scene("potion_blender", *COMMON_GLOSSY_ARGS),
            _scene("teapot_blender", *COMMON_GLOSSY_ARGS),
            _scene("luyu_blender", *COMMON_GLOSSY_ARGS),
            _scene("cat_blender", *COMMON_GLOSSY_ARGS),
        ),
        render_args=("--renderer", "refgs", "--dataset", "glossy"),
        converted_hint="Run `python nero2blender.py --path <raw GlossySynthetic root> --scene <scene>` first, or pass --data-root/--dataset-subdir to the converted directory.",
    ),
    "ref_real": DatasetConfig(
        key="ref_real",
        data_subdir="Shiny Blender Real",
        output_subdir="ref_real",
        train_script="train-real.py",
        render_script="render-real.py",
        scenes=(
            _scene(
                "sedan",
                *COMMON_REAL_ARGS,
                "-r",
                "8",
                "--env_scope_center",
                "-0.032",
                "0.808",
                "0.751",
                "--env_scope_radius",
                "2.138",
                "--init_until_iter",
                "700",
                "--xyz_axis",
                "2.0",
                "1.0",
                "0.0",
            ),
            _scene(
                "gardenspheres",
                *COMMON_REAL_ARGS,
                "-r",
                "6",
                "--env_scope_center",
                "-0.2270",
                "1.9700",
                "1.7740",
                "--env_scope_radius",
                "0.974",
                "--init_until_iter",
                "700",
                "--xyz_axis",
                "2.0",
                "1.0",
                "0.0",
            ),
            _scene(
                "toycar",
                *COMMON_REAL_ARGS,
                "-r",
                "6",
                "--env_scope_center",
                "0.486",
                "1.108",
                "3.72",
                "--env_scope_radius",
                "2.507",
                "--init_until_iter",
                "1500",
                "--xyz_axis",
                "0.0",
                "2.0",
                "1.0",
            ),
        ),
        render_args=(),
        eval_args=(),
    ),
}


def selected_scenes(config: DatasetConfig, names: Optional[Sequence[str]]) -> List[SceneConfig]:
    if not names or names == ["all"]:
        return list(config.scenes)
    scene_map = config.scene_map()
    missing = [name for name in names if name not in scene_map]
    if missing:
        raise ValueError(f"Unknown scene(s) for {config.key}: {', '.join(missing)}")
    return [scene_map[name] for name in names]


def _source_path(config: DatasetConfig, scene: SceneConfig, data_root: Path, dataset_subdir: Optional[str]) -> Path:
    return data_root / (dataset_subdir or config.data_subdir) / scene.source_dir


def _model_path(config: DatasetConfig, scene: SceneConfig, output_root: Path) -> Path:
    return output_root / config.output_subdir / scene.name


def _check_source(path: Path, config: DatasetConfig) -> None:
    if not path.exists():
        hint = f" {config.converted_hint}" if config.converted_hint else ""
        raise FileNotFoundError(f"Scene source directory not found: {path}.{hint}")
    if not ((path / "transforms_train.json").exists() or (path / "sparse").exists()):
        hint = f" {config.converted_hint}" if config.converted_hint else ""
        raise FileNotFoundError(f"Scene is not in a Ref-GS-readable format: {path}.{hint}")


def build_jobs(
    config: DatasetConfig,
    scenes: Optional[Sequence[str]],
    data_root: Path,
    output_root: Path,
    gpu: Optional[str],
    actions: Iterable[str],
    python: str,
    iteration: int = -1,
    dataset_subdir: Optional[str] = None,
    log_root: Optional[Path] = None,
    check_paths: bool = False,
    extra_train_args: Sequence[str] = (),
    extra_render_args: Sequence[str] = (),
) -> List[Job]:
    jobs = []  # type: List[Job]
    env = {"CUDA_VISIBLE_DEVICES": gpu} if gpu is not None else {}
    for scene in selected_scenes(config, list(scenes) if scenes else None):
        source_path = _source_path(config, scene, data_root, dataset_subdir)
        model_path = _model_path(config, scene, output_root)
        if check_paths:
            _check_source(source_path, config)

        for action in actions:
            log_path = None
            if log_root is not None:
                log_path = log_root / config.output_subdir / scene.name / action
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
                    *extra_render_args,
                ]
                if action == "eval":
                    command.extend(["--eval", "--metrics"])
                    command.extend(config.eval_args)
            else:
                raise ValueError(f"Unknown action: {action}")
            jobs.append(Job(action=action, scene=scene.name, command=command, env=env, log_path=log_path))
    return jobs


def parse_common_args(dataset_key: str) -> argparse.Namespace:
    config = DATASET_CONFIGS[dataset_key]
    parser = argparse.ArgumentParser(description=f"Run Ref-GS reproduction commands for {dataset_key}.")
    parser.add_argument("--scene", nargs="+", default=["all"], help="Scene name(s), or all.")
    parser.add_argument("--list-scenes", action="store_true", help="Print known scenes and exit.")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--dataset-subdir", default=None, help=f"Override dataset subdir under data-root; default: {config.data_subdir}")
    parser.add_argument("--output-root", type=Path, default=Path("output/repro"))
    parser.add_argument("--log-root", type=Path, default=Path("logs/repro"))
    parser.add_argument("--gpu", default=None, help="GPU id for CUDA_VISIBLE_DEVICES. Omit to inherit environment.")
    parser.add_argument("--python", default="python", help="Python executable used for subprocess commands.")
    parser.add_argument("--iteration", type=int, default=-1, help="Render/eval iteration. -1 loads the latest saved point cloud.")
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--skip-path-check", action="store_true", help="Do not check dataset directories before building commands.")
    parser.add_argument("--extra-train-arg", action="append", default=[], help="Append one extra arg to train command. Repeat for multiple args.")
    parser.add_argument("--extra-render-arg", action="append", default=[], help="Append one extra arg to render/eval command. Repeat for multiple args.")
    args = parser.parse_args()
    if args.list_scenes:
        print("\n".join(scene.name for scene in config.scenes))
        raise SystemExit(0)
    return args


def run_dataset(dataset_key: str) -> None:
    config = DATASET_CONFIGS[dataset_key]
    args = parse_common_args(dataset_key)
    actions = [name for name in ("train", "render", "eval") if getattr(args, name)]
    if not actions:
        if args.dry_run:
            actions = ["train", "render", "eval"]
        else:
            raise SystemExit("Choose at least one action: --train, --render, --eval, or use --dry-run.")

    jobs = build_jobs(
        config,
        scenes=args.scene,
        data_root=args.data_root,
        output_root=args.output_root,
        gpu=args.gpu,
        actions=actions,
        python=args.python,
        iteration=args.iteration,
        dataset_subdir=args.dataset_subdir,
        log_root=args.log_root,
        check_paths=not args.skip_path_check,
        extra_train_args=args.extra_train_arg,
        extra_render_args=args.extra_render_arg,
    )

    for job in jobs:
        print(job.display())
        if args.dry_run:
            continue
        if job.log_path is not None:
            job.log_path.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(job.env)
        if job.log_path is None:
            subprocess.run(job.command, check=True, env=env)
        else:
            with job.log_path.open("w", encoding="utf-8") as log_file:
                subprocess.run(job.command, check=True, env=env, stdout=log_file, stderr=subprocess.STDOUT)
