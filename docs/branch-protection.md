Branch & release policy

- `main` is reserved for released, production-ready snapshots. Do **not** push or merge directly to `main`.
- All development work should land on `dev` via pull requests.

Local safeguards

- Install the repository git hooks to prevent accidental pushes/commits to `main`:

  bash scripts/install-git-hooks.sh

CI safeguard

- A GitHub Actions workflow will fail if anything is pushed directly to `main`.

If you need to perform a release (update `main`), follow the documented release procedure and coordinate with the repository owner.
