# Architecture Reference — exonware-xwbots

**Library:** exonware-xwbots  
**Version:** 0.0.1  
**Last Updated:** 11-Feb-2026  
**Requirements source:** [REF_01_REQ.md](REF_01_REQ.md) sec. 7, 6

---

## Overview

xwbots provides **bot framework** surface: bot types, handlers, integration points. **xwbots-server** (stub) exposes webhook/API and delegates to this library. Design: contracts, base, facade; bot implementations (agentic, command, persona) in submodules.

**Design philosophy:** Thin framework; pluggable handlers; library = logic, server = HTTP/webhook surface.

---

## High-Level Structure

```
xwbots/
+-- contracts.py   # Bot interfaces
+-- base.py        # Abstract bot bases
+-- facade.py      # Public API
+-- bots/
|   +-- agentic_bot.py
|   +-- command_bot.py
|   +-- persona_bot.py
+-- config.py, defs.py, errors.py, version.py
```

**Entry points:** `exonware.xwbots` (facade, bot types).

---

## Module Breakdown

### Contracts and base

**Purpose:** Interfaces and abstract bases for bot types and handlers.

### Bots (`bots/`)

**Purpose:** Concrete bot implementations — agentic, command, persona.

### Scope vs xwbots-server

- **xwbots (this library):** Bot logic, types, handlers.
- **xwbots-server:** Webhook endpoints (e.g. Telegram, Slack), HTTP API for bot management; delegates to xwbots.

---

## Dependencies

- eXonware stack as needed (xwsystem, etc.). xwbots-server depends on xwbots.

---

## Related Documents

- [REF_01_REQ.md](REF_01_REQ.md) — Requirements source
- [REF_22_PROJECT.md](REF_22_PROJECT.md) — Requirements and status
- [GUIDE_13_ARCH.md](../../docs/guides/GUIDE_13_ARCH.md) — Architecture guide
- xwbots-server/docs/REF_22_PROJECT.md — Server scope
