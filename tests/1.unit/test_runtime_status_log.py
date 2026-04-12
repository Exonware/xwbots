#!/usr/bin/env python3
"""
#exonware/xwbots/tests/1.unit/test_runtime_status_log.py
Tests for RuntimeStatusLog JSONL (command/args fields, tail).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from exonware.xwbots.runtime_status_log import RuntimeStatusLog


@pytest.mark.asyncio
async def test_append_writes_command_args_before_message(tmp_path: Path) -> None:
    root = tmp_path / "agent"
    log = RuntimeStatusLog(root)
    await log.append("queued", "inbound_queued_while_paused", command="roles", args="scout", user_id="7")
    text = log.path.read_text(encoding="utf-8")
    line = text.strip().splitlines()[0]
    data = json.loads(line)
    keys = list(data.keys())
    assert keys[:5] == ["datetime", "status", "command", "args", "message"]
    assert data["status"] == "queued"
    assert data["command"] == "roles"
    assert data["args"] == "scout"
    assert data["message"] == "inbound_queued_while_paused"
    assert data["user_id"] == "7"


@pytest.mark.asyncio
async def test_tail_text_returns_last_n_lines(tmp_path: Path) -> None:
    root = tmp_path / "agent2"
    log = RuntimeStatusLog(root)
    for i in range(5):
        await log.append("tick", f"m{i}", command="", args=str(i))
    out = await log.tail_text(3)
    lines = [json.loads(x)["message"] for x in out.splitlines() if x.strip()]
    assert lines == ["m2", "m3", "m4"]


@pytest.mark.asyncio
async def test_append_accepts_extra_fields(tmp_path: Path) -> None:
    root = tmp_path / "agent3"
    log = RuntimeStatusLog(root)
    await log.append("resumed", "operator_resume", command="resume", args="", operator_user_id="900")
    data = json.loads(log.path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert data["operator_user_id"] == "900"
