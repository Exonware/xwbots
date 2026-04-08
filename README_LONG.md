# xwbots (long version)

**Multi-Platform Bot Framework for eXonware.**

*This is the long version (full features, examples, integration). Short overview: [README.md](README.md).*

---

**Company:** eXonware.com  
**Author:** eXonware Backend Team  
**Email:** connect@exonware.com  
**Version:** 0.0.1.0

---

## What is xwbots?

**xwbots** is an enterprise-grade multi-platform bot framework for the eXonware ecosystem. xwbots provides a unified interface for building bots across multiple platforms (Telegram, Discord, Slack, etc.) with seamless integration with xwstorage, xwauth, xwentity, xwaction, and xwai.

### The Problem We Solve

Developers building bots face challenges:
- **Platform-specific code** — Different APIs for Telegram, Discord, Slack
- **No unified interface** — Each platform requires different code
- **Poor ecosystem integration** — Bots don't integrate with storage, auth, entities
- **Limited command processing** — No unified command framework
- **No lifecycle management** — Difficult to manage bot start/stop/restart
- **No crash recovery** — Bots crash without recovery mechanisms

### The xwbots Solution

- **Multi-Platform Abstraction** — Single API for Telegram, Discord, Slack, and more
- **Ecosystem Integration** — Seamless integration with xwstorage, xwauth, xwentity, xwaction, xwai
- **Command Processing** — Unified command framework with xwaction integration
- **Lifecycle Management** — Bot start, stop, restart, and health monitoring
- **Crash Recovery** — Automatic crash recovery and restart mechanisms
- **Role-Based Access** — Integration with xwauth for role-based command access

---

## Installation

```bash
# Basic
pip install exonware-xwbots

# With lazy auto-install
pip install exonware-xwbots[lazy]

# Full (all features)
pip install exonware-xwbots[full]
```

---

## Quick Start

For **Telegram**, use **xwchat** directly (see [examples/](examples/)):

```python
from exonware.xwchat import Telegram as TelegramChatProvider

provider = TelegramChatProvider(api_token="your-telegram-key")
provider.set_message_handler(lambda ctx: "Hello!")  # or wire XWBotCommand
import asyncio
asyncio.run(provider.start_listening())
```

For command bots (e.g. Parrot with /weather, /repeat), use **XWBotCommand** and wire it to the provider's message handler—see `examples/parrot_bot/`.

---

## Key Features

### 1. Multi-Platform Support

**Telegram** is handled by **xwchat**; use its provider directly (see examples). For other platforms (Discord, Slack), a platform adapter can be used with XWBot when available.

```python
from exonware.xwchat import Telegram as TelegramChatProvider

provider = TelegramChatProvider(api_token="...")
provider.set_message_handler(your_handler)
import asyncio
asyncio.run(provider.start_listening())
```

### 2. Command Framework

Register commands with decorators; integrate with xwaction for business logic. Role-based access via xwauth.

### 3. Lifecycle and Recovery

Start, stop, restart programmatically; health monitoring; automatic crash recovery and restart.

### 4. Ecosystem Integration

- **xwstorage** — Persist bot state and data
- **xwauth** — User/role-based command access
- **xwentity** — Entity-backed bot data
- **xwaction** — Action execution from commands
- **xwai** — AI-powered responses

---

## Documentation

- [docs/INDEX.md](docs/INDEX.md) — When present
- [docs/](docs/) — Project documentation
- [README.md](README.md) — Short overview

---

## Innovation: Where does this package fit?

**Ecosystem glue — well-integrated**

**xwbots** — Multi-platform bot framework with crash recovery + auth integration. Strong engineering, tighter ecosystem integration. Part of the eXonware story — vertical integration across 20+ packages.

---

## License

MIT License — see [LICENSE](LICENSE).

---

**Company:** eXonware.com  
**Author:** eXonware Backend Team  
**Email:** connect@exonware.com
