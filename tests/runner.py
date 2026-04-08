#!/usr/bin/env python3
"""
#exonware/xwbots/tests/runner.py
Main test runner for xwbots.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 07-Jan-2025
"""

import sys
import subprocess
from pathlib import Path
# Critical UTF-8 encoding configuration for Windows compatibility
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")


def main():
    """Run all tests."""
    test_dir = Path(__file__).parent
    root_dir = test_dir.parent
    # Run pytest for all layers
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
        "-x",
        "--strict-markers"
    ]
    result = subprocess.run(cmd, cwd=root_dir)
    sys.exit(result.returncode)
if __name__ == "__main__":
    main()
