# TODO.md - Statsvy Development

---

## Future Features

- Further performance benchmarking
- Cyclomatic complexity measurement
- Maintainability index
- Halstead metrics
- Code smell detection
- Integration as separate sub-package
- HTML export functionality
- Chart rendering for metrics
- Customizable themes and styling
- Rich visual reports
- Web dashboard for metrics visualization
- CI/CD pipeline integration
- IDE extensions
- Docker containerization
- API server for remote access
- Real-time file system monitoring
- Plugin system for extensions
- Programmatic API access
- Community plugin registry
- Integration with code review tools

---

## Module Architecture

Future major features should be implemented as separate sub-packages under `src/`:

- `statsvy_quality/` — Code quality analysis and metrics
- `statsvy_web/` — Web dashboard and API
- `statsvy_plugins/` — Plugin system
- `statsvy_integrations/` — External integrations (CI/CD, IDE, etc)
