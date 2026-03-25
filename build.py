"""Build the PyQt6 desktop app with PyInstaller (onedir, windowed)."""

from __future__ import annotations

# Selenium loads several webdriver implementation modules dynamically at runtime.
# PyInstaller static analysis misses those imports, so we pin them with --hidden-import.

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "app" / "desktop" / "main.py"

_SELENIUM_HIDDEN_IMPORTS = [
    "selenium.webdriver.chrome.webdriver",
    "selenium.webdriver.chrome.service",
    "selenium.webdriver.chrome.options",
    "selenium.webdriver.common.by",
    "selenium.webdriver.support.ui",
    "selenium.webdriver.support.expected_conditions",
]


def _rm_tree(path: Path, *, retries: int = 5, delay_sec: float = 0.7) -> None:
    """Remove a directory tree. Retries on Windows when DLLs/PYDs are briefly locked
    (e.g. competitionmonitor.exe or Explorer holding files under dist/).
    """
    if not path.is_dir():
        return
    last_exc: OSError | None = None
    for attempt in range(retries):
        try:
            shutil.rmtree(path)
            return
        except (PermissionError, OSError) as exc:
            last_exc = exc
            if attempt + 1 < retries:
                time.sleep(delay_sec)
    hint = (
        f"Could not remove {path} ({last_exc}). "
        "Close competitionmonitor.exe if it is running, close any File Explorer window "
        "opened inside dist\\, then run build.py again."
    )
    raise PermissionError(hint) from last_exc


def main() -> None:
    _rm_tree(ROOT / "build")
    _rm_tree(ROOT / "dist")
    spec = ROOT / "competitionmonitor.spec"
    if spec.is_file():
        spec.unlink()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "competitionmonitor",
        "--windowed",
        "--onedir",
        "--paths",
        str(ROOT),
        str(ENTRY),
    ]
    for mod in _SELENIUM_HIDDEN_IMPORTS:
        cmd.extend(("--hidden-import", mod))

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=str(ROOT), check=True)


if __name__ == "__main__":
    main()
