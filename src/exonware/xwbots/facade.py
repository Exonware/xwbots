#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/facade.py
XWBot Facade - Main Public API
This module provides the main public API for xwbots following GUIDE_DEV.md facade pattern.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.2
Generation Date: 07-Jan-2025
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from .base import ABot
from .config import XWBotConfig
from .defs import PlatformType, BotStatus
from .errors import XWBotError
if TYPE_CHECKING:
    from .contracts import IPlatform


class XWBot(ABot):
    """
    Main XWBot class providing multi-platform bot framework.
    This class implements the facade pattern, providing a unified interface
    for bot operations across multiple platforms.
    """

    def __init__(
        self,
        platform: IPlatform,
        name: str,
        api_key: Optional[str] = None,
        enable_crash_recovery: bool = True,
        **options
    ):
        """
        Initialize XWBot.
        Args:
            platform: Platform instance (optional; for Telegram use xwchat directly, see examples)
            name: Bot name
            api_key: Optional API key
            enable_crash_recovery: Enable automatic crash recovery
            **options: Additional configuration options
        """
        self._platform = platform
        self._config = XWBotConfig(
            name=name,
            platform_type=platform.platform_type,
            api_key=api_key,
            enable_crash_recovery=enable_crash_recovery
        )
        # Initialize state
        self._status = BotStatus.STOPPED
        self._storage = None
        self._auth = None
        self._ai = None
        self._command_handler = None

    async def start(self) -> None:
        """Start bot. For Telegram (polling), this runs until the bot is stopped (e.g. Ctrl+C)."""
        import asyncio
        self._status = BotStatus.STARTING
        platform = self._platform
        if hasattr(platform, "run_polling"):
            self._status = BotStatus.RUNNING
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: platform.run_polling(self))
            self._status = BotStatus.STOPPED
        else:
            raise NotImplementedError(
                "Bot start not implemented for this platform. "
                "For Telegram use xwchat's Telegram provider directly (see examples)."
            )

    async def stop(self) -> None:
        """Stop bot. With Telegram polling, process exit (e.g. Ctrl+C) stops the bot."""
        self._status = BotStatus.STOPPING
        # Telegram polling runs in executor; no explicit stop API yet
        self._status = BotStatus.STOPPED

    async def restart(self) -> None:
        """Restart bot."""
        await self.stop()
        await self.start()

    async def health_check(self) -> dict:
        """Check bot health."""
        return {
            "status": self._status.value,
            "name": self._config.name,
            "platform": self._config.platform_type.value,
        }
    @property

    def status(self) -> BotStatus:
        """Get bot status."""
        return self._status
