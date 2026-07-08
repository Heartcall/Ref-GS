import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.summarize_sparse_view import collect_sparse_rows, write_summary


class SparseViewSummaryTests(unittest.TestCase):
    def test_summary_computes_metric_deltas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sparse_root = root / "output" / "sparse_view"
            model = sparse_root / "refnerf" / "uniform_pose" / "views_3" / "seed_0" / "coffee"
            model.mkdir(parents=True)
            (model / "results.json").write_text(
                json.dumps({"aggregate": {"iteration": 31000, "psnr": 20.0, "ssim": 0.8, "lpips": 0.2, "count": 200}}),
                encoding="utf-8",
            )
            (model / "point_cloud" / "iteration_31000").mkdir(parents=True)
            (model / "point_cloud" / "iteration_31000" / "point_cloud.ply").write_text("ply", encoding="utf-8")
            renders = model / "test" / "ours_31000" / "renders"
            renders.mkdir(parents=True)
            (renders / "000.png").write_text("x", encoding="utf-8")

            baseline_csv = root / "metrics_summary.csv"
            with baseline_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["dataset", "scene", "psnr", "ssim", "lpips"])
                writer.writeheader()
                writer.writerow({"dataset": "refnerf", "scene": "coffee", "psnr": "30.0", "ssim": "0.9", "lpips": "0.1"})

            rows = collect_sparse_rows(
                sparse_output_root=sparse_root,
                baseline_output_root=root / "missing_baseline_root",
                baseline_metrics_csv=baseline_csv,
                sparse_data_root=root / "sparse_data",
                iteration=31000,
            )

            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["status"], "ok")
            self.assertAlmostEqual(row["delta_psnr"], -10.0)
            self.assertAlmostEqual(row["delta_ssim"], -0.1)
            self.assertAlmostEqual(row["delta_lpips"], 0.1)

    def test_missing_metrics_is_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sparse_root = root / "output" / "sparse_view"
            model = sparse_root / "refnerf" / "uniform_pose" / "views_3" / "seed_0" / "coffee"
            model.mkdir(parents=True)

            rows = collect_sparse_rows(
                sparse_output_root=sparse_root,
                baseline_output_root=root / "baseline",
                baseline_metrics_csv=root / "missing.csv",
                sparse_data_root=root / "sparse_data",
                iteration=31000,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "missing_metrics")

    def test_manifest_without_model_output_is_reported_missing_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sparse_data = root / "SparseViewGenerated"
            manifest_dir = sparse_data / "refnerf" / "uniform_pose" / "views_3" / "seed_0" / "coffee"
            manifest_dir.mkdir(parents=True)
            (manifest_dir / "sparse_view_manifest.json").write_text(
                json.dumps({"train_frames_selected": 3, "test_frames": 200, "notes": ""}),
                encoding="utf-8",
            )

            rows = collect_sparse_rows(
                sparse_output_root=root / "missing_output",
                baseline_output_root=root / "baseline",
                baseline_metrics_csv=root / "missing.csv",
                sparse_data_root=sparse_data,
                iteration=31000,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["dataset"], "refnerf")
            self.assertEqual(rows[0]["train_views"], 3)
            self.assertEqual(rows[0]["test_views"], 200)
            self.assertEqual(rows[0]["status"], "missing_metrics")

    def test_failed_sparse_manifest_is_reported_as_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sparse_data = root / "SparseViewGenerated"
            manifest_dir = sparse_data / "refnerf" / "uniform_pose" / "views_3" / "seed_0" / "coffee"
            manifest_dir.mkdir(parents=True)
            (manifest_dir / "sparse_view_manifest.json").write_text(
                json.dumps(
                    {
                        "train_frames_selected": None,
                        "test_frames": None,
                        "status": "failed",
                        "notes": "FileNotFoundError: missing source scene",
                    }
                ),
                encoding="utf-8",
            )

            rows = collect_sparse_rows(
                sparse_output_root=root / "missing_output",
                baseline_output_root=root / "baseline",
                baseline_metrics_csv=root / "missing.csv",
                sparse_data_root=sparse_data,
                iteration=31000,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "failed")
            self.assertIn("missing source scene", rows[0]["notes"])

    def test_write_summary_creates_csv_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_root = Path(tmp)
            rows = [
                {
                    "dataset": "refnerf",
                    "scene": "coffee",
                    "strategy": "uniform_pose",
                    "views": 3,
                    "seed": 0,
                    "iteration": 31000,
                    "train_views": None,
                    "test_views": None,
                    "psnr": 20.0,
                    "ssim": 0.8,
                    "lpips": 0.2,
                    "baseline_psnr": 30.0,
                    "baseline_ssim": 0.9,
                    "baseline_lpips": 0.1,
                    "delta_psnr": -10.0,
                    "delta_ssim": -0.1,
                    "delta_lpips": 0.1,
                    "checkpoint_exists": False,
                    "render_exists": False,
                    "metrics_exists": True,
                    "status": "ok",
                    "notes": "",
                }
            ]

            write_summary(rows, log_root)

            self.assertTrue((log_root / "sparse_view_summary.csv").exists())
            self.assertTrue((log_root / "sparse_view_summary.json").exists())
            md = (log_root / "sparse_view_summary.md").read_text(encoding="utf-8")
            self.assertIn("Coverage", md)
            self.assertIn("Dataset Averages", md)
            self.assertIn("Failure Summary", md)


if __name__ == "__main__":
    unittest.main()
