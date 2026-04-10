#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/config.py
Configuration classes for xwbots.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.4
Generation Date: 07-Jan-2025
"""

from dataclasses import dataclass
from typing import Optional
from .defs import PlatformType
@dataclass

class XWBotConfig:
    """Configuration for XWBot."""
    name: str
    platform_type: PlatformType
    api_key: Optional[str] = None
    enable_crash_recovery: bool = True
    max_restart_attempts: int = 5
    restart_delay_seconds: int = 5
    enable_ai: bool = False
    enable_storage: bool = True
    enable_auth: bool = True
