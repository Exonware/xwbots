#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/bots/ui_actions.py
Framework ``@XWAction`` wrappers for /help, /users, and /roles so they flow through the same
observed-action path as API agents. Handlers snapshotted before observation are delegated to.
Company: eXonware.com
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from exonware.xwaction import ActionProfile, XWAction

from ..contracts import IMessage


async def _call_prior(
    handler: Callable[..., Any],
    message: IMessage,
    context: dict[str, Any],
) -> Any:
    if asyncio.iscoroutinefunction(handler):
        return await handler(message, context)
    return await asyncio.to_thread(handler, message, context)


class XWBotUiAgent:
    """Re-exposes core UI commands as ``@XWAction`` for ``XWBotCommand.observe_api_agent``."""

    _name = "xwbots_ui"

    def __init__(self, bot: Any, prior_handlers: dict[str, Callable[..., Any] | None]) -> None:
        self._bot = bot
        self._prior = prior_handlers

    def get_actions(self) -> list[Any]:
        return [self.help, self.users, self.roles]

    @XWAction(
        operationId="xwbots.help",
        api_name="help",
        cmd_shortcut="help",
        summary="Show bot help and available commands",
        profile=ActionProfile.COMMAND,
        tags=["xwbots", "ui"],
        roles=None,
        audit=False,
    )
    async def help(self, message: IMessage, context: dict[str, Any]) -> Any:
        h = self._prior.get("help")
        if h is None:
            return await self._bot._cmd_help(message, context)
        return await _call_prior(h, message, context)

    @XWAction(
        operationId="xwbots.users",
        api_name="users",
        cmd_shortcut="users",
        summary="Users administration when enabled by the host bot",
        profile=ActionProfile.COMMAND,
        tags=["xwbots", "ui"],
        roles=None,
        audit=True,
    )
    async def users(self, message: IMessage, context: dict[str, Any]) -> Any:
        h = self._prior.get("users")
        if h is None:
            return "The /users command is not enabled on this bot."
        return await _call_prior(h, message, context)

    @XWAction(
        operationId="xwbots.roles",
        api_name="roles",
        cmd_shortcut="roles",
        summary="Roles administration when enabled by the host bot",
        profile=ActionProfile.COMMAND,
        tags=["xwbots", "ui"],
        roles=None,
        audit=True,
    )
    async def roles(self, message: IMessage, context: dict[str, Any]) -> Any:
        h = self._prior.get("roles")
        if h is None:
            return "The /roles command is not enabled on this bot."
        return await _call_prior(h, message, context)
