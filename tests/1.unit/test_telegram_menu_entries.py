"""telegram_command_menu_entries role filtering + operator extras."""

from __future__ import annotations

import asyncio

import pytest

from exonware.xwbots.bots.command_bot import XWBotCommand


@pytest.mark.asyncio
async def test_menu_entries_respects_roles_and_operator_extras() -> None:
    bot = XWBotCommand(name="t")
    await bot.start()
    bot.register_command("owner_thing", lambda m, c: "x", roles=["owner"])
    bot.register_command("public_thing", lambda m, c: "y", roles=None)

    pub = bot.telegram_command_menu_entries(user_roles=[], is_telegram_operator=False)
    names = [c for c, _ in pub]
    assert "help" in names and "public_thing" in names
    assert "owner_thing" not in names

    owner = bot.telegram_command_menu_entries(user_roles=["owner"], is_telegram_operator=False)
    assert any(c == "owner_thing" for c, _ in owner)

    op = bot.telegram_command_menu_entries(user_roles=[], is_telegram_operator=True)
    op_cmds = {c for c, _ in op}
    assert "pause" in op_cmds and "restart" in op_cmds
