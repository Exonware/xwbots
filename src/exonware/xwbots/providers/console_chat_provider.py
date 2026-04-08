#!/usr/bin/env python3
"""
Console Chat Provider (Chat Provider Emulator).

A chat provider that runs in the terminal for testing bot commands without
connecting to Telegram, Discord, etc. Simulates the message flow: prompts for
input, invokes the bot handler, and prints the response.

When exonware-xwchat is available, uses TelegramChatProvider.prepare_response_for_send
to emulate exactly what would be sent to Telegram (parse_mode, sanitization),
so you can verify /help, /roles, etc. will not cause "Can't parse entities" errors.

Usage:
  from exonware.xwbots import XWBotCommand
  from exonware.xwbots.providers import ConsoleChatProvider

  bot = YourBot()
  provider = ConsoleChatProvider(username="muhdashe")
  bot.add_chat_provider(provider, "default")
  import asyncio
  asyncio.run(bot.run())

Or run the module directly with a bot class:
  python -m exonware.xwbots.providers.console_chat_provider karizma_assistant_bot.KarizmaAssistantBot
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Callable, Optional

from exonware.xwsystem import get_logger

logger = get_logger(__name__)


def _get_telegram_prepare_response():
    """Return Telegram's prepare_response_for_send when xwchat is available."""
    try:
        from exonware.xwchat import TelegramChatProvider
        provider = TelegramChatProvider(api_token="CONSOLE_EMULATOR")
        return provider.prepare_response_for_send
    except ImportError:
        return None


class ConsoleChatProvider:
    """
    Chat provider emulator that runs in the console.
    Reads commands from stdin, invokes the bot handler, prints the response.
    """

    def __init__(
        self,
        username: str = "testuser",
        user_id: str = "123456789",
        chat_id: str = "123456789",
        prompt: str = "> ",
        emulate_telegram: bool = True,
    ):
        """
        Args:
            username: Simulated Telegram username (e.g. "muhdashe").
            user_id: Simulated user ID.
            chat_id: Simulated chat ID.
            prompt: Input prompt string.
            emulate_telegram: When True and xwchat available, use Telegram's
                prepare_response_for_send to simulate what would be sent
                (catches parse errors before real Telegram).
        """
        self._username = username
        self._user_id = user_id
        self._chat_id = chat_id
        self._prompt = prompt
        self._emulate_telegram = emulate_telegram
        self._message_handler: Optional[Callable[[dict], Any]] = None
        self._prepare_response = _get_telegram_prepare_response() if emulate_telegram else None
        self._listening = False

    def set_message_handler(self, handler: Callable[[dict], Any]) -> None:
        """Set the handler(ctx) -> response. Same interface as xwchat providers."""
        self._message_handler = handler

    def invoke_message_handler(self, ctx: dict[str, Any]) -> Any:
        """Invoke the set handler with ctx."""
        if self._message_handler is None:
            return None
        return self._message_handler(ctx)

    def prepare_response_for_send(self, response: Any) -> tuple[Optional[str], Optional[str], dict[str, Any]]:
        """
        Normalize response and optionally emulate Telegram formatting.
        Returns (text, reply_to_id, send_kwargs).
        """
        if response is None:
            return (None, None, {})
        if isinstance(response, tuple):
            text = response[0]
            reply_to = response[1] if len(response) > 1 else None
            kwargs = response[2] if len(response) > 2 else {}
            if kwargs.get("parse_mode") is not None:
                return (text, reply_to, kwargs)
        else:
            text = response
            reply_to = None
            kwargs = {}
        if self._prepare_response is not None and text:
            return self._prepare_response(response)
        return (text, reply_to, kwargs)

    def _build_ctx(self, text: str) -> dict[str, Any]:
        """Build a MessageContext like Telegram would provide."""
        return {
            "chat_id": self._chat_id,
            "user_id": self._user_id,
            "text": text.strip(),
            "message_id": str(hash(text) % 10**9),
            "username": self._username,
            "group": False,
            "channel": False,
            "mentioned": True,
            "channel_id": self._chat_id,
            "group_id": "",
            "help_format": "markdown",
        }

    async def start_listening(self) -> None:
        """
        Run the console loop: read input, invoke handler, print response.
        Use with bot.run() - the bot will call this and block here.
        """
        self._listening = True
        print("Console Chat Provider (emulator)")
        print(f"  User: @{self._username} (id={self._user_id})")
        print(f"  Emulate Telegram: {self._prepare_response is not None}")
        print("  Enter commands (e.g. /help, /roles). Empty line or Ctrl+C to stop.\n")
        while self._listening:
            try:
                line = await asyncio.to_thread(input, self._prompt)
            except EOFError:
                break
            text = (line or "").strip()
            if not text:
                continue
            if text.lower() in ("exit", "quit", "q"):
                print("Exiting.")
                break
            ctx = self._build_ctx(text)
            try:
                response = self.invoke_message_handler(ctx)
                if asyncio.iscoroutine(response):
                    response = await response
                text_out, reply_to, kwargs = self.prepare_response_for_send(response)
                if text_out:
                    print("\n--- Response ---")
                    print(f"parse_mode: {kwargs.get('parse_mode', '(none)')}")
                    print("-" * 40)
                    try:
                        print(text_out)
                    except UnicodeEncodeError:
                        # Windows console may not support emoji; use ASCII-safe output
                        print(text_out.encode("ascii", errors="replace").decode("ascii"))
                    print("-" * 40)
                else:
                    print("(no response)")
            except Exception as e:
                logger.exception("Error handling command")
                print(f"\nError: {e}\n")
        self._listening = False
        print("Stopped.")

    def stop(self) -> None:
        """Stop the listening loop."""
        self._listening = False


async def _run_with_bot(bot_class: str, **bot_kwargs: Any) -> None:
    """Instantiate a bot by class path and run with ConsoleChatProvider."""
    modname, clsname = bot_class.rsplit(".", 1)
    mod = __import__(modname, fromlist=[clsname])
    BotClass = getattr(mod, clsname)
    bot = BotClass(**bot_kwargs)
    provider = ConsoleChatProvider(username="muhdashe", user_id="777777000")
    bot.add_chat_provider(provider, "default")
    await bot.run()


def main() -> None:
    """Entry point for `python -m exonware.xwbots.providers.console_chat_provider`."""
    bot_class = sys.argv[1] if len(sys.argv) > 1 else None
    if bot_class:
        asyncio.run(_run_with_bot(bot_class))
    else:
        print("Usage: python -m exonware.xwbots.providers.console_chat_provider <bot_module.BotClass>")
        print("Example: python -m exonware.xwbots.providers.console_chat_provider karizma_assistant_bot.KarizmaAssistantBot")
        sys.exit(1)


if __name__ == "__main__":
    main()
