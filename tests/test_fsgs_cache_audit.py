import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class FSGSCacheAuditTests(unittest.TestCase):
    def test_runtime_provenance_separates_training_and_shared_evaluator(self):
        from scripts.audit_fsgs_shared_eval_cache import runtime_provenance

        with tempfile.TemporaryDirectory() as directory:
            environment = Path(directory) / "environment.json"
            environment.write_text(json.dumps({"runtime": {
                "python": "/envs/FSGS/bin/python",
                "python_version": "3.8.1",
                "torch_version": "1.12.1",
                "torch_cuda_version": "11.6",
            }}))
            runtime = runtime_provenance(environment)
            self.assertEqual(runtime["original_fsgs_training_runtime"]["torch_cuda_version"], "11.6")
            self.assertEqual(runtime["shared_evaluator_runtime"]["torch_cuda_version"], "11.3")
            self.assertNotEqual(
                runtime["original_fsgs_training_runtime"]["python"],
                runtime["shared_evaluator_runtime"]["python_executable"],
            )

    def test_module_import_does_not_import_gpu_or_image_metric_packages(self):
        code = (
            "import sys; "
            "import scripts.audit_fsgs_shared_eval_cache; "
            "assert 'torch' not in sys.modules; "
            "assert 'lpipsPyTorch' not in sys.modules; "
            "assert 'PIL' not in sys.modules"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=str(REPO_ROOT),
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_manifest_fingerprint_changes_when_input_bytes_change(self):
        from scripts.audit_fsgs_shared_eval_cache import directory_manifest

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.png").write_bytes(b"first")
            before = directory_manifest(root)
            (root / "a.png").write_bytes(b"second")
            after = directory_manifest(root)
            self.assertNotEqual(before["manifest_sha256"], after["manifest_sha256"])
            self.assertEqual(before["names"], ["a.png"])

    def test_valid_legacy_cache_is_registered_without_current_evaluator_match(self):
        from scripts.audit_fsgs_shared_eval_cache import audit_cell

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            renders = root / "model" / "test" / "ours_10000" / "renders"
            gt = root / "model" / "test" / "ours_10000" / "gt"
            cache = root / "cache"
            renders.mkdir(parents=True); gt.mkdir(parents=True); cache.mkdir()
            names = ("a.png", "b.png", "c.png")
            for target in (renders, gt):
                for name in names:
                    (target / name).write_bytes(b"png")
            values = {"PSNR": 10.0, "SSIM": 0.5, "LPIPS": 0.2}
            per_view = {metric: {name: value for name in names} for metric, value in values.items()}
            (cache / "results.json").write_text(json.dumps({"ours_10000": values}))
            (cache / "per_view.json").write_text(json.dumps({"ours_10000": per_view}))
            (cache / "evaluator_metadata.json").write_text(json.dumps({
                "evaluator_sha256": "1" * 64,
                "fsgs_metrics_sha256": "2" * 64,
                "lpips_backbone": "vgg",
            }))
            result = audit_cell(
                "1_8", "fern", root / "model", cache,
                current_evaluator_sha256="3" * 64,
                current_fsgs_metrics_sha256="2" * 64,
            )
            self.assertEqual(result["status"], "reusable_registered")
            self.assertTrue(result["evaluator_file_changed"])
            self.assertFalse(result["numeric_change_proven"])
            self.assertEqual(result["reason"], "legacy_cache_registered_without_recompute")

    def test_unreadable_external_inputs_are_unknown_not_cache_miss(self):
        from scripts.audit_fsgs_shared_eval_cache import audit_cell

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = audit_cell(
                "1_8", "fern", root / "missing-model", root / "missing-cache",
                current_evaluator_sha256="3" * 64,
                current_fsgs_metrics_sha256="2" * 64,
            )
            self.assertEqual(result["status"], "external_access_unknown")
            self.assertNotEqual(result["reason"], "cache_miss")

    def test_saved_input_fingerprint_is_reused_without_recalculation(self):
        from scripts.audit_fsgs_shared_eval_cache import audit_cell

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            renders = root / "model" / "test" / "ours_10000" / "renders"
            gt = root / "model" / "test" / "ours_10000" / "gt"
            cache = root / "cache"
            renders.mkdir(parents=True); gt.mkdir(parents=True); cache.mkdir()
            names = ("a.png", "b.png", "c.png")
            for target in (renders, gt):
                for name in names:
                    (target / name).write_bytes(b"png")
            values = {"PSNR": 10.0, "SSIM": 0.5, "LPIPS": 0.2}
            per_view = {metric: {name: value for name in names} for metric, value in values.items()}
            (cache / "results.json").write_text(json.dumps({"ours_10000": values}))
            (cache / "per_view.json").write_text(json.dumps({"ours_10000": per_view}))
            (cache / "evaluator_metadata.json").write_text(json.dumps({
                "evaluator_sha256": "1" * 64,
                "fsgs_metrics_sha256": "2" * 64,
                "lpips_backbone": "vgg",
            }))
            first = audit_cell(
                "1_8", "fern", root / "model", cache,
                current_evaluator_sha256="3" * 64,
                current_fsgs_metrics_sha256="2" * 64,
            )
            saved = {
                key: first[key]
                for key in (
                    "input_fingerprint", "numeric_evaluator_fingerprint",
                    "shared_evaluator_runtime_fingerprint", "lpips_backbone",
                )
            }
            second = audit_cell(
                "1_8", "fern", root / "model", cache,
                current_evaluator_sha256="3" * 64,
                current_fsgs_metrics_sha256="2" * 64,
                previous=saved,
            )
            self.assertEqual(second["status"], "reusable")
            self.assertEqual(second["reason"], "cache_identity_matches")

    def test_numeric_runtime_or_backbone_change_invalidates_without_running_metrics(self):
        from scripts.audit_fsgs_shared_eval_cache import cache_identity_status

        saved = {
            "input_fingerprint": "1" * 64,
            "numeric_evaluator_fingerprint": "2" * 64,
            "shared_evaluator_runtime_fingerprint": "3" * 64,
            "lpips_backbone": "vgg",
        }
        current = dict(saved)
        self.assertEqual(cache_identity_status(saved, current), ("reusable", "cache_identity_matches"))
        for key, expected in (
            ("input_fingerprint", "input_hash_changed"),
            ("numeric_evaluator_fingerprint", "numeric_implementation_changed"),
            ("shared_evaluator_runtime_fingerprint", "critical_dependency_changed"),
            ("lpips_backbone", "lpips_backbone_changed"),
        ):
            changed = dict(current)
            changed[key] = "different"
            self.assertEqual(cache_identity_status(saved, changed)[0], expected)


if __name__ == "__main__":
    unittest.main()
