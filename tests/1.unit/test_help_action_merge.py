"""Merge get_actions() with optional xwapi MRO discovery for /help and observe_api_agent."""

from __future__ import annotations

from exonware.xwbots.bots.command_bot import _merge_xwaction_methods_for_agent


def _fake_action(name: str):
    def fn() -> None:
        return None

    fn.__name__ = name
    fn.xwaction = object()
    return fn


def test_merge_prefers_get_actions_order_and_dedupes_by_name() -> None:
    class _Agent:
        def get_actions(self):
            return [_fake_action("alpha"), _fake_action("beta")]

    merged = _merge_xwaction_methods_for_agent(_Agent())
    names = [getattr(f, "__name__", "") for f in merged]
    assert set(names) == {"alpha", "beta"}
