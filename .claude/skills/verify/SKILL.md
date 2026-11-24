---
name: verify
description: Verify CiteRAG bootstrap CLIs and P0 public safety APIs through Conda cv.
---

# CiteRAG runtime verification

Run from repository root with Conda environment `cv`:

```bash
conda run -n cv python scripts/bootstrap.py --check-only
conda run -n cv python scripts/check.py
```

Expect exact Python/Node/npm versions, then Ruff, network-disabled pytest, source scans, and Git whitespace checks to pass. `scripts/check.py` is itself the CLI surface; no application server exists in P0-T01.

Probe live-call rejection with a fake credential:

```bash
CITERAG_ALLOW_LIVE_NIM=true NVIDIA_API_KEY=not-a-real-credential conda run -n cv python scripts/check.py
```

Expect nonzero exit and `Routine checks forbid live NIM use` before source scans or tests. Never substitute a real credential.

Public package smoke: call `load_settings(environ={...})`, `get_development_identity`, `configure_logging`, and `assert_hosted_call_allowed` from their `apps.api` modules. Use only fake secrets. Observe fixture denial, `development-only` / `is_authenticated=false`, and JSON `[REDACTED]` output.

Conda on Windows rejects `python -c` arguments containing literal newlines. Keep smoke code single-line; use `exec('...\n...')` for a small compound statement. For clean dependency verification, seed `.venv` with `conda run -n cv python -m venv .venv` and invoke its absolute Python path through `conda run -n cv`.
