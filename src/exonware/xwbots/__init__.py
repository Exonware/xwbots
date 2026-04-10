#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/__init__.py
XWBots Package Initialization
This module provides multi-platform bot framework for the eXonware ecosystem.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 07-Jan-2025
"""
# =============================================================================
# XWLAZY INTEGRATION - Auto-install missing dependencies silently (EARLY)
# =============================================================================
# Activate xwlazy BEFORE other imports to enable auto-installation of missing dependencies
# This enables silent auto-installation of missing libraries when they are imported

try:
    from exonware.xwlazy import auto_enable_lazy
    auto_enable_lazy(__package__ or "exonware.xwbots", mode="smart")
except ImportError:
    # xwlazy not installed - lazy mode simply stays disabled (normal behavior)
    pass
from .version import __version__, __author__, __email__
# Standard imports - NO try/except!
from exonware.xwsystem import get_logger
# Ecosystem imports were unused here and forced loading optional packages (xwstorage, etc.)
# Import from exonware.xwaction / xwentity / … directly where needed.
# Core exports
from .facade import XWBot
from .contracts import (
    IBot, IBotCommand, IBotPersona, IBotAgentic,
    IPlatform, ICommand, IMessage, ICommandHandler, ICommandProvider
)
from .base import (
    ABot, ABotCommand, ABotPersona, ABotAgentic,
    ACommandProvider,
    APlatform, ACommand, AMessage, ACommandHandler
)
from .bots.command_bot import XWBotCommand
from .bots.persona_bot import XWBotPersona
from .bots.agentic_bot import XWBotAgentic
from .defs import (
    BotStatus, BotType, PlatformType, CommandType, MessageType
)
from .errors import (
    XWBotsError, XWBotError, XWPlatformError, XWCommandError, XWMessageError
)
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Main classes
    "XWBot",
    "XWBotCommand",
    "XWBotPersona",
    "XWBotAgentic",
    # Interfaces
    "IBot",
    "IBotCommand",
    "IBotPersona",
    "IBotAgentic",
    "IPlatform",
    "ICommand",
    "IMessage",
    "ICommandHandler",
    "ICommandProvider",
    # Abstract classes
    "ABot",
    "ABotCommand",
    "ABotPersona",
    "ABotAgentic",
    "ACommandProvider",
    "APlatform",
    "ACommand",
    "AMessage",
    "ACommandHandler",
    # Definitions
    "BotStatus",
    "BotType",
    "PlatformType",
    "CommandType",
    "MessageType",
    # Errors
    "XWBotsError",
    "XWBotError",
    "XWPlatformError",
    "XWCommandError",
    "XWMessageError",
]
