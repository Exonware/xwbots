#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/base.py
Abstract base classes for xwbots.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.8
Generation Date: 07-Jan-2025
"""

from abc import ABC, abstractmethod
import asyncio
from typing import Any, Optional, Callable
from exonware.xwapi.base import AApiServicesProvider
from .contracts import (
    IBot, IBotCommand, IBotPersona, IBotAgentic,
    IPlatform, ICommand, IMessage, ICommandHandler, ICommandProvider
)
from .defs import BotStatus, PlatformType, CommandType, MessageType, BotType


class ABot(IBot, ABC):
    """Abstract base class for bot operations."""

    def __init__(self, name: str, bot_type: BotType):
        """Initialize base bot."""
        self._name = name
        self._bot_type = bot_type
        self._status = BotStatus.STOPPED
        self._api_agents: dict[str, Any] = {}
        self._chat_agents: dict[str, Any] = {}
    @property

    def name(self) -> str:
        """Get bot name."""
        return self._name
    @property

    def bot_type(self) -> BotType:
        """Get bot type."""
        return self._bot_type
    @abstractmethod

    async def start(self) -> None:
        """Start bot."""
        pass
    @abstractmethod

    async def stop(self) -> None:
        """Stop bot."""
        pass
    @abstractmethod

    async def restart(self) -> None:
        """Restart bot."""
        pass
    @abstractmethod

    async def health_check(self) -> dict[str, Any]:
        """Check bot health."""
        pass
    @property

    def status(self) -> BotStatus:
        """Get bot status."""
        return self._status

    def add_api_agent(self, agent: Any, name: Optional[str] = None) -> None:
        """Add an XWApiAgent instance."""
        agent_name = name or getattr(agent, '_name', f'agent_{len(self._api_agents)}')
        self._api_agents[agent_name] = agent

    def add_chat_agent(self, agent: Any, name: Optional[str] = None) -> None:
        """Add an XWChatAgent instance."""
        agent_name = name or getattr(agent, 'name', f'chat_agent_{len(self._chat_agents)}')
        self._chat_agents[agent_name] = agent

    def get_api_agents(self) -> dict[str, Any]:
        """Get all XWApiAgent instances."""
        return self._api_agents.copy()

    def get_chat_agents(self) -> dict[str, Any]:
        """Get all XWChatAgent instances."""
        return self._chat_agents.copy()


class ABotCommand(IBotCommand, ABot, ABC):
    """Abstract base class for command-based bot operations."""

    def __init__(self, name: str):
        """Initialize command bot."""
        super().__init__(name, BotType.COMMAND)
        self._command_handlers: dict[str, Callable] = {}
        self._command_roles: dict[str, list[str]] = {}
        self._observed_agents: dict[str, Any] = {}
        self._chat_providers: dict[str, Any] = {}
        self._auth_providers: dict[str, Any] = {}
        self._storage_providers: dict[str, Any] = {}
        self._default_chat_provider_key: str | None = None
        self._default_auth_provider_key: str | None = None
        self._default_storage_provider_key: str | None = None
        self._command_providers: dict[str, Any] = {}
        self._default_command_provider_key: str | None = None

    def add_chat_provider(self, provider: Any, title: str = "default") -> None:
        """Add a chat provider under a title. First added or title='default' becomes default."""
        self._chat_providers[title] = provider
        if self._default_chat_provider_key is None or title == "default":
            self._default_chat_provider_key = title

    def get_chat_providers(self) -> dict[str, Any]:
        """Get all chat providers (title -> provider)."""
        return dict(self._chat_providers)

    def get_default_chat_provider(self) -> Any | None:
        """Get the default chat provider, if any."""
        if self._default_chat_provider_key is not None:
            return self._chat_providers.get(self._default_chat_provider_key)
        return next(iter(self._chat_providers.values()), None) if self._chat_providers else None

    def add_auth_provider(self, provider: Any, title: str = "default") -> None:
        """Add an auth provider under a title. First added or title='default' becomes default."""
        self._auth_providers[title] = provider
        if self._default_auth_provider_key is None or title == "default":
            self._default_auth_provider_key = title

    def get_auth_providers(self) -> dict[str, Any]:
        """Get all auth providers (title -> provider)."""
        return dict(self._auth_providers)

    def get_default_auth_provider(self) -> Any | None:
        """Get the default auth provider, if any."""
        if self._default_auth_provider_key is not None:
            return self._auth_providers.get(self._default_auth_provider_key)
        return next(iter(self._auth_providers.values()), None) if self._auth_providers else None

    def add_storage_provider(self, provider: Any, title: str = "default") -> None:
        """Add a storage provider under a title. First added or title='default' becomes default."""
        self._storage_providers[title] = provider
        if self._default_storage_provider_key is None or title == "default":
            self._default_storage_provider_key = title

    def get_storage_providers(self) -> dict[str, Any]:
        """Get all storage providers (title -> provider)."""
        return dict(self._storage_providers)

    def get_default_storage_provider(self) -> Any | None:
        """Get the default storage provider, if any."""
        if self._default_storage_provider_key is not None:
            return self._storage_providers.get(self._default_storage_provider_key)
        return next(iter(self._storage_providers.values()), None) if self._storage_providers else None

    def add_command_provider(self, provider: Any, title: str = "default") -> None:
        """Add a command provider under a title. First added or title='default' becomes default. Calls provider.register_with(self) if present."""
        self._command_providers[title] = provider
        if self._default_command_provider_key is None or title == "default":
            self._default_command_provider_key = title
        register_with = getattr(provider, "register_with", None)
        if callable(register_with):
            register_with(self)

    def get_command_providers(self) -> dict[str, Any]:
        """Get all command providers (title -> provider)."""
        return dict(self._command_providers)

    def get_default_command_provider(self) -> Any | None:
        """Get the default command provider, if any."""
        if self._default_command_provider_key is not None:
            return self._command_providers.get(self._default_command_provider_key)
        return next(iter(self._command_providers.values()), None) if self._command_providers else None
    @property

    def bot_type(self) -> BotType:
        """Get bot type (COMMAND)."""
        return BotType.COMMAND
    @abstractmethod

    def register_command(self, command_name: str, handler: Callable, roles: Optional[list[str]] = None) -> None:
        """Register a command handler."""
        pass
    @abstractmethod

    async def execute_command(self, command_name: str, message: IMessage, context: dict[str, Any]) -> Any:
        """Execute a command."""
        pass
    @abstractmethod

    def observe_api_agent(self, agent: Any, agent_name: Optional[str] = None) -> None:
        """Observe an XWApiAgent and auto-generate commands from its actions."""
        pass


class ACommandProvider(AApiServicesProvider, ICommandProvider, ABC):
    """
    Abstract base for command providers. Extends AApiServicesProvider (xwapi);
    subclasses implement get_action_command_names() and register_with(bot).
    Optionally override get_status_entries(bot) to contribute to /status (auth, storage, etc.).
    """

    @abstractmethod
    def register_with(self, bot: IBotCommand) -> None:
        """Register this provider's commands with the bot (e.g. bot.register_command, bot.observe_api_agent)."""
        pass

    async def get_status_entries(self, bot: Any) -> list[tuple[str, bool, str]]:
        """
        Return status check entries for /status: list of (check_name, ok, detail).
        Default: report authentication and storage from bot's providers.
        Subclasses override to add more (e.g. Live.me connection).
        """
        entries: list[tuple[str, bool, str]] = []

        # Authentication: check each auth provider (e.g. is_connected)
        auth_providers = getattr(bot, "get_auth_providers", lambda: {})()
        if not auth_providers:
            entries.append(("Authentication", False, "No auth provider configured"))
        else:
            for title, prov in auth_providers.items():
                name = f"Authentication ({title})"
                is_connected = getattr(prov, "is_connected", None)
                if callable(is_connected):
                    try:
                        result = is_connected()
                        if asyncio.iscoroutine(result):
                            result = await result
                        entries.append((name, bool(result), "OK" if result else "Not connected"))
                    except Exception as e:
                        entries.append((name, False, str(e)))
                else:
                    entries.append((name, True, "Configured (no health check)"))

        # Storage: check each storage provider (simple availability or "configured")
        storage_providers = getattr(bot, "get_storage_providers", lambda: {})()
        if not storage_providers:
            entries.append(("Storage", False, "No storage provider configured"))
        else:
            for title, prov in storage_providers.items():
                name = f"Storage ({title})"
                health = getattr(prov, "health_check", None) or getattr(prov, "health", None)
                if callable(health):
                    try:
                        result = health()
                        if asyncio.iscoroutine(result):
                            result = await result
                        ok = result if isinstance(result, bool) else bool(result.get("healthy", result) if isinstance(result, dict) else result)
                        entries.append((name, ok, "OK" if ok else str(result)))
                    except Exception as e:
                        entries.append((name, False, str(e)))
                else:
                    entries.append((name, True, "Configured (no health check)"))

        return entries


class ABotPersona(IBotPersona, ABot, ABC):
    """Abstract base class for persona-based conversational bot operations."""

    def __init__(self, name: str):
        """Initialize persona bot."""
        super().__init__(name, BotType.PERSONA)
        self._persona_name = "Assistant"
        self._personality_traits: list[str] = []
        self._conversation_style = "friendly"
        self._knowledge_providers: dict[str, Any] = {}
        self._default_knowledge_provider_key: str | None = None

    def add_knowledge_provider(self, provider: Any, title: str = "default") -> None:
        """Add a knowledge provider under a title. First added or title='default' becomes default."""
        self._knowledge_providers[title] = provider
        if self._default_knowledge_provider_key is None or title == "default":
            self._default_knowledge_provider_key = title

    def get_knowledge_providers(self) -> dict[str, Any]:
        """Get all knowledge providers (title -> provider)."""
        return dict(self._knowledge_providers)

    def get_default_knowledge_provider(self) -> Any | None:
        """Get the default knowledge provider, if any."""
        if self._default_knowledge_provider_key is not None:
            return self._knowledge_providers.get(self._default_knowledge_provider_key)
        return next(iter(self._knowledge_providers.values()), None) if self._knowledge_providers else None
    @property

    def bot_type(self) -> BotType:
        """Get bot type (PERSONA)."""
        return BotType.PERSONA
    @abstractmethod

    async def process_message(self, message: IMessage, context: dict[str, Any]) -> str:
        """Process a natural language message and generate response."""
        pass

    def set_persona(self, persona_name: str, personality_traits: list[str], conversation_style: str) -> None:
        """Set persona configuration."""
        self._persona_name = persona_name
        self._personality_traits = personality_traits
        self._conversation_style = conversation_style


class ABotAgentic(IBotAgentic, ABot, ABC):
    """Abstract base class for autonomous agent bot operations."""

    def __init__(self, name: str):
        """Initialize agentic bot."""
        super().__init__(name, BotType.AGENTIC)
        self._active_goals: list[dict[str, Any]] = []
        self._managed_bots: dict[str, Any] = {}
    @property

    def bot_type(self) -> BotType:
        """Get bot type (AGENTIC)."""
        return BotType.AGENTIC
    @abstractmethod

    async def add_goal(self, goal: dict[str, Any]) -> str:
        """Add a goal for the agent to pursue."""
        pass
    @abstractmethod

    async def assign_bot(self, bot_instance: Any, capabilities: list[str]) -> None:
        """Assign a bot instance to be managed by this agent."""
        pass


class APlatform(IPlatform, ABC):
    """Abstract base class for platform operations."""
    @abstractmethod

    async def send_message(self, chat_id: str, text: str, **kwargs) -> None:
        """Send message."""
        pass
    @abstractmethod

    async def receive_message(self) -> IMessage:
        """Receive message."""
        pass
    @property
    @abstractmethod

    def platform_type(self) -> PlatformType:
        """Get platform type."""
        pass


class ACommand(ICommand, ABC):
    """Abstract base class for command operations."""
    @property
    @abstractmethod

    def name(self) -> str:
        """Get command name."""
        pass
    @property
    @abstractmethod

    def command_type(self) -> CommandType:
        """Get command type."""
        pass
    @abstractmethod

    async def execute(self, message: IMessage, context: dict[str, Any]) -> Any:
        """Execute command."""
        pass


class AMessage(IMessage, ABC):
    """Abstract base class for message operations."""
    @property
    @abstractmethod

    def message_id(self) -> str:
        """Get message ID."""
        pass
    @property
    @abstractmethod

    def chat_id(self) -> str:
        """Get chat ID."""
        pass
    @property
    @abstractmethod

    def text(self) -> Optional[str]:
        """Get message text."""
        pass
    @property
    @abstractmethod

    def message_type(self) -> MessageType:
        """Get message type."""
        pass
    @abstractmethod

    async def reply(self, text: str, **kwargs) -> None:
        """Reply to message."""
        pass


class ACommandHandler(ICommandHandler, ABC):
    """Abstract base class for command handlers."""
    @abstractmethod

    def register(self, command_name: str, handler: Any, roles: Optional[list[str]] = None) -> None:
        """Register command handler."""
        pass
    @abstractmethod

    async def handle(self, message: IMessage) -> Any:
        """Handle command."""
        pass
