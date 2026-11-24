# CiteRAG

P0-T01 repository bootstrap. Application pipelines are implemented in later phase-gated tasks; this is not a release setup guide.

## Bootstrap

Prerequisites: Conda and nvm (or nvm-windows). From the repository root, use this single setup path:

```bash
conda env create --file environment.yml
nvm install
nvm use
conda run -n cv python scripts/bootstrap.py
conda run -n cv python scripts/check.py
```

If the `cv` environment already exists, start at `nvm install`. The bootstrap command is idempotent; rerun it after dependency-lock changes. It verifies Python 3.12.15, Node 24.13.0, and npm 11.6.2, installs every Python dependency from `requirements-dev.lock` with dependency resolution disabled, and runs `npm ci` against `package-lock.json`.

`scripts/check.py` removes hosted-provider credentials from child processes, disables package/model network access, scans source for credentials, checks browser sources for server-secret names, and runs Ruff, pytest, and Git whitespace checks. Pytest also blocks socket connections through `tests/conftest.py`.

## Configuration and hosted calls

`config/settings.yaml` contains non-secret defaults. Provider credentials belong only in environment variables, never in YAML, committed fixtures, logs, or browser code. `.env.example` documents the variable names; it is a template, not an auto-loaded file.

Routine development and CI use fixtures only and consume no hosted-model quota. Live calls require a separate authorized procedure, `fixtures_only: false`, explicit live opt-in, a credential, and a recorded reason. P0-T01 implements only the policy boundary, not a hosted client.

The pre-P7 identity in `apps/api/identity.py` is a development-only single-user identity. It is not authentication and is rejected in production configuration.

See `tests/fixtures/README.md` for fixture rules and `TASKS.md` for phase gates. Full architecture, service, privacy, and clean-machine release documentation belongs to P7-T05.
