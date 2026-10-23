"""Tests for the dependency-free, cached-asset runtime builder."""
import importlib.util
import json
from pathlib import Path
import unittest

WEB = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_runtime", WEB / "build_runtime.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class RuntimeBuildTests(unittest.TestCase):
    def setUp(self):
        self.data = {"level": "wizard", "levels": {}, "world_of": {}, "atlas": "pixels", "pip": "pixels"}
        self.asset = "window.ASSETS = " + json.dumps(self.data) + ";"
        self.cache = '<link rel="apple-touch-icon" href="data:image/png;base64,abc"><script>\n' + self.asset + '\n</script><script>old();</script>'
        self.template = '<link rel="apple-touch-icon" href="/*ICON*/"><link rel="icon" href="/*ICON*/"><script>/*ASSETS*/</script><script>/*GAME*/</script>'

    def test_replaces_runtime_without_changing_assets(self):
        result = BUILDER.render_runtime(self.cache, self.template, "newGame();")
        self.assertIn(self.asset, result)
        self.assertEqual(result.count("data:image/png;base64,abc"), 2)
        self.assertIn("newGame();", result)
        self.assertNotIn("old();", result)

    def test_rejects_missing_asset_cache(self):
        with self.assertRaises(ValueError):
            BUILDER.render_runtime("", self.template, "")

    def test_rejects_duplicate_asset_blocks(self):
        with self.assertRaises(ValueError):
            BUILDER.render_runtime(self.cache + '<script>' + self.asset + '</script>', self.template, "")

    def test_rejects_executable_asset_payload(self):
        with self.assertRaises(ValueError):
            BUILDER.render_runtime(self.cache.replace(json.dumps(self.data), 'stealData()'), self.template, "")

    def test_rejects_missing_icon(self):
        with self.assertRaises(ValueError):
            BUILDER.render_runtime(self.cache.replace('apple-touch-icon', 'not-an-icon'), self.template, "")

    def test_rejects_incomplete_asset_payload(self):
        with self.assertRaises(ValueError):
            BUILDER.render_runtime(self.cache.replace(json.dumps(self.data), '{}'), self.template, "")

    def test_rejects_changed_template_markers(self):
        with self.assertRaises(ValueError):
            BUILDER.render_runtime(self.cache, self.template.replace('/*GAME*/', ''), "")

    def test_actual_output_matches_source(self):
        cached = (WEB / 'index.html').read_text()
        result = BUILDER.render_runtime(cached, (WEB / 'src/index.template.html').read_text(), (WEB / 'src/game.js').read_text())
        self.assertEqual(result, cached)


if __name__ == '__main__':
    unittest.main()
