import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from scripts.make_sparse_view_dataset import generate_sparse_datasets, sparse_scene_path
from scripts.refgs_runner import Job
from scripts.run_sparse_view_eval import build_sparse_jobs, parse_args, run_jobs, should_skip_action


class SparseViewRunnerTests(unittest.TestCase):
    def test_build_sparse_jobs_uses_refgs_config_and_sparse_paths(self):
        jobs = build_sparse_jobs(
            dataset_key="refnerf",
            scenes=["coffee"],
            views=[3],
            strategy="uniform_pose",
            seed=0,
            sparse_data_root=Path("/data/liuly/dataset/3DGS/SparseViewGenerated"),
            output_root=Path("output/sparse_view"),
            log_root=Path("logs/sparse_view"),
            gpu="1",
            actions=["train", "render", "eval"],
            python="python",
            iteration=31000,
        )

        self.assertEqual([job.action for job in jobs], ["train", "render", "eval"])
        train = jobs[0]
        self.assertEqual(train.env["CUDA_VISIBLE_DEVICES"], "1")
        self.assertEqual(train.command[:2], ["python", "train.py"])
        self.assertIn("/data/liuly/dataset/3DGS/SparseViewGenerated/refnerf/uniform_pose/views_3/seed_0/coffee", train.command)
        self.assertIn("output/sparse_view/refnerf/uniform_pose/views_3/seed_0/coffee", train.command)
        self.assertIn("--albedo_lr", train.command)
        self.assertIn("0.002", train.command)

        render = jobs[1]
        self.assertEqual(render.command[:2], ["python", "render.py"])
        self.assertIn("--skip_train", render.command)
        self.assertNotIn("--split", render.command)
        self.assertNotIn("--metrics", render.command)

        eval_job = jobs[2]
        self.assertIn("--eval", eval_job.command)
        self.assertIn("--metrics", eval_job.command)
        self.assertEqual(eval_job.log_path, Path("logs/sparse_view/refnerf/uniform_pose/views_3/seed_0/coffee/eval"))

    def test_skip_existing_checks_expected_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp)
            self.assertFalse(should_skip_action("train", model, 10))
            (model / "point_cloud" / "iteration_10").mkdir(parents=True)
            (model / "point_cloud" / "iteration_10" / "point_cloud.ply").write_text("ply", encoding="utf-8")
            self.assertTrue(should_skip_action("train", model, 10))

            self.assertFalse(should_skip_action("render", model, 10))
            renders = model / "test" / "ours_10" / "renders"
            renders.mkdir(parents=True)
            (renders / "000.png").write_text("x", encoding="utf-8")
            self.assertTrue(should_skip_action("render", model, 10))

            self.assertFalse(should_skip_action("eval", model, 10))
            (model / "test" / "ours_10" / "results.json").write_text("{}", encoding="utf-8")
            self.assertTrue(should_skip_action("eval", model, 10))

    def test_generate_sparse_datasets_can_record_failed_scene_and_continue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_root = root / "SparseViewGenerated"

            manifests = generate_sparse_datasets(
                dataset="refnerf",
                scenes=["coffee"],
                data_root=root / "missing_data",
                source_subdir=None,
                output_root=output_root,
                views=[3],
                strategy="uniform_pose",
                seed=0,
                continue_on_error=True,
            )

            self.assertEqual(len(manifests), 1)
            manifest = manifests[0]
            self.assertEqual(manifest["status"], "failed")
            self.assertIn("Missing transforms_train.json", manifest["notes"])
            manifest_path = sparse_scene_path(output_root, "refnerf", "uniform_pose", 3, 0, "coffee") / "sparse_view_manifest.json"
            self.assertTrue(manifest_path.exists())

    def test_runner_defaults_child_python_to_current_interpreter(self):
        argv = [
            "run_sparse_view_eval.py",
            "--dataset",
            "refnerf",
            "--views",
            "3",
            "--strategy",
            "uniform_pose",
            "--dry-run",
        ]
        with mock.patch("sys.argv", argv):
            args = parse_args()

        self.assertEqual(args.python, sys.executable)

    def test_run_jobs_records_failure_reason_from_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model"
            log_root = root / "logs"
            log_path = log_root / "train"
            job = Job(
                action="train",
                scene="coffee",
                command=[
                    sys.executable,
                    "-c",
                    "import sys; print('RuntimeError: CUDA out of memory'); sys.exit(2)",
                    "-m",
                    str(model),
                ],
                log_path=log_path,
            )

            records = run_jobs([job], iteration=10, skip_existing=False, dry_run=False, log_root=log_root)

            self.assertEqual(records[0]["status"], "failed")
            self.assertIn("CUDA out of memory", records[0]["failure_reason"])
            status = json.loads((log_root / "run_status.json").read_text(encoding="utf-8"))
            self.assertIn("failure_reason", status[0])


if __name__ == "__main__":
    unittest.main()
