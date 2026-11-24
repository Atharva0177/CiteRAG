# P0-T01 — Bootstrap proof

Date: 2026-11-24. Branch: `p0-t01-bootstrap`.

## Scope and status

Local bootstrap and verification passed. Implementation and proof were committed in `f246a05`; GitHub Actions `offline-ci` run [45382729300](https://github.com/Atharva0177/CiteRAG/actions/runs/45382729300) completed successfully at that commit. Formal completion evidence was recorded after these checks.

## Toolchain

Executed through Conda environment `cv`:

| Tool | Verified version |
| --- | --- |
| Python | 3.12.15 |
| pip | 26.2.1 in `cv` |
| Node | 24.13.0 |
| npm | 11.6.2 |
| pytest | 9.1.1 |
| Ruff | 0.17.1 |
| PyYAML | 6.0.3 |

Version pins are in `.python-version`, `.nvmrc`, `environment.yml`, `package.json`, `package-lock.json`, and `requirements-dev.lock`. The Python lock includes direct and transitive routine-test dependencies. Bootstrap disables dependency resolution with `--no-deps`; npm uses `npm ci`.

## Executed setup

Existing `cv` setup:

```bash
conda run -n cv python scripts/bootstrap.py
```

Result: passed. Python, Node, and npm versions matched; every locked Python requirement was satisfied; `npm ci` completed with `up to date`.

Cold dependency setup used a clean venv seeded by the `cv` interpreter, leaving the existing Conda environment unchanged:

```bash
conda run -n cv python -m venv .venv
conda run -n cv "E:/RAG/.venv/Scripts/python.exe" scripts/bootstrap.py
```

Result: passed. The clean environment downloaded and installed all nine locked Python packages, validated all three runtime versions, and completed `npm ci`. Package downloads were setup traffic only; no hosted model client or live model procedure was invoked.

Second setup through the same path:

```bash
conda run -n cv "E:/RAG/.venv/Scripts/python.exe" scripts/bootstrap.py
```

Result: passed. Every Python requirement reported `Requirement already satisfied`; npm reported `up to date`. This demonstrates repeatability and idempotence after cold installation.

One initial wrapper attempt used a relative executable path and failed before installation with `'.venv' is not recognized as an internal or external command`. The absolute executable path shown above corrected the invocation; it was not a dependency failure.

The existing `cv` environment was not deleted or recreated. The README's first-time `conda env create --file environment.yml` command was therefore not exercised in this session; the locked bootstrap script itself received cold and repeat runs.

## Clean-environment verification

```bash
conda run -n cv "E:/RAG/.venv/Scripts/python.exe" scripts/check.py
```

Final result:

```text
All checks passed!
26 passed in 0.62s
Offline checks passed; no hosted model procedure was invoked.
```

The same check in `cv` also passed with `26 passed in 0.60s`.

## Reproduction boundary

Normal project commands remain `conda run -n cv python scripts/bootstrap.py` and `conda run -n cv python scripts/check.py`. The `.venv` was verification-only, is ignored, and is not part of the committed source.
