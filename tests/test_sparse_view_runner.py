import tempfile
import unittest
from pathlib import Path

from scripts.run_sparse_view_eval import build_sparse_jobs, should_skip_action


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
        self.assertIn("--split", render.command)
        self.assertIn("test", render.command)
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


if __name__ == "__main__":
    unittest.main()
