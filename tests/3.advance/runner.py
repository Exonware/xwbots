#!/usr/bin/env python3
"""
#exonware/xwbots/tests/3.advance/runner.py
Runner for advance tests (3.advance layer).
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
    """Run advance tests."""
    test_dir = Path(__file__).parent
    root_dir = test_dir.parent.parent
    # Run pytest for this layer
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
        "-x",
        "--strict-markers",
        "-m", "xwbots_advance"
    ]
    result = subprocess.run(cmd, cwd=root_dir)
    sys.exit(result.returncode)
if __name__ == "__main__":
    main()
