# TODO.md - Statsvy Development

---

## Future Features

- Further performance benchmarking
- Cyclomatic complexity measurement
- Maintainability index
- Halstead metrics
- Code smell detection
- Web dashboard for metrics visualization
- IDE extensions
- Programmatic API access

---

## Module Architecture

Future major features should be implemented as separate sub-packages under `src/`:

- `statsvy_quality/` — Code quality analysis and metrics
- `statsvy_web/` — Web dashboard and API
- `statsvy_plugins/` — Plugin system
- `statsvy_integrations/` — External integrations (CI/CD, IDE, etc)
