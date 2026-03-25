"""Build the PyQt6 desktop app with PyInstaller (onedir, windowed)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTRY = ROOT / "app" / "desktop" / "main.py"


def _rm_tree(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)


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
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=str(ROOT), check=True)


if __name__ == "__main__":
    main()
