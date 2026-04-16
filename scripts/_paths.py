"""Shared path + command helpers for the bootstrap/start scripts.

Kept stdlib-only so it can run before any dependencies are installed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
VENV_DIR = BACKEND_DIR / ".venv"

IS_WINDOWS = os.name == "nt"


def venv_python() -> Path:
    """Path to the python executable inside the backend venv."""
    if IS_WINDOWS:
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def npm_executable() -> str:
    """Find the npm binary; on Windows it's npm.cmd."""
    candidates = ["npm.cmd", "npm"] if IS_WINDOWS else ["npm"]
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    print(
        "error: could not find `npm` on PATH. Install Node 18+ from https://nodejs.org",
        file=sys.stderr,
    )
    sys.exit(1)


def run(cmd: list[str | Path], *, cwd: Path | None = None) -> None:
    """Run a subprocess, streaming output, and exit on failure."""
    printable = " ".join(str(c) for c in cmd)
    print(f"\n$ {printable}" + (f"   (in {cwd})" if cwd else ""))
    result = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)
