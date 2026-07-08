import json
import tempfile
import unittest
from pathlib import Path

from scripts.sparse_view_utils import (
    generate_sparse_scene,
    select_frames,
)


def _frame(name, x=0.0, z=0.0):
    return {
        "file_path": f"rgb/{name}",
        "transform_matrix": [
            [1.0, 0.0, 0.0, x],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, z],
            [0.0, 0.0, 0.0, 1.0],
        ],
    }


class SparseViewUtilsTests(unittest.TestCase):
    def test_random_strategy_is_stable_for_same_seed(self):
        frames = [_frame(str(i), x=float(i), z=1.0) for i in range(12)]

        first = select_frames(frames, 4, "random", seed=9)
        second = select_frames(frames, 4, "random", seed=9)

        self.assertEqual(first.indices, second.indices)
        self.assertEqual(first.file_paths, second.file_paths)
        self.assertEqual(first.indices, sorted(first.indices))

    def test_uniform_index_selects_requested_count_in_original_order(self):
        frames = [_frame(str(i), x=float(i), z=1.0) for i in range(10)]

        result = select_frames(frames, 5, "uniform_index", seed=0)

        self.assertEqual(len(result.indices), 5)
        self.assertEqual(result.indices, sorted(result.indices))
        self.assertEqual(result.status, "ok")

    def test_uniform_pose_runs_with_transform_matrix(self):
        frames = [
            _frame("a", x=0.0, z=1.0),
            _frame("b", x=1.0, z=0.0),
            _frame("c", x=0.0, z=-1.0),
            _frame("d", x=-1.0, z=0.0),
        ]

        result = select_frames(frames, 2, "uniform_pose", seed=0)

        self.assertEqual(len(result.indices), 2)
        self.assertEqual(result.status, "ok")

    def test_farthest_pose_does_not_repeat_frames(self):
        frames = [_frame(str(i), x=float(i), z=0.0) for i in range(6)]

        result = select_frames(frames, 4, "farthest_pose", seed=1)

        self.assertEqual(len(result.indices), 4)
        self.assertEqual(len(set(result.indices)), 4)

    def test_not_enough_frames_uses_all_frames_and_records_status(self):
        frames = [_frame(str(i), x=float(i), z=0.0) for i in range(2)]

        result = select_frames(frames, 5, "uniform_index", seed=0)

        self.assertEqual(result.indices, [0, 1])
        self.assertEqual(result.status, "not_enough_frames")

    def test_generate_sparse_scene_preserves_test_json_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            output = root / "out"
            (source / "rgb").mkdir(parents=True)
            train_json = {
                "camera_angle_x": 0.5,
                "fl_x": 100.0,
                "frames": [_frame(str(i), x=float(i), z=0.0) for i in range(4)],
            }
            test_json = {
                "camera_angle_x": 0.5,
                "frames": [_frame("test0", x=0.0, z=1.0), _frame("test1", x=1.0, z=1.0)],
            }
            (source / "transforms_train.json").write_text(json.dumps(train_json, indent=2), encoding="utf-8")
            raw_test = json.dumps(test_json, indent=4)
            (source / "transforms_test.json").write_text(raw_test, encoding="utf-8")

            manifest = generate_sparse_scene(
                dataset="refnerf",
                scene="coffee",
                source_scene=source,
                output_scene=output,
                views=3,
                strategy="uniform_index",
                seed=0,
            )

            self.assertEqual((output / "transforms_test.json").read_text(encoding="utf-8"), raw_test)
            sparse_train = json.loads((output / "transforms_train.json").read_text(encoding="utf-8"))
            self.assertEqual(sparse_train["camera_angle_x"], 0.5)
            self.assertEqual(sparse_train["fl_x"], 100.0)
            self.assertEqual(len(sparse_train["frames"]), 3)
            manifest_json = json.loads((output / "sparse_view_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest_json["selected_file_paths"], manifest["selected_file_paths"])
            self.assertEqual(manifest_json["strategy"], "uniform_index")
            self.assertEqual(manifest_json["seed"], 0)
            self.assertEqual(manifest_json["requested_views"], 3)

    def test_dry_run_does_not_write_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            output = root / "out"
            source.mkdir()
            train_json = {"frames": [_frame(str(i), x=float(i), z=0.0) for i in range(4)]}
            test_json = {"frames": [_frame("test0", x=0.0, z=1.0)]}
            (source / "transforms_train.json").write_text(json.dumps(train_json), encoding="utf-8")
            (source / "transforms_test.json").write_text(json.dumps(test_json), encoding="utf-8")

            manifest = generate_sparse_scene(
                dataset="refnerf",
                scene="coffee",
                source_scene=source,
                output_scene=output,
                views=3,
                strategy="uniform_index",
                seed=0,
                dry_run=True,
            )

            self.assertFalse(output.exists())
            self.assertTrue(manifest["dry_run"])

    def test_generate_sparse_scene_is_idempotent_when_manifest_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            output = root / "out"
            source.mkdir()
            train_json = {"frames": [_frame(str(i), x=float(i), z=0.0) for i in range(4)]}
            test_json = {"frames": [_frame("test0", x=0.0, z=1.0)]}
            (source / "transforms_train.json").write_text(json.dumps(train_json), encoding="utf-8")
            (source / "transforms_test.json").write_text(json.dumps(test_json), encoding="utf-8")

            first = generate_sparse_scene(
                dataset="refnerf",
                scene="coffee",
                source_scene=source,
                output_scene=output,
                views=3,
                strategy="uniform_index",
                seed=0,
            )
            second = generate_sparse_scene(
                dataset="refnerf",
                scene="coffee",
                source_scene=source,
                output_scene=output,
                views=3,
                strategy="uniform_index",
                seed=0,
            )

            self.assertEqual(second["selected_indices"], first["selected_indices"])
            self.assertEqual(second["status"], "ok")


if __name__ == "__main__":
    unittest.main()
