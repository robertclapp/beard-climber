"""Select an already-installed Chromium browser; never install or download one."""
import os
from pathlib import Path
import shutil


def browser_executable(bundled_path):
    """Honor an explicit CHROME_BINARY, then system Chrome, then Playwright's cache."""
    explicit = os.environ.get("CHROME_BINARY")
    if explicit:
        candidate = shutil.which(explicit)
        if candidate:
            return candidate
        raise RuntimeError("CHROME_BINARY does not name an executable file: " + explicit)
    for name in ("google-chrome", "chromium", "chromium-browser"):
        candidate = shutil.which(name)
        if candidate:
            return candidate
    if bundled_path and Path(bundled_path).is_file() and os.access(bundled_path, os.X_OK):
        return str(bundled_path)
    raise RuntimeError(
        "No installed Chromium browser found. Set CHROME_BINARY to an existing "
        "Chrome/Chromium executable, or prepare Playwright's browser separately. "
        "This test runner does not download browsers."
    )
