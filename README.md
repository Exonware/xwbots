# xwbots

**Multi-platform bot framework.** Single API for Telegram, Discord, Slack; commands, lifecycle, crash recovery; integration with xwstorage, xwauth, xwentity, xwaction, xwai. Per project docs.

*Full features and examples: [README_LONG.md](README_LONG.md).*

**Company:** eXonware.com · **Author:** eXonware Backend Team · **Email:** connect@exonware.com  

[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://exonware.com)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

---

## 📦 Install

```bash
pip install exonware-xwbots
# Optional: [lazy] or [full]
pip install exonware-xwbots[lazy]
pip install exonware-xwbots[full]
```

---

## 🚀 Quick start

For **Telegram**, use **xwchat** directly (xwbots does not ship a platform adapter; xwchat owns the transport):

```python
from exonware.xwchat import Telegram as TelegramChatProvider

provider = TelegramChatProvider(api_token="your-telegram-key")
provider.set_message_handler(lambda ctx: "Hello!")  # or wire an XWBotCommand
import asyncio
asyncio.run(provider.start_listening())
```

See [examples/](examples/) for Karizma and Parrot bots that wire xwchat + command handlers.

---

## ✨ What you get

| Area | What's in it |
|------|----------------|
| **Platforms** | Telegram via **xwchat** (use xwchat's provider directly; see examples). |
| **Commands** | Command framework; xwaction integration; role-based access (xwauth). |
| **Lifecycle** | Start, stop, restart; crash recovery. |
| **Ecosystem** | xwstorage, xwauth, xwentity, xwaction, xwai. |

---

## 🛠️ Development (editable xwchat)

XWBots uses **xwchat** for Telegram. To work on both with live changes:

- **Recommended (exonware repo):** From repo root, run the shared venv script so the xwbots `.venv` gets all xw libs (including xwchat) in editable mode:
  ```bash
  python scripts/venvs/setup_venvs.py --packages-only
  ```
  Then activate `xwbots/.venv` and use it; xwchat will be installed as `-e ../xwchat`.

- **If you created xwbots' venv manually:** Ensure xwchat is editable in the current environment:
  ```bash
  # From exonware repo root or from xwbots
  python xwbots/scripts/ensure_editable_xwchat.py
  ```

---

## 📖 Docs and tests

- **Start:** [docs/INDEX.md](docs/INDEX.md) or [docs/](docs/).
- **Tests:** Run from project root per project layout.

---

## 📜 License and links

MIT — see [LICENSE](LICENSE). **Homepage:** https://exonware.com · **Repository:** https://github.com/exonware/xwbots  


## ⏱️ Async Support

<!-- async-support:start -->
- xwbots includes asynchronous execution paths in production code.
- Source validation: 56 async def definitions and 28 await usages under src/.
- Use async APIs for I/O-heavy or concurrent workloads to improve throughput and responsiveness.
<!-- async-support:end -->
Version: 0.0.1.7 | Updated: 13-Apr-2026

*Built with ❤️ by eXonware.com - Revolutionizing Python Development Since 2025*
