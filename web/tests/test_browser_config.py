"""Browser selection tests only: these never start or install a browser."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("browser_config", Path(__file__).resolve().parents[1] / "browser_config.py")
CONFIG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIG)


class BrowserConfigTests(unittest.TestCase):
    def test_explicit_browser_wins(self):
        with patch.dict(os.environ, {"CHROME_BINARY": "/custom/chrome"}), patch.object(CONFIG.shutil, "which", return_value="/custom/chrome") as lookup:
            self.assertEqual(CONFIG.browser_executable("/bundled/chrome"), "/custom/chrome")
            lookup.assert_called_once_with("/custom/chrome")

    def test_invalid_explicit_browser_does_not_silently_fallback(self):
        with patch.dict(os.environ, {"CHROME_BINARY": "/missing/chrome"}), patch.object(CONFIG.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "CHROME_BINARY"):
                CONFIG.browser_executable("/bundled/chrome")

    def test_system_chrome_has_priority(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(CONFIG.shutil, "which", side_effect=lambda name: "/usr/bin/" + name):
            self.assertEqual(CONFIG.browser_executable(None), "/usr/bin/google-chrome")

    def test_system_chromium_fallback(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(CONFIG.shutil, "which", side_effect=lambda name: "/usr/bin/chromium" if name == "chromium" else None):
            self.assertEqual(CONFIG.browser_executable(None), "/usr/bin/chromium")

    def test_existing_executable_playwright_cache_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "chrome"
            binary.write_text("fixture, never executed")
            binary.chmod(0o700)
            with patch.dict(os.environ, {}, clear=True), patch.object(CONFIG.shutil, "which", return_value=None):
                self.assertEqual(CONFIG.browser_executable(binary), str(binary))

    def test_nonexecutable_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "chrome"
            binary.write_text("fixture")
            binary.chmod(0o600)
            with patch.dict(os.environ, {}, clear=True), patch.object(CONFIG.shutil, "which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "No installed Chromium"):
                    CONFIG.browser_executable(binary)

    def test_missing_browser_has_actionable_error(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(CONFIG.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "does not download"):
                CONFIG.browser_executable(None)


if __name__ == "__main__":
    unittest.main()
