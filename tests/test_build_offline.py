"""Offline builder protection regression tests. Fixtures never touch production assets."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BUILDER = Path(__file__).resolve().parents[1] / "scripts" / "build-offline.py"
VALID_HTML = "<!doctype html><html><head><title>Fixture</title></head><body>OK</body></html>"


class OfflineBuilderSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "site"
        (self.root / "scripts").mkdir(parents=True)
        shutil.copy2(BUILDER, self.root / "scripts" / "build-offline.py")
        (self.root / "scripts" / "offline-worker-template.js").write_text(
            "const CONFIG = /* OFFLINE_CONFIG */;\n", encoding="utf-8"
        )
        (self.root / "offline-settings.json").write_text(
            json.dumps({"app": "fixture", "limits": "Offline fixture only"}),
            encoding="utf-8",
        )

    def run_builder(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / "build-offline.py"), *args],
            cwd=self.root, text=True, capture_output=True, check=False,
        )

    def test_valid_bundle_can_be_generated_and_checked_without_changes(self):
        (self.root / "index.html").write_text(VALID_HTML, encoding="utf-8")
        generated = self.run_builder()
        self.assertEqual(generated.returncode, 0, generated.stderr)
        html = (self.root / "index.html").read_text(encoding="utf-8")
        self.assertIn("data-offline-client", html)
        worker = (self.root / "sw.js").read_text(encoding="utf-8")
        manifest = (self.root / "offline-assets.json").read_text(encoding="utf-8")
        checked = self.run_builder("--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual((self.root / "sw.js").read_text(encoding="utf-8"), worker)
        self.assertEqual((self.root / "offline-assets.json").read_text(encoding="utf-8"), manifest)

    def test_invalid_later_page_does_not_partially_mutate_prior_pages(self):
        (self.root / "a.html").write_text(VALID_HTML, encoding="utf-8")
        (self.root / "z.html").write_text("<html><body>Missing head close</body></html>", encoding="utf-8")
        before = (self.root / "a.html").read_bytes()
        result = self.run_builder()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing </head>", result.stderr)
        self.assertEqual((self.root / "a.html").read_bytes(), before)
        self.assertFalse((self.root / "sw.js").exists())
        self.assertFalse((self.root / "offline-assets.json").exists())

    def test_symlinked_public_asset_is_rejected_not_published(self):
        (self.root / "index.html").write_text(VALID_HTML, encoding="utf-8")
        outside = Path(self.temp.name) / "outside-private.txt"
        outside.write_text("private fixture", encoding="utf-8")
        (self.root / "exposed.txt").symlink_to(outside)
        result = self.run_builder()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsafe symlinked public asset", result.stderr)
        self.assertFalse((self.root / "sw.js").exists())
        self.assertFalse((self.root / "offline-assets.json").exists())

    def test_read_only_check_detects_stale_output(self):
        (self.root / "index.html").write_text(VALID_HTML, encoding="utf-8")
        self.assertEqual(self.run_builder().returncode, 0)
        worker = (self.root / "sw.js").read_bytes()
        (self.root / "index.html").write_text(
            (self.root / "index.html").read_text(encoding="utf-8") + "<!-- changed -->",
            encoding="utf-8",
        )
        result = self.run_builder("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Stale or missing sw.js", result.stderr)
        self.assertEqual((self.root / "sw.js").read_bytes(), worker)


if __name__ == "__main__":
    unittest.main()
