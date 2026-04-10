#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/errors.py
Error classes for xwbots.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 07-Jan-2025
"""


class XWBotsError(Exception):
    """Base error for xwbots."""
    pass


class XWBotError(XWBotsError):
    """Bot-related errors."""
    pass


class XWPlatformError(XWBotsError):
    """Platform-related errors."""
    pass


class XWCommandError(XWBotsError):
    """Command-related errors."""
    pass


class XWMessageError(XWBotsError):
    """Message-related errors."""
    pass
