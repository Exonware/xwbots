#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/bots/command_bot.py
XWBotCommand - Command-based bot implementation.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.5
Generation Date: 07-Jan-2025
"""

import asyncio
import functools
import logging
import re
from types import SimpleNamespace
from typing import Any, Optional, Callable, List, Union
import inspect
from inspect import signature
from datetime import datetime
from exonware.xwsystem import get_logger
from exonware.xwaction import ActionParameter
from ..base import ABotCommand
from ..contracts import IMessage
from ..defs import BotStatus, BotType, MessageType
logger = get_logger(__name__)

# XWAction signature keys filled by the bot/runtime, not by the user in chat.
_HELP_HIDDEN_ACTION_PARAMS = frozenset({"self", "session", "context", "message"})

# Commands that must not be tracked as cancellable work (avoid self-cancel noise).
_CANCEL_SKIP_INFLIGHT_TRACK = frozenset({"cancel", "cancel_all"})

# Log fragments only; never pass session tokens or full context dicts.
_LOG_SKIP_KWARGS = frozenset({"session", "message", "context"})


def _log_truncate(s: str, max_len: int = 280) -> str:
  t = (s or "").replace("\r", " ").replace("\n", " ").strip()
  if len(t) <= max_len:
    return t
  return t[: max_len - 1] + "…"


def _safe_context_for_log(context: dict[str, Any] | None) -> dict[str, Any]:
  """User/chat identifiers for logs (no secrets)."""
  if not context:
    return {}
  out: dict[str, Any] = {}
  for k in (
      "user_id",
      "chat_id",
      "username",
      "telegram_username",
      "chat_type",
      "chat_title",
      "agent_name",
      "help_format",
  ):
    v = context.get(k)
    if v is not None and v != "":
      if k == "chat_title":
        out[k] = _log_truncate(str(v), 120)
      else:
        out[k] = v
  ur = context.get("user_roles")
  if isinstance(ur, list) and ur:
    out["user_roles"] = [_log_truncate(str(x), 64) for x in ur[:16]]
    if len(ur) > 16:
      out["user_roles_truncated"] = len(ur) - 16
  return out


def _safe_action_kwargs_for_log(kwargs: dict[str, Any], max_val: int = 160) -> dict[str, Any]:
  """Action parameters for logs; strips framework-injected objects."""
  out: dict[str, Any] = {}
  for k, v in kwargs.items():
    if k in _LOG_SKIP_KWARGS:
      continue
    if v is None:
      out[k] = None
    elif isinstance(v, (str, int, float, bool)):
      out[k] = _log_truncate(str(v), max_val)
    elif isinstance(v, (list, tuple)):
      out[k] = f"<{type(v).__name__} len={len(v)}>"
    else:
      out[k] = f"<{type(v).__name__}>"
  return out


def _coerce_observed_action_result(value: Any) -> Any:
    """If an action returns a dict with user_report (e.g. revive_auths), surface plain text to chat."""
    if isinstance(value, dict):
        ur = value.get("user_report")
        if isinstance(ur, str) and ur.strip():
            return ur.strip()
    return value


def _message_from_context(ctx: Any) -> IMessage:
    """Build a minimal IMessage from a provider context (dict or object). Used by run()."""
    if isinstance(ctx, dict):
        text = ctx.get("text")
        message_id = ctx.get("message_id") or ""
        chat_id = ctx.get("chat_id") or ""
        data = dict(ctx)
    else:
        text = getattr(ctx, "text", None)
        message_id = getattr(ctx, "message_id", None) or ""
        chat_id = getattr(ctx, "chat_id", None) or ""
        data = getattr(ctx, "__dict__", {})

    async def _reply(_self: Any, reply_text: str, **kwargs: Any) -> None:
        pass

    m = SimpleNamespace(
        text=text,
        message_id=message_id,
        chat_id=chat_id,
        message_type=MessageType.TEXT,
        _message_data=data,
        reply=lambda reply_text: _reply(m, reply_text),
    )
    return m  # type: ignore[return-value]

# Short form: param name (trailing * = required) -> type string
_TYPE_STR_MAP = {
    "string": str,
    "str": str,
    "integer": int,
    "int": int,
    "number": float,
    "float": float,
    "boolean": bool,
    "bool": bool,
    "array": list,
    "list": list,
    "object": dict,
    "dict": dict,
}


def _is_async_callable(obj: Any) -> bool:
    """Return True if obj is an async callable (unwraps bound methods and partials)."""
    while isinstance(obj, functools.partial):
        obj = obj.func
    func = getattr(obj, "__func__", obj)
    return asyncio.iscoroutinefunction(func)


def _type_str_to_type(s: str) -> type:
    """Convert type string to Python type for short parameter form."""
    return _TYPE_STR_MAP.get((s or "string").strip().lower(), str)


# --- Help formatting per provider ---
# Default help uses a *small* markup dialect: *bold*, _italic_, `code` (single asterisks — NOT raw Telegram).
# - telegram_html: converts to <b>, <i>, <code> (Telegram HTML parse_mode).
# - telegram_markdown_v2: converts to **bold**, __italic__, `code` then escapes (Telegram MarkdownV2).
_MARKDOWN_V2_ESCAPE = re.compile(r"([\\_*\[\]()~`>#+=|{}.!-])")
# For plain text only: escape reserved chars that are NOT * or _ (so we don't break **bold** or __italic__)
_MARKDOWN_V2_ESCAPE_PLAIN = re.compile(r"(?<!\\)([\[\]()~`>#+=|{}.!-])")


def _escape_telegram_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2 (so they are literal)."""
    return _MARKDOWN_V2_ESCAPE.sub(r"\\\1", text)


def _escape_html(text: str) -> str:
    """Escape < > & for Telegram HTML parse_mode."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_help_telegram_html(default_help: str) -> str:
    """
    Convert default-format help (*bold*, _italic_, `code`) to Telegram HTML (<b>, <i>, <code>).
    Single * is only our internal delimiter; Telegram HTML does not use asterisks for bold.
    Escapes the whole string first. Protects `code` segments so underscores in command names
    (e.g. rep_broad_day_u) are not turned into <i>, which can cause "expected </b>, found </i>" when nested.
    """
    # Placeholder for code segments so _italic_ doesn't match inside command names
    _CODE_PLACEHOLDER = "\x00CODE\x01"
    _CODE_PLACEHOLDER_END = "\x00CODE\x02"
    parts = []
    rest = default_help
    while True:
        i = rest.find("`")
        if i == -1:
            parts.append((False, rest))
            break
        j = rest.find("`", i + 1)
        if j == -1:
            parts.append((False, rest))
            break
        if i > 0:
            parts.append((False, rest[:i]))
        inner = rest[i + 1 : j]
        parts.append((True, inner))
        rest = rest[j + 1 :]
    # Rebuild: escape non-code, leave code content to be wrapped later
    out_parts = []
    for is_code, segment in parts:
        if is_code:
            out_parts.append(_CODE_PLACEHOLDER + _escape_html(segment) + _CODE_PLACEHOLDER_END)
        else:
            seg = _escape_html(segment)
            seg = re.sub(r"\*([^*]+)\*", lambda m: "<b>" + m.group(1) + "</b>", seg)
            seg = re.sub(r"_([^_]+)_", lambda m: "<i>" + m.group(1) + "</i>", seg)
            out_parts.append(seg)
    out = "".join(out_parts)
    out = out.replace(_CODE_PLACEHOLDER, "<code>").replace(_CODE_PLACEHOLDER_END, "</code>")
    return out


def _format_help_telegram_markdown_v2(default_help: str) -> str:
    """
    Convert default-format help (*bold*, _italic_, `code`) to Telegram MarkdownV2 (**bold**, __italic__, `code`)
    and escape all MarkdownV2 special characters (including in plain text between formatting).
    """

    def replace_bold(m: re.Match) -> str:
        return "**" + _escape_telegram_markdown_v2(m.group(1)) + "**"

    def replace_italic(m: re.Match) -> str:
        return "__" + _escape_telegram_markdown_v2(m.group(1)) + "__"

    def replace_code(m: re.Match) -> str:
        return "`" + _escape_telegram_markdown_v2(m.group(1)) + "`"

    out = re.sub(r"\*([^*]+)\*", replace_bold, default_help)
    out = re.sub(r"_([^_]+)_", replace_italic, out)
    out = re.sub(r"`([^`]+)`", replace_code, out)
    # Escape any remaining special chars in plain text (e.g. "." in "Echo back your message.")
    out = _MARKDOWN_V2_ESCAPE_PLAIN.sub(r"\\\1", out)
    return out


_HELP_FORMATTERS: dict[str, Callable[[str], str]] = {
    "default": lambda s: s,
    "telegram_markdown_v2": _format_help_telegram_markdown_v2,
    "telegram_html": _format_help_telegram_html,
}


def _help_truncate(text: str | None, max_len: int = 160) -> str:
    """Single-line preview for help (keeps Telegram HTML small and readable)."""
    if not text:
        return ""
    one = " ".join((text or "").split())
    if len(one) <= max_len:
        return one
    return one[: max_len - 1] + "…"


def _normalize_parameters(
    parameters: Optional[List[Union[str, ActionParameter, dict[str, str]]]] = None,
) -> List[ActionParameter]:
    """
    Convert parameters to list of ActionParameter. Accepts:
    - ActionParameter: use as-is
    - str: param name only -> ActionParameter(name, str, required=True)
    - dict: short form {param_name: type_str} or {param_name*: type_str} (trailing * = required).
            One dict can have multiple keys, e.g. {"city": "string", "limit": "integer"}.
    """
    if not parameters:
        return []
    out: List[ActionParameter] = []
    for p in parameters:
        if isinstance(p, ActionParameter):
            out.append(p)
        elif isinstance(p, dict):
            for key, type_str in p.items():
                name = key.rstrip("*")
                required = key.endswith("*")
                param_type = _type_str_to_type(type_str) if isinstance(type_str, str) else str
                out.append(ActionParameter(name=name, param_type=param_type, required=required))
        else:
            out.append(ActionParameter(name=str(p), param_type=str, required=True))
    return out


class _CommandsAdapter:
    """Fluent adapter for adding commands. Each add() returns the bot for chaining."""

    def __init__(self, bot: "XWBotCommand") -> None:
        self._bot = bot

    def add(
        self,
        name: str,
        handler: Callable,
        parameters: Optional[List[Union[str, ActionParameter, dict[str, str]]]] = None,
        roles: Optional[List[str]] = None,
    ) -> "XWBotCommand":
        """Register a command and return the bot for chaining. parameters: ActionParameter, str (name only), or short dict form {name: type_str} / {name*: type_str} (* = required)."""
        self._bot.register_command(name, handler, parameters=parameters, roles=roles)
        return self._bot


class _ProvidersAdapter:
    """Fluent adapter for adding providers. chat/auth/storage each support multiple providers via .add()."""

    def __init__(self, bot: "XWBotCommand") -> None:
        self._bot = bot

    def add(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Add a chat provider (backward compat). Prefer bot.providers.chat.add(provider, title)."""
        self._bot.add_chat_provider(provider, title)
        return self._bot

    @property
    def chat(self) -> "_ChatProvidersAdapter":
        """Add chat providers: bot.providers.chat.add(telegram_provider)."""
        return _ChatProvidersAdapter(self._bot)

    @property
    def auth(self) -> "_AuthProvidersAdapter":
        """Add auth providers: bot.providers.auth.add(auth_provider)."""
        return _AuthProvidersAdapter(self._bot)

    @property
    def storage(self) -> "_StorageProvidersAdapter":
        """Add storage providers: bot.providers.storage.add(storage_provider)."""
        return _StorageProvidersAdapter(self._bot)

    @property
    def command(self) -> "_CommandProvidersAdapter":
        """Add command providers: bot.providers.command.add(command_provider). Provider implements register_with(bot)."""
        return _CommandProvidersAdapter(self._bot)


class _ChatProvidersAdapter:
    """Fluent adapter for adding chat providers. add(provider, title='default') returns the bot for chaining."""

    def __init__(self, bot: "XWBotCommand") -> None:
        self._bot = bot

    def add(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Add a chat provider under a title (default title is 'default')."""
        self._bot.add_chat_provider(provider, title)
        return self._bot


class _AuthProvidersAdapter:
    """Fluent adapter for adding auth providers. add(provider, title='default') returns the bot for chaining."""

    def __init__(self, bot: "XWBotCommand") -> None:
        self._bot = bot

    def add(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Add an auth provider under a title (default title is 'default')."""
        self._bot.add_auth_provider(provider, title)
        return self._bot


class _StorageProvidersAdapter:
    """Fluent adapter for adding storage providers. add(provider, title='default') returns the bot for chaining."""

    def __init__(self, bot: "XWBotCommand") -> None:
        self._bot = bot

    def add(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Add a storage provider under a title (default title is 'default')."""
        self._bot.add_storage_provider(provider, title)
        return self._bot


class _CommandProvidersAdapter:
    """Fluent adapter for adding command providers. add(provider, title='default') calls provider.register_with(bot)."""

    def __init__(self, bot: "XWBotCommand") -> None:
        self._bot = bot

    def add(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Add a command provider under a title. Provider should implement register_with(bot)."""
        self._bot.add_command_provider(provider, title)
        return self._bot


class XWBotCommand(ABotCommand):
    """
    Command-based bot implementation.
    Features:
    - Command registration and execution
    - Automatic command generation from XWApiAgent actions
    - Role-based command access
    - Help command auto-generation
    - /cancel (per-user) and /cancel_all (staff) for in-flight asyncio command tasks
    """

    def __init__(self, name: str, platform: Optional[Any] = None):
        """
        Initialize command bot.
        Args:
            name: Bot name
            platform: Optional platform instance (IPlatform)
        """
        super().__init__(name)
        self._platform = platform
        self._start_time: Optional[datetime] = None
        self._help_cache: dict[str, str] = {}
        self._command_parameters: dict[str, List[ActionParameter]] = {}
        # In-flight asyncio tasks per Telegram/chat user (see execute_command + /cancel).
        self._inflight_by_user: dict[str, set[asyncio.Task]] = {}

    def _inflight_user_key(self, context: dict[str, Any]) -> str:
        """Stable key for the caller so /cancel only affects their own work."""
        uid = str(context.get("user_id") or "").strip()
        if uid:
            return f"uid:{uid}"
        un = str(context.get("username") or "").strip().lstrip("@").lower()
        if un:
            return f"u:{un}"
        return "unknown"

    def _register_inflight_command_task(self, command_name: str, context: dict[str, Any]) -> None:
        if command_name in _CANCEL_SKIP_INFLIGHT_TRACK:
            return
        t = asyncio.current_task()
        if t is None:
            return
        key = self._inflight_user_key(context)
        self._inflight_by_user.setdefault(key, set()).add(t)

        def _done(_completed: asyncio.Task) -> None:
            b = self._inflight_by_user.get(key)
            if b is not None:
                b.discard(t)
                if not b:
                    self._inflight_by_user.pop(key, None)

        t.add_done_callback(_done)

    async def start(self) -> None:
        """Start the command bot."""
        if self._status == BotStatus.RUNNING:
            return
        self._status = BotStatus.STARTING
        logger.info(f"Starting command bot: {self._name}")
        # Register default help, start, and status commands
        self.register_command("help", self._cmd_help, roles=None)
        self.register_command("start", self._cmd_help, roles=None)
        self.register_command("status", self._cmd_status, roles=None)
        self.register_command("cancel", self._cmd_cancel, roles=None)
        # cancel_all: sheet must grant owner or management; handler also blocks scouts (unless owner).
        self.register_command(
            "cancel_all",
            self._cmd_cancel_all,
            roles=["owner", "management"],
        )
        self._status = BotStatus.RUNNING
        self._start_time = datetime.utcnow()
        logger.info(f"Command bot '{self._name}' started")

    async def stop(self) -> None:
        """Stop the command bot."""
        if self._status == BotStatus.STOPPED:
            return
        self._status = BotStatus.STOPPING
        logger.info(f"Stopping command bot: {self._name}")
        self._status = BotStatus.STOPPED
        logger.info(f"Command bot '{self._name}' stopped")

    async def restart(self) -> None:
        """Restart the command bot."""
        await self.stop()
        await self.start()

    async def health_check(self) -> dict[str, Any]:
        """Check bot health."""
        uptime = None
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
        return {
            "bot_name": self._name,
            "bot_type": self._bot_type.value,
            "status": self._status.value,
            "uptime_seconds": uptime,
            "registered_commands": len(self._command_handlers),
            "observed_agents": len(self._observed_agents),
            "api_agents": len(self._api_agents),
            "chat_agents": len(self._chat_agents),
            "healthy": self._status == BotStatus.RUNNING
        }

    def register_command(
        self,
        command_name: str,
        handler: Callable,
        roles: Optional[list[str]] = None,
        parameters: Optional[List[Union[str, ActionParameter, dict[str, str]]]] = None,
    ) -> None:
        """
        Register a command handler.
        Args:
            command_name: Command name (without / prefix)
            handler: Handler function
            roles: Optional list of required roles
            parameters: Optional list of ActionParameter, str (name only), or short dict {name: type_str} / {name*: type_str} (* = required).
        """
        command_name = command_name.lstrip('/')
        self._command_handlers[command_name] = handler
        self._command_roles[command_name] = roles or []
        if parameters is not None:
            self._command_parameters[command_name] = _normalize_parameters(parameters)
        self._help_cache.clear()
        logger.info(f"Registered command: /{command_name} (roles: {roles or 'any'})")

    def register(self, command_name: str, handler: Callable, roles: Optional[list[str]] = None) -> None:
        """ICommandHandler: register a command (delegates to register_command)."""
        self.register_command(command_name, handler, roles=roles)

    @property
    def commands(self) -> _CommandsAdapter:
        """Fluent API: bot.commands.add(name=..., handler=...) returns the bot for chaining."""
        return _CommandsAdapter(self)

    @property
    def providers(self) -> _ProvidersAdapter:
        """Fluent API: bot.providers.chat.add(p), bot.providers.auth(p), bot.providers.storage(p)."""
        return _ProvidersAdapter(self)

    def chat_provider(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Fluent API: add a chat provider under a title and return self for chaining."""
        self.add_chat_provider(provider, title)
        return self

    def auth_provider(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Fluent API: add an auth provider under a title and return self for chaining."""
        self.add_auth_provider(provider, title)
        return self

    def storage_provider(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Fluent API: add a storage provider under a title and return self for chaining."""
        self.add_storage_provider(provider, title)
        return self

    def command_provider(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Fluent API: add a command provider under a title (provider.register_with(bot)) and return self for chaining."""
        self.add_command_provider(provider, title)
        return self

    def command(
        self,
        name: str,
        handler: Optional[Callable] = None,
        parameters: Optional[List[Union[str, ActionParameter, dict[str, str]]]] = None,
        roles: Optional[List[str]] = None,
    ) -> Any:
        """
        Fluent API: register a command and return self for chaining.
        parameters: optional list of ActionParameter(name, param_type=..., required=...), str (name only), or short dict form {name: type_str} / {name*: type_str} (* = required).
        Can be used as:
          bot.command("repeat", _repeat, parameters=[ActionParameter("string")])
          or as decorator: @bot.command("repeat") def repeat(string): ...
        """
        if handler is not None:
            self.register_command(name, handler, roles=roles, parameters=parameters)
            return self

        def decorator(f: Callable) -> Callable:
            self.register_command(name, f, roles=roles, parameters=parameters)
            return f

        return decorator

    def provider(self, provider: Any, title: str = "default") -> "XWBotCommand":
        """Fluent API: add a chat provider (backward compat) and return self for chaining."""
        self.add_chat_provider(provider, title)
        return self

    async def run(self) -> None:
        """
        Start the bot and run the first registered provider's event loop (e.g. Telegram polling).
        Use after .command(...).provider(...). Requires at least one provider.
        """
        await self.start()
        if not self.get_chat_providers():
            logger.warning("No chat providers registered; run() only started the bot.")
            return
        prov = self.get_default_chat_provider()
        if prov is None:
            logger.warning("No default chat provider; run() only started the bot.")
            return
        if hasattr(prov, "set_message_handler") and hasattr(prov, "start_listening"):
            def on_message(ctx: Any) -> Any:
                return self.handle(_message_from_context(ctx))
            prov.set_message_handler(on_message)
            await prov.start_listening()
        else:
            logger.warning("Default chat provider has no set_message_handler/start_listening; run() only started the bot.")

    async def handle(self, message: IMessage) -> Any:
        """
        ICommandHandler: parse message text into command + args and execute.
        Enables using XWBotCommand as bot._command_handler so platforms can
        dispatch to execute_command (and thus to observed XWApiAgent actions).
        Returns reply text or None if no command matched / empty.
        """
        text = (message.text or "").strip()
        if not text:
            return None
        parts = text.split()
        cmd = parts[0].lstrip("/")
        if not cmd:
            return None
        context: dict[str, Any] = {}
        if hasattr(message, "_message_data"):
            data = getattr(message, "_message_data", {})
            context.setdefault("user_id", data.get("user_id"))
            context.setdefault("chat_id", data.get("chat_id"))
            context.setdefault("username", data.get("username"))
            context.setdefault("help_format", data.get("help_format"))
        return await self.execute_command(cmd, message, context)

    async def execute_command(self, command_name: str, message: IMessage, context: dict[str, Any]) -> Any:
        """
        Execute a command.
        Args:
            command_name: Command name (without / prefix)
            message: Message instance
            context: Execution context
        Returns:
            Command execution result
        """
        command_name = command_name.lstrip('/')
        if command_name not in self._command_handlers:
            return (
                f"🤷 I don't know /{command_name}\n\n"
                "📖 Send /help for the full command list."
            )
        handler = self._command_handlers[command_name]
        try:
            # Check role-based access if roles are required
            required_roles = self._command_roles.get(command_name, [])
            if required_roles:
                user_roles = context.get('user_roles', [])
                if not any(role in user_roles for role in required_roles):
                    return (
                        "🔒 Access denied\n\n"
                        f"Needed roles: {', '.join(required_roles)}\n"
                        "Tip: check Google sheet / authorizer mapping for your Telegram @username."
                    )
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "execute_command start | bot=%r | command=/%s | ctx=%s | text=%s",
                    getattr(self, "_name", "?"),
                    command_name,
                    _safe_context_for_log(context),
                    _log_truncate(message.text or "", 220),
                )
            self._register_inflight_command_task(command_name, context)
            # Execute handler
            sig = signature(handler)
            params = list(sig.parameters.keys())
            text = message.text or ""
            parts = text.split()[1:] if text.strip().startswith('/') else text.split()
            kwargs: dict[str, Any] = {}
            if 'message' in params:
                kwargs['message'] = message
            if 'context' in params:
                kwargs['context'] = context
            param_names = [p for p in params if p not in ('message', 'context')]
            # *args (VAR_POSITIONAL) cannot be passed by keyword; pass as positional
            args_param = sig.parameters.get('args') if 'args' in param_names else None
            if args_param is not None and args_param.kind == inspect.Parameter.VAR_POSITIONAL:
                # Handler is (message, context, *args) — call with message, context, *parts
                call_args: list[Any] = []
                if 'message' in params:
                    call_args.append(message)
                if 'context' in params:
                    call_args.append(context)
                call_args.extend(parts)
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(*call_args)
                else:
                    result = await asyncio.to_thread(handler, *call_args)
            elif 'args' in param_names:
                kwargs['args'] = parts
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(**kwargs)
                else:
                    result = await asyncio.to_thread(handler, **kwargs)
            else:
                for i, pname in enumerate(param_names):
                    if i < len(parts):
                        kwargs[pname] = parts[i]
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(**kwargs)
                else:
                    result = await asyncio.to_thread(handler, **kwargs)
            return result
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(
                "execute_command failed | bot=%r | command=/%s | ctx=%s | text=%s | %s: %s",
                getattr(self, "_name", "?"),
                command_name,
                _safe_context_for_log(context),
                _log_truncate(message.text or "", 400),
                type(e).__name__,
                e,
                exc_info=True,
            )
            return f"⚠️ Something went wrong\n\n{str(e)}\n\nTry again or send /help."

    def observe_api_agent(self, agent: Any, agent_name: Optional[str] = None) -> None:
        """
        Observe an XWApiAgent and auto-generate commands from its actions.
        This method:
        1. Discovers all XWAction-decorated methods in the agent
        2. Creates command handlers for each action with cmd_shortcut
        3. Auto-generates a help command that lists all commands from all observed agents
        Args:
            agent: XWApiAgent instance
            agent_name: Optional name for the agent (defaults to agent's name)
        """
        try:
            # Get agent name (ensure str for dict key and add_api_agent)
            if agent_name is None:
                agent_name = getattr(agent, '_name', f'agent_{len(self._observed_agents)}')
            name: str = agent_name or f'agent_{len(self._observed_agents)}'
            # Store agent
            self._observed_agents[name] = agent
            # Add to api_agents as well
            self.add_api_agent(agent, name)
            # Discover actions from agent
            if hasattr(agent, 'get_actions'):
                actions = agent.get_actions()
            else:
                # Fallback: try to discover actions manually
                from inspect import getmembers, ismethod
                actions = []
                for name, method in getmembers(agent, predicate=ismethod):
                    if hasattr(method, 'xwaction'):
                        actions.append(method)
            logger.info(f"Observing agent '{name}' with {len(actions)} actions")
            # Create command handlers for each action
            for action in actions:
                # Get action metadata
                xwaction = getattr(action, 'xwaction', None)
                if not xwaction:
                    continue
                # Get command shortcut
                cmd_shortcut = (
                    getattr(xwaction, 'cmd_shortcut', None) or
                    getattr(xwaction, '_cmd_shortcut', None) or
                    None
                )
                if not cmd_shortcut:
                    # Try to use operationId or api_name as fallback
                    cmd_shortcut = (
                        getattr(xwaction, 'operationId', None) or
                        getattr(xwaction, '_operationId', None) or
                        getattr(xwaction, 'api_name', None) or
                        getattr(xwaction, '_api_name', None) or
                        action.__name__
                    )
                    # Convert to command-friendly format
                    cmd_shortcut = cmd_shortcut.replace('.', '_').replace('-', '_')
                # Get roles
                roles = getattr(xwaction, 'roles', None) or getattr(xwaction, '_roles', None) or []
                # Bind per-action callables via default args. A plain closure over `action` would
                # leak the *last* loop iteration's method to every registered handler (Python late binding).
                async def handler(
                    message: IMessage,
                    context: dict[str, Any],
                    *args,
                    _act: Any = action,
                    _agent_inst: Any = agent,
                    _agent_nm: str = name,
                ) -> Any:
                    act = _act
                    agent_inst = _agent_inst
                    agent_nm = _agent_nm
                    # Extract arguments from message
                    text = message.text or ""
                    parts = text.split()[1:] if text.startswith('/') else text.split()
                    # Prepare context with agent
                    exec_context = context.copy()
                    exec_context['agent'] = agent_inst
                    exec_context['agent_name'] = agent_nm
                    # Call action method
                    kw_log: dict[str, Any] = {}
                    try:
                        # Get method signature
                        sig = signature(act)
                        params = list(sig.parameters.keys())
                        # Prepare arguments
                        kwargs = {}
                        if 'message' in params:
                            kwargs['message'] = message
                        # XWAction wrapper reads kwargs['context'] (dict) to build ActionContext.metadata
                        # (user_roles, username). Methods without a `context` param still need it for
                        # check_permissions; the facade strips `context` before calling the inner func.
                        if 'context' in params or getattr(act, "xwaction", None) is not None:
                            kwargs['context'] = exec_context
                        if 'session' in params:
                            # Try to get session from context or agent
                            kwargs['session'] = exec_context.get('session') or getattr(agent_inst, 'session', None)
                        # Add positional arguments (never bind `self` from message parts)
                        param_idx = 0
                        for param in params:
                            if param == "self":
                                continue
                            if param not in kwargs and param_idx < len(parts):
                                kwargs[param] = parts[param_idx]
                                param_idx += 1
                        kw_log = _safe_action_kwargs_for_log(kwargs)
                        if logger.isEnabledFor(logging.DEBUG):
                            xw_dbg = getattr(act, "xwaction", None)
                            _cmd = (
                                getattr(xw_dbg, "cmd_shortcut", None)
                                or getattr(xw_dbg, "_cmd_shortcut", None)
                                or getattr(act, "__name__", "?")
                            )
                            logger.debug(
                                "observed_action start | bot=%r | agent=%r | /%s | ctx=%s | params=%s",
                                getattr(self, "_name", "?"),
                                agent_nm,
                                _cmd,
                                _safe_context_for_log(exec_context),
                                kw_log,
                            )
                        # #region agent log
                        try:
                            import json
                            import time
                            from pathlib import Path

                            _dbg = Path.cwd() / "debug-817459.log"
                            ur = exec_context.get("user_roles")
                            with _dbg.open("a", encoding="utf-8") as _df:
                                _df.write(
                                    json.dumps(
                                        {
                                            "sessionId": "817459",
                                            "hypothesisId": "H-ctx",
                                            "runId": "post-fix",
                                            "location": "xwbots/command_bot.observe_api_agent",
                                            "message": "invoke_action_kwargs",
                                            "data": {
                                                "act": getattr(act, "__name__", str(act)),
                                                "kwargs_keys": sorted(kwargs.keys()),
                                                "has_context_kw": "context" in kwargs,
                                                "user_roles_len": len(ur) if isinstance(ur, list) else None,
                                            },
                                            "timestamp": int(time.time() * 1000),
                                        }
                                    )
                                    + "\n"
                                )
                        except Exception:
                            pass
                        # #endregion
                        # Execute action without blocking the event loop (sync LMAM/API code would block and break reply sending)
                        if asyncio.iscoroutinefunction(act):
                            result = await act(**kwargs)
                        else:
                            result = await asyncio.to_thread(act, **kwargs)
                        return _coerce_observed_action_result(result)
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        xw = getattr(act, "xwaction", None)
                        cmd_alias = (
                            getattr(xw, "cmd_shortcut", None)
                            or getattr(xw, "_cmd_shortcut", None)
                            or getattr(act, "__name__", "action")
                        )
                        api_nm = getattr(xw, "api_name", None) if xw else None
                        logger.error(
                            "observed_action failed | bot=%r | agent=%r | command=/%s | "
                            "api_name=%r | action=%s | ctx=%s | params=%s | text=%s | %s: %s",
                            getattr(self, "_name", "?"),
                            agent_nm,
                            cmd_alias,
                            api_nm,
                            getattr(act, "__name__", "?"),
                            _safe_context_for_log(exec_context),
                            kw_log,
                            _log_truncate(text, 400),
                            type(e).__name__,
                            e,
                            exc_info=True,
                        )
                        return f"⚠️ Command failed\n\n{str(e)}"
                # Register command
                self.register_command(cmd_shortcut, handler, roles=roles)
                logger.debug(f"Auto-registered command /{cmd_shortcut} from agent '{name}' action '{action.__name__}'")
            self._help_cache.clear()
            logger.info(f"Successfully observed agent '{name}' and registered {len(actions)} commands")
        except Exception as e:
            logger.error(f"Error observing agent: {e}", exc_info=True)
            raise

    async def _cmd_cancel(
        self, message: IMessage, context: dict[str, Any]
    ) -> str:
        """
        Cancel in-flight command work for this user only (asyncio tasks awaiting LMAM/actions).
        Does not stop threads already running inside sync code; it stops the bot awaiting them.
        """
        key = self._inflight_user_key(context)
        if key == "unknown":
            return (
                "⚠️ Cannot identify you (no user id / username in context).\n"
                "/cancel only cancels work tied to your Telegram account."
            )
        bucket = self._inflight_by_user.get(key)
        if not bucket:
            return "ℹ️ No in-progress commands to cancel for you."
        me = asyncio.current_task()
        n = 0
        for t in list(bucket):
            if t is me or t.done():
                continue
            t.cancel()
            n += 1
        if n == 0:
            return "ℹ️ No active in-progress commands to cancel for you."
        return (
            f"🛑 Requested cancel for {n} in-progress command(s).\n"
            "Note: work already running in a background thread may finish shortly; "
            "the bot stops waiting on it."
        )

    async def _cmd_cancel_all(
        self, message: IMessage, context: dict[str, Any]
    ) -> str:
        """
        Cancel all in-flight command tasks for every user.
        Registered with owner|management; scouts are excluded unless they are also owner.
        """
        raw_roles = context.get("user_roles") or []
        if not isinstance(raw_roles, list):
            raw_roles = []
        role_lc = {str(r).strip().lower() for r in raw_roles if r is not None}
        # Agency leads only: not scouts (unless owner). Management without scout is OK.
        if "scout" in role_lc and "owner" not in role_lc:
            return (
                "🔒 /cancel_all is only for agency leadership — owners, or management who are "
                "not scouts.\n\n"
                "Scouts can use /cancel to stop their own in-progress commands."
            )
        me = asyncio.current_task()
        n = 0
        for _key, bucket in list(self._inflight_by_user.items()):
            for t in list(bucket):
                if t is me or t.done():
                    continue
                t.cancel()
                n += 1
        if n == 0:
            return "ℹ️ No in-progress commands to cancel."
        return (
            f"🛑 Requested cancel for {n} in-progress command(s) (all users).\n"
            "Note: threads already spawned by sync actions may still run briefly."
        )

    async def _cmd_help(
        self, message: IMessage, context: dict[str, Any]
    ) -> str | tuple[str, None, dict[str, Any]]:
        """Generate help message from all registered commands, with XWAction summary/description/parameters when available. Returns str or (text, None, send_kwargs) for provider-specific formatting (e.g. Telegram MarkdownV2)."""
        help_format = context.get("help_format") or "default"
        if help_format in self._help_cache:
            formatted = self._help_cache[help_format]
        else:
            if "default" not in self._help_cache:
                self._help_cache["default"] = self._build_help_default()
            default_help = self._help_cache["default"]
            formatter = _HELP_FORMATTERS.get(help_format, _HELP_FORMATTERS["default"])
            formatted = formatter(default_help)
            self._help_cache[help_format] = formatted
        if help_format == "telegram_markdown_v2":
            return (
                formatted,
                None,
                {"parse_mode": "MarkdownV2", "disable_web_page_preview": True},
            )
        if help_format == "telegram_html":
            return (formatted, None, {"parse_mode": "HTML", "disable_web_page_preview": True})
        return formatted

    async def _cmd_status(self, message: IMessage, context: dict[str, Any]) -> str:
        """Aggregate status from all command providers (auth, storage, Live.me, etc.) and return a single message."""
        lines = [
            "📋 Bot status",
            "",
            f"🤖 {self._name}",
            "",
        ]
        providers = self.get_command_providers()
        if not providers:
            lines.append("ℹ️ No command providers registered.")
            return "\n".join(lines)
        for title, prov in providers.items():
            lines.append(f"▸ {title}")
            get_status = getattr(prov, "get_status_entries", None)
            if not callable(get_status):
                lines.append("  (no status entries)")
                continue
            try:
                entries = get_status(self)
                if asyncio.iscoroutine(entries):
                    entries = await entries
                for name, ok, detail in entries:
                    icon = "✅" if ok else "❌"
                    lines.append(f"  {icon} {name} — {detail}")
            except Exception as e:
                lines.append(f"  ⚠️ {title}: {e}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def _build_help_default(self) -> str:
        """Build help in default markup (*bold*, _italic_, `code`) for cache + Telegram formatters."""
        # Map cmd_name -> (agent_name, action) for XWAction metadata
        cmd_action_map: dict[str, tuple[str, Any]] = {}
        commands_by_agent: dict[str, list[str]] = {}
        standalone_commands: list[str] = []
        for cmd_name, _handler in self._command_handlers.items():
            if cmd_name in ("help", "start", "cancel", "cancel_all"):
                continue
            agent_name: str | None = None
            found_action = None
            for ag_name, ag in self._observed_agents.items():
                if hasattr(ag, "get_actions"):
                    for action in ag.get_actions():
                        xwaction = getattr(action, "xwaction", None)
                        if xwaction:
                            shortcut = (
                                getattr(xwaction, "cmd_shortcut", None)
                                or getattr(xwaction, "_cmd_shortcut", None)
                                or getattr(action, "__name__", "")
                            )
                            if shortcut == cmd_name:
                                agent_name = ag_name
                                found_action = action
                                break
                if agent_name is not None:
                    break
            if found_action is not None and agent_name is not None:
                cmd_action_map[cmd_name] = (agent_name, found_action)
            if agent_name:
                commands_by_agent.setdefault(agent_name, []).append(cmd_name)
            else:
                standalone_commands.append(cmd_name)

        def _one_line_for_cmd(cmd: str) -> tuple[str, str | None]:
            """Return (main command line, optional indented detail line). No bullet glyphs."""
            roles = self._command_roles.get(cmd, [])
            lock = f" 🔒`{', '.join(roles)}`" if roles else ""
            blurb: str | None = None
            extras: list[str] = []
            if cmd in cmd_action_map:
                _an, action = cmd_action_map[cmd]
                xw = getattr(action, "xwaction", None)
                if xw:
                    summary = getattr(xw, "summary", None) or getattr(xw, "_summary", None)
                    desc = getattr(xw, "description", None) or getattr(xw, "_description", None)
                    text = (summary or desc or "").strip()
                    if text:
                        blurb = _help_truncate(text, 140)
                    params = getattr(xw, "parameters", None) or getattr(xw, "_parameters", None)
                    if isinstance(params, dict) and params:
                        parts: list[str] = []
                        for pname, pinfo in params.items():
                            if pname in _HELP_HIDDEN_ACTION_PARAMS:
                                continue
                            ptype = getattr(pinfo, "type", None)
                            type_str = getattr(ptype, "__name__", str(ptype)) if ptype is not None else "any"
                            req = getattr(pinfo, "required", True)
                            parts.append(f"{pname}:{type_str}" + ("" if req else "?"))
                        if parts:
                            extras.append("args: " + ", ".join(parts[:8]) + ("…" if len(parts) > 8 else ""))
                    rt = getattr(xw, "return_type", None)
                    if rt is not None:
                        extras.append("→ " + getattr(rt, "__name__", str(rt)))
            param_list = self._command_parameters.get(cmd)
            if param_list and not extras:
                extras.append("args: " + ", ".join(str(p) for p in param_list[:6]))
            sub = None
            if extras:
                sub = "   " + " · ".join(extras)
            main = f"`/{cmd}`" + (f" — {blurb}" if blurb else "") + lock
            return main, sub

        lines: list[str] = [
            f"📖 *{self._name}*",
            "",
            "_Commands use a slash. Locked commands need the right role in the sheet._",
            "",
            "*⚡ Quick*",
            "`/help` — this list",
        ]
        if "start" in self._command_handlers:
            lines.append("`/start` — welcome / setup")
        if "cancel" in self._command_handlers:
            lines.append("`/cancel` — stop your in-progress commands (this account)")
        if "cancel_all" in self._command_handlers:
            lines.append(
                "`/cancel_all` — stop every in-progress command 🔒`owner, management` _(not scouts)_"
            )
        lines.append("")

        for agent_name, commands in sorted(commands_by_agent.items()):
            lines.append(f"🧩 *{agent_name}*")
            for cmd in sorted(commands):
                main, sub = _one_line_for_cmd(cmd)
                lines.append(main)
                if sub:
                    lines.append(sub)
            lines.append("")

        if standalone_commands:
            lines.append("*📎 Other commands*")
            for cmd in sorted(standalone_commands):
                main, sub = _one_line_for_cmd(cmd)
                lines.append(main)
                if sub:
                    lines.append(sub)
            lines.append("")

        lines.append("💡 _Send /help anytime._")
        return "\n".join(lines).rstrip()
