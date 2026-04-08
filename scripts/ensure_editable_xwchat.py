#!/usr/bin/env python3
"""
Ensure xwchat is installed in editable mode in the current environment.
Run from exonware repo root or from xwbots directory when xwchat is a sibling.

  From repo root:  python xwbots/scripts/ensure_editable_xwchat.py
  From xwbots:     python scripts/ensure_editable_xwchat.py

XWBots uses xwchat for Telegram; editable install lets you change xwchat without reinstalling.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def find_xwchat() -> Path | None:
    # Run from repo root (exonware) or from xwbots
    cwd = Path.cwd()
    candidates = [
        cwd / "xwchat",
        cwd.parent / "xwchat",  # when cwd is xwbots
    ]
    for p in candidates:
        if (p / "pyproject.toml").exists():
            return p
    return None


def main() -> int:
    xwchat_dir = find_xwchat()
    if not xwchat_dir:
        print("xwchat not found as sibling (no xwchat/pyproject.toml).", file=sys.stderr)
        print("Run from exonware repo root or from xwbots directory.", file=sys.stderr)
        return 1
    cmd = [sys.executable, "-m", "pip", "install", "-e", f"{xwchat_dir}[full]"]
    print("Installing xwchat in editable mode:", " ".join(cmd))
    r = subprocess.run(cmd)
    return 0 if r.returncode == 0 else r.returncode


if __name__ == "__main__":
    sys.exit(main())
