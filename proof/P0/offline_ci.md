# P0-T01 — Offline CI and safety proof

Date: 2026-11-24. Branch: `p0-t01-bootstrap`.

## Local CI-equivalent result

Executed in both `cv` and a clean `cv`-seeded verification environment:

```bash
conda run -n cv python scripts/check.py
conda run -n cv "E:/RAG/.venv/Scripts/python.exe" scripts/check.py
```

Both final runs passed:

- Ruff: `All checks passed!`.
- Pytest: `26 passed` in each environment.
- `git diff --check`: exit 0.
- Direct source trailing-whitespace scan: no findings, including untracked files and fresh CI checkout contents.
- Source secret scan: no findings.
- Browser-source server-credential-name check: passed. No browser bundle exists yet; Next.js work begins in P6.

`.github/workflows/ci.yml` runs on every push and pull request. It installs exact Python/Node versions, runs the same locked bootstrap, then invokes `scripts/check.py`. The workflow references no repository secrets or hosted-provider credentials.

**Remote CI status:** not run. No commit or push was authorized, so this file does not claim a green GitHub Actions job. Local CI-equivalent commands are green; remote workflow execution and committed proof remain required before formal task completion.

## Network-disabled tests

`tests/conftest.py` installs an autouse guard that replaces `socket.create_connection`, `socket.socket.connect`, and `socket.socket.connect_ex` with a function raising `RuntimeError`. A runtime test confirms connection attempts fail with `Network access is disabled during fixture-only tests`.

The check runner also:

- removes `NVIDIA_API_KEY` from child-process environments;
- forces `CITERAG_ALLOW_LIVE_NIM=false` and clears the live-call reason;
- sets `PIP_NO_INDEX=1`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and `npm_config_offline=true` for checks;
- refuses to start routine checks when the ambient environment explicitly enables live NIM use.

Negative control executed with a fake credential and live opt-in enabled. The checker exited nonzero before lint/tests and printed `Routine checks forbid live NIM use; run a separately authorized procedure`. The fake credential was not printed.

No hosted model client exists in P0-T01. All tests are local; zero hosted-model calls were made and zero NIM quota was consumed. Dependency downloads during cold bootstrap are separate from the network-disabled test phase.

## Configuration and identity boundaries

Tests verify:

- fixture-only defaults and environment-only provider secrets;
- malformed or unknown YAML fails with `ConfigurationError`, including non-scalar values and non-string keys;
- secret values are excluded from `Settings` representation;
- live calls require all four controls: non-fixture configuration, explicit opt-in, credential, and nonempty procedure reason;
- development identity is explicitly unauthenticated and rejected for production configuration;
- JSON logs preserve safe structured context while redacting configured secrets, bearer values, and sensitive nested keys.

## Credential-handling observation

During verification, a populated environment template/local copy appeared outside the planned blank template. Final `.env.example` was confirmed blank. `.env copy.example` was not read or modified; `.gitignore` now ignores `.env*` local variants while explicitly keeping `.env.example` trackable. Git confirmed the local copy is ignored and the template is not ignored.

No credential value is reproduced in proof. The scanner reports only file, line, and finding type. If the observed value was a real credential, rotate it; conversation/tool output cannot be treated as a secret store.

## Runtime observation

The runtime-version CLI printed `Python 3.12.15`, `Node 24.13.0`, and `npm 11.6.2`. The complete check CLI exited 0 with 26 tests and no hosted procedure.

Public `apps.api` smoke using a fake provider secret observed:

```text
fixtures_only: true
identity: development-only, is_authenticated=false
hosted call: Configuration is fixtures only; hosted calls are disabled
log message: credential [REDACTED]
context.Authorization: [REDACTED]
context.safe: ok
trace_id: p0-runtime
```

A separate CLI negative control with live opt-in enabled exited nonzero before source scans or tests. One API-smoke invocation with literal newlines failed in Conda's argument wrapper before Python started (`Support for scripts where arguments contain newlines not implemented`); a single-line invocation completed successfully. This wrapper limitation is recorded in `.claude/skills/verify/SKILL.md`.

## Evidence limit

These tests prove the implemented P0-T01 policy and local routine-check behavior. They do not prove future provider clients will be safe, confidential-collection enforcement, full browser-bundle absence of secrets, or remote CI success; those belong to their owning later tasks and the pending remote run.
