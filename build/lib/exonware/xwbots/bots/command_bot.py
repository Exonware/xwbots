from collections.abc import Callable
#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/bots/command_bot.py
XWBotCommand - Command-based bot implementation.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.0
Generation Date: 07-Jan-2025
"""

import asyncio
import functools
import re
from types import SimpleNamespace
from typing import Any
import inspect
from inspect import signature
from datetime import datetime
from exonware.xwsystem import get_logger
from exonware.xwaction import ActionParameter
from ..base import ABotCommand
from ..contracts import IMessage
from ..defs import BotStatus, BotType, MessageType
logger = get_logger(__name__)


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


# --- Help formatting per provider (default = single */_ for bold/italic; telegram_markdown_v2 = double and escaped) ---
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


def _normalize_parameters(
    parameters: list[str | ActionParameter | dict[str, str]] | None = None,
) -> list[ActionParameter]:
    """
    Convert parameters to list of ActionParameter. Accepts:
    - ActionParameter: use as-is
    - str: param name only -> ActionParameter(name, str, required=True)
    - dict: short form {param_name: type_str} or {param_name*: type_str} (trailing * = required).
            One dict can have multiple keys, e.g. {"city": "string", "limit": "integer"}.
    """
    if not parameters:
        return []
    out: list[ActionParameter] = []
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
        parameters: list[str | ActionParameter | dict[str, str]] | None = None,
        roles: list[str] | None = None,
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
    """

    def __init__(self, name: str, platform: Any | None = None):
        """
        Initialize command bot.
        Args:
            name: Bot name
            platform: Optional platform instance (IPlatform)
        """
        super().__init__(name)
        self._platform = platform
        self._start_time: datetime | None = None
        self._help_cache: dict[str, str] = {}
        self._command_parameters: dict[str, list[ActionParameter]] = {}

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
        roles: list[str] | None = None,
        parameters: list[str | ActionParameter | dict[str, str]] | None = None,
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

    def register(self, command_name: str, handler: Callable, roles: list[str] | None = None) -> None:
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
        handler: Callable | None = None,
        parameters: list[str | ActionParameter | dict[str, str]] | None = None,
        roles: list[str] | None = None,
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
            return f"❌ Unknown command: /{command_name}. Use /help for available commands."
        handler = self._command_handlers[command_name]
        try:
            # Check role-based access if roles are required
            required_roles = self._command_roles.get(command_name, [])
            if required_roles:
                user_roles = context.get('user_roles', [])
                if not any(role in user_roles for role in required_roles):
                    return f"❌ Access denied. Required roles: {', '.join(required_roles)}"
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
        except Exception as e:
            logger.error(f"Error executing command /{command_name}: {e}", exc_info=True)
            return f"❌ Error executing command: {str(e)}"

    def observe_api_agent(self, agent: Any, agent_name: str | None = None) -> None:
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
                # Create command handler wrapper with proper closure
                # Capture action, agent, and agent_name in closure
                act = action  # Capture in closure
                agent_inst = agent  # Capture in closure
                agent_nm = name  # Capture in closure
                async def handler(message: IMessage, context: dict[str, Any], *args) -> Any:
                    # Extract arguments from message
                    text = message.text or ""
                    parts = text.split()[1:] if text.startswith('/') else text.split()
                    # Prepare context with agent
                    exec_context = context.copy()
                    exec_context['agent'] = agent_inst
                    exec_context['agent_name'] = agent_nm
                    # Call action method
                    try:
                        # Get method signature
                        sig = signature(act)
                        params = list(sig.parameters.keys())
                        # Prepare arguments
                        kwargs = {}
                        if 'message' in params:
                            kwargs['message'] = message
                        if 'context' in params:
                            kwargs['context'] = exec_context
                        if 'session' in params:
                            # Try to get session from context or agent
                            kwargs['session'] = exec_context.get('session') or getattr(agent_inst, 'session', None)
                        # Add positional arguments
                        param_idx = 0
                        for param in params:
                            if param not in kwargs and param_idx < len(parts):
                                kwargs[param] = parts[param_idx]
                                param_idx += 1
                        # Execute action without blocking the event loop (sync LMAM/API code would block and break reply sending)
                        if asyncio.iscoroutinefunction(act):
                            result = await act(**kwargs)
                        else:
                            result = await asyncio.to_thread(act, **kwargs)
                        return result
                    except Exception as e:
                        logger.error(f"Error executing action {act.__name__}: {e}", exc_info=True)
                        return f"❌ Error: {str(e)}"
                # Register command
                self.register_command(cmd_shortcut, handler, roles=roles)
                logger.debug(f"Auto-registered command /{cmd_shortcut} from agent '{name}' action '{action.__name__}'")
            self._help_cache.clear()
            logger.info(f"Successfully observed agent '{name}' and registered {len(actions)} commands")
        except Exception as e:
            logger.error(f"Error observing agent: {e}", exc_info=True)
            raise

    async def _cmd_help(self, message: IMessage, context: dict[str, Any]) -> str | tuple[str, None, dict[str, str]]:
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
            return (formatted, None, {"parse_mode": "MarkdownV2"})
        if help_format == "telegram_html":
            return (formatted, None, {"parse_mode": "HTML"})
        return formatted

    async def _cmd_status(self, message: IMessage, context: dict[str, Any]) -> str:
        """Aggregate status from all command providers (auth, storage, Live.me, etc.) and return a single message."""
        lines = ["📋 Status"]
        providers = self.get_command_providers()
        if not providers:
            lines.append("No command providers registered.")
            return "\n".join(lines)
        for title, prov in providers.items():
            get_status = getattr(prov, "get_status_entries", None)
            if not callable(get_status):
                continue
            try:
                entries = get_status(self)
                if asyncio.iscoroutine(entries):
                    entries = await entries
                for name, ok, detail in entries:
                    icon = "✅" if ok else "❌"
                    lines.append(f"{icon} {name}: {detail}")
            except Exception as e:
                lines.append(f"❌ {title}: {e}")
        return "\n".join(lines) if len(lines) > 1 else "\n".join(lines)

    def _build_help_default(self) -> str:
        """Build help text in default format (*bold*, _italic_, `code`). Used for caching and for other formatters."""
        help_lines = [f"🤖 *{self._name} - Available Commands*\n"]
        # Map cmd_name -> (agent_name, action) for XWAction metadata
        cmd_action_map: dict[str, tuple[str, Any]] = {}
        commands_by_agent: dict[str, list[str]] = {}
        standalone_commands = []
        for cmd_name, handler in self._command_handlers.items():
            if cmd_name in ("help", "start"):
                continue
            agent_name = None
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
        # Add commands by agent with optional XWAction in/out info
        for agent_name, commands in commands_by_agent.items():
            help_lines.append(f"\n*{agent_name.upper()} Commands:*")
            for cmd in sorted(commands):
                roles = self._command_roles.get(cmd, [])
                role_text = f" [{', '.join(roles)}]" if roles else ""
                help_lines.append(f"• `/{cmd}`{role_text}")
                if cmd in cmd_action_map:
                    _agent_name, action = cmd_action_map[cmd]
                    xwaction = getattr(action, "xwaction", None)
                    if xwaction:
                        summary = getattr(xwaction, "summary", None) or getattr(xwaction, "_summary", None)
                        if summary:
                            help_lines.append(f"  Summary: {summary}")
                        description = getattr(xwaction, "description", None) or getattr(xwaction, "_description", None)
                        if description:
                            help_lines.append(f"  Description: {description}")
                        params = getattr(xwaction, "parameters", None) or getattr(xwaction, "_parameters", None)
                        if isinstance(params, dict) and params:
                            param_parts = []
                            for pname, pinfo in params.items():
                                if pname == "self":
                                    continue
                                ptype = getattr(pinfo, "type", None)
                                type_str = getattr(ptype, "__name__", str(ptype)) if ptype is not None else "any"
                                required = getattr(pinfo, "required", True)
                                param_parts.append(f"{pname} ({type_str})" + ("" if required else " [optional]"))
                            if param_parts:
                                help_lines.append(f"  In: {', '.join(param_parts)}")
                        return_type = getattr(xwaction, "return_type", None)
                        if return_type is not None:
                            out_str = getattr(return_type, "__name__", str(return_type))
                            help_lines.append(f"  Out: {out_str}")
        if standalone_commands:
            help_lines.append(f"\n*General Commands:*")
            for cmd in sorted(standalone_commands):
                roles = self._command_roles.get(cmd, [])
                role_text = f" [{', '.join(roles)}]" if roles else ""
                help_lines.append(f"• `/{cmd}`{role_text}")
                param_list = self._command_parameters.get(cmd)
                if param_list:
                    help_lines.append(f"  In: {', '.join(str(p) for p in param_list)}")
        help_lines.append(f"\n*Use `/help` to see this message again.*")
        return "\n".join(help_lines)
