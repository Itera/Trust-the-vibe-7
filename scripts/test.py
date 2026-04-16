"""Run backend + frontend test suites. Cross-platform.

Usage:
    python scripts/test.py
    python scripts/test.py --backend-only
    python scripts/test.py --frontend-only
"""
from __future__ import annotations

import argparse
import sys

from _paths import BACKEND_DIR, FRONTEND_DIR, npm_executable, run, venv_python


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-only", action="store_true")
    parser.add_argument("--frontend-only", action="store_true")
    args = parser.parse_args()

    if not args.frontend_only:
        py = venv_python()
        if not py.exists():
            print(
                "error: backend venv not found. Run `python scripts/setup.py` first.",
                file=sys.stderr,
            )
            return 1
        run([py, "-m", "pytest"], cwd=BACKEND_DIR)

    if not args.backend_only:
        run([npm_executable(), "test"], cwd=FRONTEND_DIR)

    print("\n✓ all tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
