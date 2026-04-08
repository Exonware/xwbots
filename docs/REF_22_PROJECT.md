# Project Reference — xwbots

**Library:** exonware-xwbots  
**Last Updated:** 07-Feb-2026

Per REF_35_REVIEW.

---

## Vision

xwbots provides **bot framework** surface for the eXonware ecosystem (~28 Python files). **xwbots-server** (stub) exposes the API (e.g. webhook endpoints) and delegates to this library. Scope: library = bot logic and types; server = HTTP/API surface.

---

## Goals

1. **Bot framework:** Bot types, handlers, integration points.
2. **Scope vs xwbots-server:** xwbots = library; xwbots-server = API/webhook surface (delegates to xwbots). Documented here and in xwbots-server REF_22.
3. **Traceability:** REF_22_PROJECT, REF_35_REVIEW, logs.

---

## Functional Requirements (Summary)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-001 | Bot framework and package structure | High | Done |
| FR-002 | Tests (4-layer confirm) | Medium | Done |

---

## Project Status Overview

- **Current phase:** Alpha (Low–Medium). REF_22 (this file), REF_35_REVIEW; logs/reviews/.
- **Docs:** REF_22_PROJECT (this file), REF_35_REVIEW; logs/reviews/.

---

*See GUIDE_22_PROJECT.md. Review: REF_35_REVIEW.md. xwbots-server: see xwbots-server/docs/REF_22_PROJECT.md.*
