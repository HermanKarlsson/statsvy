---
description: Always load these instructions for all AI-assisted actions in this repository.
applyTo: "**/*"
---

# Project Instructions for Copilot

When generating code, reviewing code, proposing architecture, or answering technical questions within this repository, always:

1. Read and follow the rules defined in `AGENTS.md`.
2. Read and follow the architectural principles defined in `ARCHITECTURE.md`.
3. Apply these documents as authoritative sources for:
   - coding standards
   - architecture and module boundaries
   - file organization
   - immutability rules
   - testing requirements
   - documentation style
   - dependency constraints

If a user request conflicts with these documents, prefer the rules in `AGENTS.md` and `ARCHITECTURE.md`.

When unsure, summarize the relevant parts of these documents and explain how they apply before generating code.
