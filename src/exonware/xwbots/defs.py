#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/defs.py
Type definitions and enums for xwbots.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.11
Generation Date: 07-Jan-2025
"""

from enum import Enum
from typing import Any


class BotStatus(Enum):
    """Bot status types."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    CRASHED = "crashed"


class BotType(Enum):
    """Bot type classification."""
    COMMAND = "command"      # Command-based bot (structured commands)
    PERSONA = "persona"     # Conversational bot (natural language + personality)
    AGENTIC = "agentic"     # Autonomous agent bot (decision-making + orchestration)


class PlatformType(Enum):
    """Platform types."""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    CUSTOM = "custom"


class CommandType(Enum):
    """Command types."""
    TEXT = "text"
    CALLBACK = "callback"
    INLINE = "inline"


class MessageType(Enum):
    """Message types."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
