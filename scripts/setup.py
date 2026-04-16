"""One-shot bootstrap: create venv, install deps, build frontend.

Works on macOS, Linux, and Windows. Run with:

    python scripts/setup.py
"""
from __future__ import annotations

import sys
import venv

from _paths import (
    BACKEND_DIR,
    FRONTEND_DIR,
    VENV_DIR,
    npm_executable,
    run,
    venv_python,
)


def ensure_venv() -> None:
    if venv_python().exists():
        print(f"venv already present at {VENV_DIR}")
        return
    print(f"creating venv at {VENV_DIR}")
    builder = venv.EnvBuilder(with_pip=True, upgrade_deps=True)
    builder.create(VENV_DIR)


def install_backend() -> None:
    py = venv_python()
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-r", BACKEND_DIR / "requirements.txt"])


def install_and_build_frontend() -> None:
    npm = npm_executable()
    run([npm, "install"], cwd=FRONTEND_DIR)
    run([npm, "run", "build"], cwd=FRONTEND_DIR)


def main() -> int:
    if sys.version_info < (3, 10):
        print("error: Python 3.10+ required", file=sys.stderr)
        return 1

    ensure_venv()
    install_backend()
    install_and_build_frontend()

    print("\n✓ setup complete — now run:  python scripts/start.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
