# Requirements Reference (REF_01_REQ)

**Project:** xwbots  
**Sponsor:** eXonware.com / eXonware Backend Team  
**Version:** 0.0.1  
**Last Updated:** 11-Feb-2026  
**Produced by:** [GUIDE_01_REQ.md](../guides/GUIDE_01_REQ.md)

---

## Purpose of This Document

This document is the **single source of raw and refined requirements** collected from the project sponsor and stakeholders. It is updated on every requirements-gathering run. When the **Clarity Checklist** (section 12) reaches the agreed threshold, use this content to fill REF_12_IDEA, REF_22_PROJECT, REF_13_ARCH, REF_14_DX, REF_15_API, and planning artifacts. Template structure: [GUIDE_01_REQ.md](../guides/GUIDE_01_REQ.md).

---

## 1. Vision and Goals

| Field | Content |
|-------|---------|
| One-sentence purpose | **Three types of bots**—**command** (commands/scenarios, execute functions, no LLM), **persona** (personality + knowledge base), **agentic** (command + persona + KB + API functions and calls)—**easy to use**, connect to **Telegram, Slack, Discord, and others**; **heavily uses xwaction, xwapi, and xwchat** (to give bots a voice and talk). (sponsor) |
| Primary users/beneficiaries | eXonware stack; developers building command, persona, or agentic bots across platforms. (sponsor + REF_22) |
| Success (6 mo / 1 yr) | 6 mo: Stable command/persona/agentic API, REF_* compliance. 1 yr: Production use, multi-platform, ecosystem integration. (Refine per REF_22.) |
| Top 3–5 goals (ordered) | 1) **Three bot types:** command-based (no LLM), persona (personality + knowledge base), agentic (command + persona + KB + API/function calls). 2) **Really easy to use**; connect easily to Telegram, Slack, Discord, others. 3) **Heavy use of xwaction** (execute functions), **xwapi** (API calls), **xwchat** (voice/talk). 4) Single API across platforms; lifecycle, crash recovery. 5) Library = bot logic; xwbots-server = HTTP/webhook surface. (sponsor + REF_22) |
| Problem statement | Need one framework for command bots, persona bots, and agentic bots that plugs into the eXonware stack (xwaction, xwapi, xwchat) and works across Telegram, Slack, Discord, and others. (sponsor) |

## 2. Scope and Boundaries

| In scope | Out of scope | Dependencies | Anti-goals |
|----------|--------------|--------------|------------|
| **Three bot types:** command (commands/scenarios, execute functions, no LLM), persona (personality, knowledge base), agentic (command + persona + KB + API/function calls); multi-platform (Telegram, Slack, Discord, others); **xwaction, xwapi, xwchat** integration; easy-to-use API; lifecycle, crash recovery; 4-layer tests. (sponsor + REF_22, README) | HTTP/webhook server implementation (xwbots-server). (from REF_22) | xwsystem, xwstorage, xwauth, xwentity, xwaction, xwapi, xwchat, xwai. (sponsor + pyproject.toml) | Platform-specific implementations as stable public API. (inferred) |

### 2a. Reverse-Engineered Evidence (from codebase)

- **Three bot types:** `bots/command_bot.py` — **XWBotCommand** (command registration/execution, scenarios, auto commands from XWApiAgent actions, role-based access; no LLM). `bots/persona_bot.py` — **XWBotPersona** (personality-driven responses, natural language, integration with XWApiAgent and XWChatAgent, context-aware; knowledge base via integration). `bots/agentic_bot.py` — **XWBotAgentic** (autonomous decision-making, multi-bot orchestration, goal management; combines command + persona + API/function capability).
- **Facade:** `facade.py` — **XWBot**(platform, name, api_key, enable_crash_recovery); **ABot** base; platform = TelegramPlatform, DiscordPlatform, etc. (`defs.py` PlatformType).
- **Stack integration:** Command bot uses xwaction (execute functions); persona/agentic use xwapi (XWApiAgent) and xwchat (XWChatAgent for voice/talk). xwstorage, xwauth, xwentity, xwai in contracts/deps.

## 3. Stakeholders and Sponsor

| Sponsor (name, role, final say) | Main stakeholders | External customers/partners | Doc consumers |
|----------------------------------|-------------------|-----------------------------|---------------|
| eXonware (company); eXonware Backend Team (author, maintainer, final say). Vision: three bot types—command, persona, agentic; xwaction, xwapi, xwchat; easy, multi-platform. | Project sponsor / eXonware; downstream REF owners. | None currently. Future: open-source adopters. | Downstream REF_22/REF_13 owners; bot developers; AI agents (Cursor). |

## 4. Compliance and Standards

| Regulatory/standards | Security & privacy | Certifications/evidence |
|----------------------|--------------------|--------------------------|
| Per GUIDE_00_MASTER, GUIDE_11_COMP. (inferred) | xwauth integration for role-based access. (inferred) | None currently. Per GUIDE_00_MASTER when required. |

## 5. Product and User Experience

| Main user journeys/use cases | Developer persona & 1–3 line tasks | Usability/accessibility | UX/DX benchmarks |
|-----------------------------|------------------------------------|--------------------------|------------------|
| Create command bot (no LLM), persona bot (personality + KB), or agentic bot (all + API calls); connect to Telegram/Slack/Discord/others; use xwaction, xwapi, xwchat for actions, APIs, and voice. (sponsor + README) | Developer: XWBotCommand / XWBotPersona / XWBotAgentic(platform=...), or XWBot(platform=TelegramPlatform(...)), @bot.command("start"), await bot.start(). (facade, bots/) | Really easy to use (sponsor) | Per REF_22. |

## 6. API and Surface Area

| Main entry points / "key code" | Easy (1–3 lines) vs advanced | Integration/existing APIs | Not in public API |
|--------------------------------|------------------------------|---------------------------|-------------------|
| XWBot, XWBotCommand, XWBotPersona, XWBotAgentic; TelegramPlatform, DiscordPlatform, SlackPlatform; command decorator; bot.start(). (facade, bots/) | Easy: XWBot(platform=...), @bot.command("start"), bot.start(). Or pick command/persona/agentic bot type. Advanced: xwaction, xwapi, xwchat, role-based access. (README, sponsor) | xwstorage, xwauth, xwentity, xwaction, xwapi, xwchat, xwai. (sponsor + REF_22) | Platform adapter internals. (inferred) |

## 7. Architecture and Technology

| Required/forbidden tech | Preferred patterns | Scale & performance | Multi-language/platform |
|-------------------------|--------------------|----------------------|-------------------------|
| Python 3.12+; xwsystem, xwstorage, xwauth, xwentity, xwaction, xwapi, xwchat, xwai. (sponsor + pyproject.toml) | Three bot types (command, persona, agentic); library vs server scope. (sponsor + REF_22) | Per REF_22. | Python; multi-platform (Telegram, Discord, Slack, others). (inferred) |

## 8. Non-Functional Requirements (Five Priorities)

| Security | Usability | Maintainability | Performance | Extensibility |
|----------|-----------|-----------------|-------------|---------------|
| xwauth for role-based access. (inferred) | Per REF_22. | REF_22, REF_35, logs; 4-layer tests. (from REF_22) | Per REF_22. | Platform adapters. (inferred) |

## 9. Milestones and Timeline

| Major milestones | Definition of done (first) | Fixed vs flexible |
|------------------|----------------------------|-------------------|
| M1 — Bot framework and structure (Done); M2 — Tests (4-layer confirm) (Done). (from REF_22) | FR-002: 4-layer tests confirmed. (from REF_22) | Per REF_22. |

## 10. Risks and Assumptions

| Top risks | Assumptions | Kill/pivot criteria |
|-----------|-------------|----------------------|
| Per REF_22. | xwbots-server delegates to xwbots; scope documented in both REF_22s. (from REF_22) | Per REF_22. |

## 11. Workshop / Session Log (Optional)

| Date | Type | Participants | Outcomes |
|------|------|---------------|----------|
| 11-Feb-2026 | Reverse‑engineer + Q&A | User + Agent | Sponsor vision: three bot types—command (no LLM), persona (personality + KB), agentic (command + persona + KB + API/function calls); easy to use; Telegram, Slack, Discord, others; heavily uses xwaction, xwapi, xwchat (voice/talk). REF_01 updated; Section 2a added (bots/command_bot, persona_bot, agentic_bot). |

## 12. Clarity Checklist

| # | Criterion | ☐ |
|---|-----------|---|
| 1 | Vision and one-sentence purpose filled and confirmed | ☑ |
| 2 | Primary users and success criteria defined | ☑ |
| 3 | Top 3–5 goals listed and ordered | ☑ |
| 4 | In-scope and out-of-scope clear | ☑ |
| 5 | Dependencies and anti-goals documented | ☑ |
| 6 | Sponsor and main stakeholders identified | ☑ |
| 7 | Compliance/standards stated or deferred | ☑ |
| 8 | Main user journeys / use cases listed | ☑ |
| 9 | API / "key code" expectations captured | ☑ |
| 10 | Architecture/technology constraints captured | ☑ |
| 11 | NFRs (Five Priorities) addressed | ☑ |
| 12 | Milestones and DoD for first milestone set | ☑ |
| 13 | Top risks and assumptions documented | ☑ |
| 14 | Sponsor confirmed vision, scope, priorities | ☑ |

**Clarity score:** 14 / 14. **Ready to fill downstream docs?** ☑ Yes

---

*Inferred content is marked; sponsor confirmation required. Per GUIDE_01_REQ.*
