from __future__ import annotations

import sys
from pathlib import Path

# Monorepo checkout: add sibling package src dirs so `exonware.*` imports resolve without editable installs.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_PKG_ROOT = Path(__file__).resolve().parents[1]
_SIBLING_SRCS = (
    "xwapi",
    "xwnode",
    "xwformats",
    "xwjson",
    "xwschema",
    "xwquery",
    "xwdata",
    "xwentity",
    "xwauth",
    "xwstorage",
    "xwsystem",
    "xwaction",
    "xwai",
    "xwlazy",
)

for _name in _SIBLING_SRCS:
    _src = _REPO_ROOT / _name / "src"
    if _src.is_dir():
        _p = str(_src)
        if _p not in sys.path:
            sys.path.insert(0, _p)

_pkg_src = _PKG_ROOT / "src"
if _pkg_src.is_dir():
    _ps = str(_pkg_src)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)

import pytest
