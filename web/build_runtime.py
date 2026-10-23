"""Rebuild HTML/runtime using the existing generated asset cache, without Blender.

For game.js/template-only changes: python3 web/build_runtime.py [--check]
For model/art changes use render_web_assets.py and build_web.py instead.
This command parses cached JSON as data; it never executes scripts from HTML.
"""
import argparse
import json
from pathlib import Path
import re
import tempfile


HERE = Path(__file__).resolve().parent


def render_runtime(cached_html, template, game_js):
    blocks = re.findall(r"<script\b[^>]*>([\s\S]*?)</script>", cached_html, re.I)
    asset_blocks = [s.strip() for s in blocks if s.strip().startswith("window.ASSETS = ")]
    if len(asset_blocks) != 1 or not asset_blocks[0].endswith(";"):
        raise ValueError("Expected exactly one cached window.ASSETS JSON block")
    assets = asset_blocks[0]
    payload = json.loads(assets[len("window.ASSETS = "):-1])
    if not isinstance(payload, dict) or not {"level", "levels", "world_of", "atlas", "pip"} <= payload.keys():
        raise ValueError("Cached asset payload is incomplete")
    icons = re.findall(r'<link\s+rel="apple-touch-icon"\s+href="([^"]+)"', cached_html)
    if len(icons) != 1 or not icons[0].startswith("data:image/png;base64,"):
        raise ValueError("Expected one cached PNG home-screen icon")
    expected = {"/*ICON*/": 2, "/*ASSETS*/": 1, "/*GAME*/": 1}
    if any(template.count(marker) != count for marker, count in expected.items()):
        raise ValueError("Unexpected template markers; review the full asset build")
    return template.replace("/*ICON*/", icons[0]).replace("/*ASSETS*/", assets).replace("/*GAME*/", game_js)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if index.html is out of sync; do not write")
    args = parser.parse_args()
    target = HERE / "index.html"
    try:
        cached = target.read_text(encoding="utf-8")
        rendered = render_runtime(cached, (HERE / "src/index.template.html").read_text(encoding="utf-8"),
                                  (HERE / "src/game.js").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Runtime rebuild failed: {exc}\n")
    if args.check:
        if rendered != cached:
            parser.exit(1, "index.html is stale. Run python3 web/build_runtime.py\n")
        print("Runtime and template match index.html; cached assets unchanged.")
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=HERE, prefix=".index-", suffix=".tmp", delete=False) as f:
            temporary = Path(f.name)
            f.write(rendered)
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print("Rebuilt web/index.html from source; reused existing art, sound and icon. World packs unchanged.")


if __name__ == "__main__":
    main()
