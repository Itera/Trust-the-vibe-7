"""Start the FastAPI server (which also serves the built frontend).

Usage:
    python scripts/start.py                 # serves on http://127.0.0.1:8000
    python scripts/start.py --port 9000
    python scripts/start.py --host 0.0.0.0 --reload
"""
from __future__ import annotations

import argparse
import sys

from _paths import BACKEND_DIR, FRONTEND_DIR, run, venv_python


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    py = venv_python()
    if not py.exists():
        print(
            "error: backend venv not found. Run `python scripts/setup.py` first.",
            file=sys.stderr,
        )
        return 1

    if not (FRONTEND_DIR / "dist" / "index.html").exists():
        print(
            "warning: frontend/dist not built — backend will serve a placeholder "
            "at /. Run `python scripts/setup.py` to build the UI.",
            file=sys.stderr,
        )

    cmd: list[str] = [
        str(py),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.reload:
        cmd.append("--reload")

    run(cmd, cwd=BACKEND_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
