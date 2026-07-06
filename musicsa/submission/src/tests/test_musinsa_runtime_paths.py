import sys
import tempfile
import unittest
from pathlib import Path

from scripts import musinsa_runtime_paths as runtime_paths


class MusinsaRuntimePathsTest(unittest.TestCase):
    def setUp(self):
        # Make sure no test leaks a frozen state into another test.
        self._had_frozen = hasattr(sys, "frozen")
        self._orig_frozen = getattr(sys, "frozen", None)
        self._had_meipass = hasattr(sys, "_MEIPASS")
        self._orig_meipass = getattr(sys, "_MEIPASS", None)
        self._orig_executable = sys.executable

    def tearDown(self):
        if self._had_frozen:
            sys.frozen = self._orig_frozen
        elif hasattr(sys, "frozen"):
            del sys.frozen
        if self._had_meipass:
            sys._MEIPASS = self._orig_meipass
        elif hasattr(sys, "_MEIPASS"):
            del sys._MEIPASS
        sys.executable = self._orig_executable

    def test_not_frozen_reports_false(self):
        if hasattr(sys, "frozen"):
            del sys.frozen
        self.assertFalse(runtime_paths.is_frozen())

    def test_not_frozen_uses_src_root_for_both_roots(self):
        if hasattr(sys, "frozen"):
            del sys.frozen
        self.assertEqual(runtime_paths.bundle_root(), runtime_paths.SRC_ROOT)
        self.assertEqual(runtime_paths.app_data_root(), runtime_paths.SRC_ROOT)

    def test_resource_path_joins_bundle_root(self):
        if hasattr(sys, "frozen"):
            del sys.frozen
        expected = runtime_paths.SRC_ROOT / "config" / "scoring_weights.json"
        self.assertEqual(runtime_paths.resource_path("config", "scoring_weights.json"), expected)

    def test_frozen_bundle_root_uses_meipass(self):
        sys.frozen = True
        with tempfile.TemporaryDirectory() as meipass_dir:
            sys._MEIPASS = meipass_dir
            self.assertEqual(runtime_paths.bundle_root(), Path(meipass_dir))

    def test_frozen_app_data_root_uses_executable_dir(self):
        sys.frozen = True
        with tempfile.TemporaryDirectory() as exe_dir:
            sys.executable = str(Path(exe_dir) / "MusinsaBuyerApp.exe")
            # Compare against a resolved path on both sides: on Windows,
            # Path.resolve() can normalize a temp dir to its short (8.3)
            # alias (e.g. HAMCOD~1), so comparing to the raw exe_dir string
            # is flaky depending on OS path-resolution quirks unrelated to
            # the behavior under test.
            self.assertEqual(runtime_paths.app_data_root(), Path(exe_dir).resolve())

    def test_writable_path_seeds_from_bundled_default_on_first_use(self):
        sys.frozen = True
        with tempfile.TemporaryDirectory() as meipass_dir, tempfile.TemporaryDirectory() as exe_dir:
            sys._MEIPASS = meipass_dir
            sys.executable = str(Path(exe_dir) / "MusinsaBuyerApp.exe")

            seed_dir = Path(meipass_dir) / "config"
            seed_dir.mkdir(parents=True, exist_ok=True)
            seed_file = seed_dir / "keyword_learning_queue.json"
            seed_file.write_text('{"terms": []}', encoding="utf-8")

            target = runtime_paths.writable_path("config", "keyword_learning_queue.json")

            self.assertEqual(target, Path(exe_dir).resolve() / "config" / "keyword_learning_queue.json")
            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), '{"terms": []}')

    def test_writable_path_does_not_reseed_once_present(self):
        sys.frozen = True
        with tempfile.TemporaryDirectory() as meipass_dir, tempfile.TemporaryDirectory() as exe_dir:
            sys._MEIPASS = meipass_dir
            sys.executable = str(Path(exe_dir) / "MusinsaBuyerApp.exe")

            seed_dir = Path(meipass_dir) / "config"
            seed_dir.mkdir(parents=True, exist_ok=True)
            (seed_dir / "keyword_learning_queue.json").write_text('{"terms": []}', encoding="utf-8")

            existing_dir = Path(exe_dir) / "config"
            existing_dir.mkdir(parents=True, exist_ok=True)
            existing_file = existing_dir / "keyword_learning_queue.json"
            existing_file.write_text('{"terms": ["already_learned"]}', encoding="utf-8")

            target = runtime_paths.writable_path("config", "keyword_learning_queue.json")

            self.assertEqual(target.read_text(encoding="utf-8"), '{"terms": ["already_learned"]}')


if __name__ == "__main__":
    unittest.main()
