#!/usr/bin/env python3
"""
#exonware/xwbots/tests/0.core/test_core_imports.py
Core import tests for xwbots.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 07-Jan-2025
"""

import pytest
@pytest.mark.xwbots_core

class TestCoreImports:
    """Test core imports."""

    def test_import_xwbots(self):
        """Test that xwbots can be imported."""
        from exonware.xwbots import XWBot
        assert XWBot is not None

    def test_import_contracts(self):
        """Test that contracts can be imported."""
        from exonware.xwbots.contracts import IBot, IPlatform
        assert IBot is not None
        assert IPlatform is not None

    def test_import_errors(self):
        """Test that errors can be imported."""
        from exonware.xwbots.errors import XWBotsError
        assert XWBotsError is not None

    def test_import_defs(self):
        """Test that definitions can be imported."""
        from exonware.xwbots.defs import BotStatus, PlatformType
        assert BotStatus is not None
        assert PlatformType is not None
