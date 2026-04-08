#!/usr/bin/env python3
"""
#exonware/xwbots/tests/0.core/test_core_facade.py
Core facade tests for xwbots.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 07-Jan-2025
"""

import pytest
from exonware.xwbots import XWBot
from exonware.xwbots.defs import BotStatus
@pytest.mark.xwbots_core

class TestCoreFacade:
    """Test core facade functionality."""

    def test_xwbot_initialization(self):
        """Test that XWBot can be initialized."""
        # Create a mock platform
        class MockPlatform:
            @property
            def platform_type(self):
                from exonware.xwbots.defs import PlatformType
                return PlatformType.TELEGRAM
        platform = MockPlatform()
        bot = XWBot(platform=platform, name="test_bot")
        assert bot is not None
        assert bot.status == BotStatus.STOPPED

    def test_xwbot_config(self):
        """Test XWBot configuration."""
        class MockPlatform:
            @property
            def platform_type(self):
                from exonware.xwbots.defs import PlatformType
                return PlatformType.TELEGRAM
        platform = MockPlatform()
        bot = XWBot(platform=platform, name="test_bot", enable_crash_recovery=True)
        assert bot._config.name == "test_bot"
        assert bot._config.enable_crash_recovery is True
