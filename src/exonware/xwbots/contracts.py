#!/usr/bin/env python3
"""
#exonware/xwbots/src/exonware/xwbots/contracts.py
Protocol interfaces for xwbots.
Company: eXonware.com
Author: eXonware Backend Team
Email: connect@exonware.com
Version: 0.0.1.7
Generation Date: 07-Jan-2025
"""

from __future__ import annotations
from typing import Any, Optional, Protocol, runtime_checkable, Callable
from exonware.xwapi.contracts import IApiServicesProvider
from .defs import BotStatus, PlatformType, CommandType, MessageType, BotType
@runtime_checkable

class IBot(Protocol):
    """Interface for bot operations."""

    async def start(self) -> None:
        """Start bot."""
        ...

    async def stop(self) -> None:
        """Stop bot."""
        ...

    async def restart(self) -> None:
        """Restart bot."""
        ...

    async def health_check(self) -> dict[str, Any]:
        """Check bot health."""
        ...
    @property

    def status(self) -> BotStatus:
        """Get bot status."""
        ...

    def add_api_agent(self, agent: Any, name: Optional[str] = None) -> None:
        """Add an XWApiAgent instance."""
        ...

    def add_chat_agent(self, agent: Any, name: Optional[str] = None) -> None:
        """Add an XWChatAgent instance."""
        ...

    def get_api_agents(self) -> dict[str, Any]:
        """Get all XWApiAgent instances."""
        ...

    def get_chat_agents(self) -> dict[str, Any]:
        """Get all XWChatAgent instances."""
        ...
@runtime_checkable

class IBotCommand(IBot, Protocol):
    """Interface for command-based bot operations."""

    def add_chat_provider(self, provider: Any, title: str = "default") -> None:
        """Add a chat provider under a title. Use title='default' for the default provider."""
        ...

    def get_chat_providers(self) -> dict[str, Any]:
        """Get all chat providers (title -> provider)."""
        ...

    def get_default_chat_provider(self) -> Any | None:
        """Get the default chat provider, if any."""
        ...

    def add_auth_provider(self, provider: Any, title: str = "default") -> None:
        """Add an auth provider under a title. Use title='default' for the default provider."""
        ...

    def get_auth_providers(self) -> dict[str, Any]:
        """Get all auth providers (title -> provider)."""
        ...

    def get_default_auth_provider(self) -> Any | None:
        """Get the default auth provider, if any."""
        ...

    def add_storage_provider(self, provider: Any, title: str = "default") -> None:
        """Add a storage provider under a title. Use title='default' for the default provider."""
        ...

    def get_storage_providers(self) -> dict[str, Any]:
        """Get all storage providers (title -> provider)."""
        ...

    def get_default_storage_provider(self) -> Any | None:
        """Get the default storage provider, if any."""
        ...

    def add_command_provider(self, provider: Any, title: str = "default") -> None:
        """Add a command provider under a title. Provider should implement register_with(bot)."""
        ...

    def get_command_providers(self) -> dict[str, Any]:
        """Get all command providers (title -> provider)."""
        ...

    def get_default_command_provider(self) -> Any | None:
        """Get the default command provider, if any."""
        ...
    @property

    def bot_type(self) -> BotType:
        """Get bot type (COMMAND)."""
        ...

    def register_command(self, command_name: str, handler: Callable, roles: Optional[list[str]] = None) -> None:
        """Register a command handler."""
        ...

    async def execute_command(self, command_name: str, message: IMessage, context: dict[str, Any]) -> Any:
        """Execute a command."""
        ...

    def observe_api_agent(self, agent: Any, agent_name: Optional[str] = None) -> None:
        """Observe an XWApiAgent and auto-generate commands from its actions."""
        ...
@runtime_checkable

class IBotPersona(IBot, Protocol):
    """Interface for persona-based conversational bot operations."""

    def add_knowledge_provider(self, provider: Any, title: str = "default") -> None:
        """Add a knowledge provider under a title. Use title='default' for the default provider."""
        ...

    def get_knowledge_providers(self) -> dict[str, Any]:
        """Get all knowledge providers (title -> provider)."""
        ...

    def get_default_knowledge_provider(self) -> Any | None:
        """Get the default knowledge provider, if any."""
        ...
    @property

    def bot_type(self) -> BotType:
        """Get bot type (PERSONA)."""
        ...

    async def process_message(self, message: IMessage, context: dict[str, Any]) -> str:
        """Process a natural language message and generate response."""
        ...

    def set_persona(self, persona_name: str, personality_traits: list[str], conversation_style: str) -> None:
        """Set persona configuration."""
        ...
@runtime_checkable

class IBotAgentic(IBot, Protocol):
    """Interface for autonomous agent bot operations."""
    @property

    def bot_type(self) -> BotType:
        """Get bot type (AGENTIC)."""
        ...

    async def add_goal(self, goal: dict[str, Any]) -> str:
        """Add a goal for the agent to pursue."""
        ...

    async def assign_bot(self, bot_instance: Any, capabilities: list[str]) -> None:
        """Assign a bot instance to be managed by this agent."""
        ...
@runtime_checkable

class IPlatform(Protocol):
    """Interface for platform operations."""

    async def send_message(self, chat_id: str, text: str, **kwargs) -> None:
        """Send message."""
        ...

    async def receive_message(self) -> IMessage:
        """Receive message."""
        ...
    @property

    def platform_type(self) -> PlatformType:
        """Get platform type."""
        ...
@runtime_checkable

class ICommand(Protocol):
    """Interface for command operations."""
    @property

    def name(self) -> str:
        """Get command name."""
        ...
    @property

    def command_type(self) -> CommandType:
        """Get command type."""
        ...

    async def execute(self, message: IMessage, context: dict[str, Any]) -> Any:
        """Execute command."""
        ...
@runtime_checkable

class IMessage(Protocol):
    """Interface for message operations."""
    @property

    def message_id(self) -> str:
        """Get message ID."""
        ...
    @property

    def chat_id(self) -> str:
        """Get chat ID."""
        ...
    @property

    def text(self) -> Optional[str]:
        """Get message text."""
        ...
    @property

    def message_type(self) -> MessageType:
        """Get message type."""
        ...

    async def reply(self, text: str, **kwargs) -> None:
        """Reply to message."""
        ...
@runtime_checkable

class ICommandHandler(Protocol):
    """Interface for command handlers."""

    def register(self, command_name: str, handler: Callable, roles: Optional[list[str]] = None) -> None:
        """Register command handler."""
        ...

    async def handle(self, message: IMessage) -> Any:
        """Handle command."""
        ...


@runtime_checkable
class ICommandProvider(IApiServicesProvider, Protocol):
    """Interface for pluggable command sets. Register commands with the bot when added. Extends IApiServicesProvider (xwapi)."""

    def register_with(self, bot: IBotCommand) -> None:
        """Register this provider's commands with the bot (e.g. bot.register_command, bot.observe_api_agent)."""
        ...
