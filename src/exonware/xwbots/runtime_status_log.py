#!/usr/bin/env python3
"""
Runtime / operator status logging for command hosts (xwbots layer).

Writes JSON lines (datetime, status, command, args, message, …) under ``<root>/logs/runtime_status.jsonl``.
Chat transports (e.g. xwchat) should not implement this; they call the optional sinks passed in at wiring time.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RuntimeStatusLog:
    """Append-only JSONL log for host-level status events."""

    def __init__(self, root: str | Path, *, filename: str = "runtime_status.jsonl") -> None:
        self._path = Path(root) / "logs" / filename
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    async def append(
        self,
        status: str,
        message: str,
        *,
        command: str = "",
        args: str = "",
        **extra: Any,
    ) -> None:
        rec: dict[str, Any] = {
            "datetime": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "command": (command or "").strip(),
            "args": (args or "").strip(),
            "message": message,
            **extra,
        }
        line = json.dumps(rec, ensure_ascii=False, default=str) + "\n"

        def _write() -> None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line)

        await asyncio.to_thread(_write)

    async def tail_text(self, max_lines: int) -> str:
        if max_lines < 1:
            max_lines = 1
        if not self._path.exists():
            return ""

        def _read() -> str:
            lines = self._path.read_text(encoding="utf-8", errors="replace").splitlines()
            return "\n".join(lines[-max_lines:])

        return await asyncio.to_thread(_read)
