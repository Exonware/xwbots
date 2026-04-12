#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/bots/__init__.py
Bot implementations package.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.6
"""

from .command_bot import XWBotCommand
from .persona_bot import XWBotPersona
from .agentic_bot import XWBotAgentic
__all__ = [
    "XWBotCommand",
    "XWBotPersona",
    "XWBotAgentic",
]
