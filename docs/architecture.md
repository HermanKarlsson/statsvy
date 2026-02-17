# Architecture

For a detailed overview of the project architecture, see [ARCHITECTURE.md](https://github.com/HermanKarlsson/statsvy/blob/main/ARCHITECTURE.md) in the repository.

## High-Level Overview

Statsvy follows a layered architecture with clear separation of concerns:

```
CLI Layer (cli/)
    ↓
Configuration (config/)
    ↓
Core Logic (core/)
    ↓
Data Models (data/)
    ↓
Formatters / Serializers / Storage
```

### Key Principles

- **Data/logic separation** — Frozen dataclasses hold data; separate classes handle logic
- **Coordinator pattern** — Core modules orchestrate specialized components
- **Strategy pattern** — Project config readers for different formats (pyproject.toml, package.json, Cargo.toml)
- **One class per file** — Clear file-to-class mapping
- **Composition over inheritance** — Components are composed, not inherited

### Directory Structure

```
src/statsvy/
├── cli/              # Command handlers and orchestrators
├── config/           # Configuration loading and management
├── config_readers/   # Strategy pattern: project config readers
├── core/             # Core coordinators (analyzer, scanner, formatter)
├── data/             # Pure data models (frozen dataclasses)
├── formatters/       # Output formatters (table, JSON, markdown)
├── language_parsing/ # Language detection and line analysis
├── serializers/      # Data serialization/deserialization
├── storage/          # Persistence and history management
└── utils/            # Shared utilities (console, paths)
```

For the complete architecture documentation including data flow diagrams, module responsibilities, and design decisions, see the full [ARCHITECTURE.md](https://github.com/HermanKarlsson/statsvy/blob/main/ARCHITECTURE.md).
