#!/usr/bin/env python3

from types import SimpleNamespace

from exonware.xwbots.bots.command_transport import (
    command_context_from_message,
    parse_slash_command_text,
)


def test_parse_slash_command_text() -> None:
    assert parse_slash_command_text("") == (None, [])
    assert parse_slash_command_text("   ") == (None, [])
    assert parse_slash_command_text("/roles") == ("roles", [])
    assert parse_slash_command_text("/users scout admin") == ("users", ["scout", "admin"])


def test_command_context_from_message() -> None:
    msg = SimpleNamespace(
        text="/x",
        _message_data={
            "user_id": "1",
            "chat_id": "2",
            "username": "u",
            "help_format": "telegram_html",
            "chat_type": "supergroup",
            "ignored": None,
        },
    )
    ctx = command_context_from_message(msg)
    assert ctx["user_id"] == "1"
    assert ctx["chat_id"] == "2"
    assert ctx["username"] == "u"
    assert ctx["help_format"] == "telegram_html"
    assert ctx["chat_type"] == "supergroup"
    assert "ignored" not in ctx
