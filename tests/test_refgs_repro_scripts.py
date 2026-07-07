import os
import unittest
from pathlib import Path

from scripts.refgs_runner import DATASET_CONFIGS, build_jobs


class RefGSRunnerTests(unittest.TestCase):
    def test_refnerf_coffee_train_command_keeps_original_hparams(self):
        jobs = build_jobs(
            DATASET_CONFIGS["refnerf"],
            scenes=["coffee"],
            data_root=Path("/data/liuly/dataset/3DGS"),
            output_root=Path("output/repro"),
            gpu="3",
            actions=("train",),
            python="python",
        )

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job.env["CUDA_VISIBLE_DEVICES"], "3")
        self.assertNotIn("CUDA_VISIBLE_DEVICES", job.command)
        self.assertEqual(job.command[:2], ["python", "train.py"])
        self.assertIn("/data/liuly/dataset/3DGS/Shiny Blender Synthetic/coffee", job.command)
        self.assertIn("output/repro/refnerf/coffee", job.command)
        self.assertIn("--run_dim", job.command)
        self.assertIn("256", job.command)
        self.assertIn("--albedo_lr", job.command)
        self.assertIn("0.002", job.command)

    def test_ref_real_gardenspheres_command_uses_real_entry_and_env_scope(self):
        jobs = build_jobs(
            DATASET_CONFIGS["ref_real"],
            scenes=["gardenspheres"],
            data_root=Path("/data/liuly/dataset/3DGS"),
            output_root=Path("output/repro"),
            gpu="0",
            actions=("train",),
            python="python",
        )

        command = jobs[0].command
        self.assertEqual(command[:2], ["python", "train-real.py"])
        self.assertIn("-r", command)
        self.assertIn("6", command)
        self.assertIn("--env_scope_center", command)
        center_index = command.index("--env_scope_center")
        self.assertEqual(command[center_index + 1 : center_index + 4], ["-0.2270", "1.9700", "1.7740"])
        self.assertIn("--xyz_axis", command)

    def test_render_and_eval_jobs_target_refgs_renderer(self):
        jobs = build_jobs(
            DATASET_CONFIGS["nerf_synthetic"],
            scenes=["lego"],
            data_root=Path("/data/liuly/dataset/3DGS"),
            output_root=Path("output/repro"),
            gpu=None,
            actions=("render", "eval"),
            python="python",
            iteration=31000,
        )

        self.assertEqual([job.action for job in jobs], ["render", "eval"])
        self.assertEqual(jobs[0].command[:2], ["python", "render.py"])
        self.assertNotIn("--eval", jobs[0].command)
        self.assertEqual(jobs[1].command[:2], ["python", "render.py"])
        self.assertIn("--eval", jobs[1].command)
        self.assertIn("--metrics", jobs[1].command)
        self.assertIn("--iteration", jobs[1].command)
        self.assertIn("31000", jobs[1].command)


if __name__ == "__main__":
    unittest.main()
