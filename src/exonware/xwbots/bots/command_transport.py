#!/usr/bin/env python3
"""
Parse slash commands and build execution context from provider-attached message data.

Framework-neutral: no chat SDK imports; reads optional ``_message_data`` bags used by
:class:`exonware.xwbots.bots.command_bot.XWBotCommand` message bridges.
"""

from __future__ import annotations

from typing import Any


def parse_slash_command_text(text: str) -> tuple[str | None, list[str]]:
    """
    Split ``text`` into command name (without leading ``/``) and argument tokens.

    Returns ``(None, [])`` when there is no usable command token.
    """
    parts = (text or "").strip().split()
    if not parts:
        return None, []
    cmd = parts[0].lstrip("/")
    if not cmd:
        return None, []
    return cmd, parts[1:]


def command_context_from_message(message: Any) -> dict[str, Any]:
    """
    Populate a command ``context`` dict from ``message._message_data`` when present.

    Keys mirror what :meth:`exonware.xwbots.bots.command_bot.XWBotCommand.handle`
    historically copied from Telegram bridges.
    """
    context: dict[str, Any] = {}
    if not hasattr(message, "_message_data"):
        return context
    data = getattr(message, "_message_data", {}) or {}
    if not isinstance(data, dict):
        return context
    context.setdefault("user_id", data.get("user_id"))
    context.setdefault("chat_id", data.get("chat_id"))
    context.setdefault("username", data.get("username"))
    context.setdefault("help_format", data.get("help_format"))
    for key in (
        "group",
        "channel",
        "mentioned",
        "chat_type",
        "chat_title",
        "first_name",
    ):
        if key in data and data[key] is not None:
            context.setdefault(key, data[key])
    return context
