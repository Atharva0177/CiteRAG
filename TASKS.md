# CiteRAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local, single-user CiteRAG application that answers questions over PDF, PNG, and JPG documents with machine-verified claim citations, exact source quotes, block-level highlights, and honest refusals.

**Architecture:** Next.js calls FastAPI; FastAPI orchestrates hosted NIM rewrite, embedding, rerank, answer, and verification calls through one gateway. Celery workers render and parse pages through a Linux/WSL2 vLLM service, chunk typed blocks, and index PostgreSQL plus the P0-selected vector store. Every phase produces committed proof and blocks the next phase until its gate passes.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Celery, Redis, PostgreSQL, Qdrant or pgvector, PyMuPDF, vLLM, NVIDIA NIM, Next.js 15, TypeScript, pdf.js, pytest, Vitest, Playwright, Docker Compose.

## Global Constraints

- Task IDs, commit scopes, and proof directories use `P{phase}-T{nn}` and `proof/Pn/` exactly.
- Every task starts as **Not started**, has owner **Atharva**, and ends with one commit using `type(Pn-Tnn): message`.
- Do not begin a phase until every prior-phase task and gate is complete. Exploratory work does not close a later task.
- Follow `DECISION.md`; its accepted decisions are binding and its pending-gate decisions remain unresolved until evidence closes them.
- Supported v1 inputs are PDF, PNG, and JPG only. DOCX/PPTX, page-image retrieval, multimodal retrieval, and answer caching are optional P7 stretch work.
- Render PDF pages to RGB at 150 dpi. Downscale proportionally only above 1664×2048 pixels. Preserve actual dimensions and scale.
- Parser settings are exact: prompt `</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>`, `max_new_tokens=8744`, temperature 0, `top_k=1`, `repetition_penalty=1.1`, `skip_special_tokens=false`.
- Do not hardcode unverified model IDs, vector dimensions, input limits, request flags, rerank routes, score ranges, reasoning controls, quota limits, or endpoint terms.
- Hosted calls go through the NIM gateway. Normal tests use recorded fixtures and must make zero network calls to hosted models.
- A failed page gets two retries, meaning at most three attempts, without failing sibling pages. Parse-service outages pause resumable jobs.
- Text chunks target 400–800 tokens with about 12% overlap. Tables split above 1,200 tokens or the lower safe embedding limit, repeating header rows. No indexed chunk may exceed the measured embedding limit.
- Retrieval uses dense top 40, lexical top 40, RRF constant 60, rerank top 30, final top 8. PostgreSQL full-text search uses the `simple` configuration.
- Answer text is never streamed and never displayed before structural, quote, and entailment verification completes.
- Unsupported claims are removed, partial claims are badged, and no surviving factual claim may lack a valid citation.
- Displayed quotes are exact spans copied from stored source text. Highlight granularity is the parsed block.
- Secrets come from environment variables, never reach browser code, and are redacted from logs and proof artifacts.
- Confidential collections default to `true` and block hosted indexing/chat until explicit owner override and privacy acknowledgment.
- Every prompt, model, threshold, or chunking change reruns evaluation and records config hash plus git SHA in `eval_runs`.
- Original success targets cannot be silently changed. Recalibration is allowed only in P5 with measured reason and retained history.
- Run tests from repository root with `python -m pytest` and web tests from `apps/web` with `npm test`; live-NIM commands require an explicit budget acknowledgment environment variable.

## Execution and Review Rules

1. Mark one task **In progress** in this file before starting it.
2. Complete steps in order. Write and run the failing test before implementation unless the task is exclusively environment measurement or human review.
3. A red expected-failure run must fail for the stated reason, not collection errors or missing test infrastructure.
4. Run the listed focused tests and relevant regression tests before review.
5. Compare code, test output, and proof artifacts with acceptance criteria. An agent narrative is not proof.
6. Save proof at the task's exact path, including commands, sanitized raw output, date, config hash, and git SHA where applicable.
7. Commit only the task's files and proof. Mark **Done** only after commit and reviewer acceptance. Record the commit SHA beside status.
8. If acceptance fails, keep the task open and write the failure plus fix plan in its proof artifact. Do not lower the gate silently.

## File Responsibility Map

| Path | Responsibility |
| --- | --- |
| `packages/common/citerag_common/config.py` | Typed environment/YAML loading and verified-model guards |
| `packages/common/citerag_common/models.py` | SQLAlchemy persistence contracts |
| `packages/common/citerag_common/files.py` | Private upload storage and file validation |
| `packages/common/citerag_common/tracing.py` | Trace IDs, structured events, redaction |
| `apps/api/nim_gateway/` | Hosted request adapters, limits, retries, cache, fixtures |
| `apps/api/app/routers/` | Collection, document, chat, conversation, auth, health HTTP contracts |
| `apps/api/app/retrieval/` | Rewrite, hybrid search, RRF, rerank, abstention, context |
| `apps/api/app/verifier/` | Answer schema, quote matching, entailment policy, citation resolution |
| `apps/api/app/services/chat.py` | Query orchestration, persistence, regeneration, SSE events |
| `apps/worker/celery_app.py` | Celery configuration and queues |
| `apps/worker/tasks/` | Resumable render, parse, chunk, index, deletion workflows |
| `apps/parse_service/` | Isolated vLLM startup, parser client, postprocess adapter |
| `packages/chunking/chunking/` | Pure typed-block chunking and token accounting |
| `packages/eval/eval/` | Gold schema, metrics, calibration, ablations, reports |
| `apps/web/src/lib/` | Typed API/SSE clients and citation geometry |
| `apps/web/src/components/` | Library, chat, verified answer, PDF/image highlights |
| `scripts/` | Explicit live smoke, overlay, benchmark, gate, and load commands |
| `config/` | Versioned models, retrieval, prompts, thresholds |
| `proof/` | Committed gate evidence; never a source of application behavior |

## Canonical Internal Contracts

These names are normative across tasks. Extend fields additively only when a task explicitly defines them.

```python
# packages/common/citerag_common/contracts.py
from dataclasses import dataclass

# Coordinates use floating point; page numbers are one-based.
BBoxNorm = tuple[float, float, float, float]  # x0, y0, x1, y1
BBoxPixels = tuple[float, float, float, float]
BBoxPDF = tuple[float, float, float, float]

@dataclass(frozen=True)
class ParsedBlock:
    id: str
    page_id: str
    order_idx: int
    class_name: str
    bbox_norm: BBoxNorm
    bbox_px: BBoxPixels
    bbox_pdf: BBoxPDF
    text: str
    html: str | None

@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    chunk_type: str
    text: str
    embed_text: str
    token_count: int
    section_path: str | None
    page_start: int
    page_end: int
    continues_from: str | None
    block_ids: tuple[str, ...]
    lang: str

@dataclass(frozen=True)
class RankedChunk:
    chunk: Chunk
    dense_rank: int | None
    lexical_rank: int | None
    rrf_score: float
    rerank_score: float | None
    final_rank: int

@dataclass(frozen=True)
class Citation:
    chunk_id: str
    document_id: str
    page: int
    block_ids: tuple[str, ...]
    bboxes_pdf: tuple[BBoxPDF, ...]
    bboxes_px: tuple[BBoxPixels, ...]
    quote: str
    role: str  # primary or supplementary
    table_html: str | None
```

---

# P0 — Environment and Smoke Tests

**Entry:** PRD and approved `DECISION.md` exist; RTX 5070 machine and NVIDIA account are available.  
**Exit gate:** All six models respond or recorded fallbacks are chosen; three page types parse; model/limits/privacy/vector-store evidence and `config/models.yaml` are committed under `proof/P0/`.

### P0-T01: Initialize reproducible repository and guarded configuration

**Status:** Not started | **Owner:** Atharva  
**Depends on:** None  
**Requirements:** PRD §12 reproducibility, §15, §18 | **Decisions:** D-001, D-002, D-004  
**Proof:** `proof/P0/repository.md`

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.env.example`, `config/models.yaml`, `config/retrieval.yaml`
- Create: `packages/common/citerag_common/config.py`, `packages/common/citerag_common/contracts.py`, `packages/common/tests/test_config.py`
- Create: `.github/workflows/ci.yml`

**Interfaces:** Produce `ModelConfig.require_live() -> str`; later tasks cannot call an unverified model.

- [ ] **Step 1: Write the failing configuration guard test**

```python
# packages/common/tests/test_config.py
import pytest
from citerag_common.config import ModelConfig


def test_unverified_model_cannot_be_called():
    config = ModelConfig(model_id=None, verified=False)
    with pytest.raises(ValueError, match="P0 verification required"):
        config.require_live()


def test_verified_model_returns_exact_id():
    config = ModelConfig(model_id="vendor/measured-model", verified=True)
    assert config.require_live() == "vendor/measured-model"
```

- [ ] **Step 2: Run the test and confirm the missing implementation failure**

Run: `python -m pytest packages/common/tests/test_config.py -v`  
Expected: collection FAIL reporting `ModuleNotFoundError: No module named 'citerag_common'` after `pip install -e .` has installed declared packages.

- [ ] **Step 3: Add minimal project packaging and guard implementation**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "citerag"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.10", "PyYAML>=6.0"]

[project.optional-dependencies]
dev = ["pytest>=8.3", "pytest-cov>=6"]

[tool.setuptools.packages.find]
where = ["packages/common", "packages/chunking", "packages/eval"]
include = ["citerag_common*", "chunking*", "eval*"]

[tool.pytest.ini_options]
testpaths = ["packages", "apps"]
```

```python
# packages/common/citerag_common/config.py
from pydantic import BaseModel


class ModelConfig(BaseModel):
    model_id: str | None = None
    verified: bool = False

    def require_live(self) -> str:
        if not self.verified or not self.model_id:
            raise ValueError("P0 verification required before live model calls")
        return self.model_id
```

```yaml
# config/models.yaml
parse: {model_id: null, verified: false, endpoint: "http://127.0.0.1:8001"}
embed: {model_id: null, verified: false, vector_dim: null, max_input_tokens: null}
rerank: {model_id: null, verified: false, route: null, score_range: null}
rewrite: {model_id: null, verified: false}
answer: {model_id: null, verified: false, fallback_model_id: null}
verify: {model_id: null, verified: false, fallback_model_id: null}
limits: {requests_per_minute: null, credits_total: null, credits_remaining: null}
```

```yaml
# config/retrieval.yaml
dense_top_k: 40
lexical_top_k: 40
rrf_constant: 60
rerank_top_k: 30
final_top_k: 8
abstention_threshold: null
quote_match_threshold: 92
quote_max_words: 25
context_token_budget: 12000
```

- [ ] **Step 4: Add quota-safe CI and verify the tests pass**

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: python -m pip install -e '.[dev]'
      - run: python -m pytest packages/common/tests -v
```

Run: `python -m pip install -e '.[dev]' && python -m pytest packages/common/tests/test_config.py -v`  
Expected: 2 PASS; no network calls.

- [ ] **Step 5: Initialize git, record environment commands, and commit**

Run: `git init && git add pyproject.toml .gitignore .env.example config packages/common .github && git commit -m "chore(P0-T01): initialize reproducible repository"`  
Expected: `git rev-parse --verify HEAD` prints a SHA. Save commands and test output in the proof file.

**Acceptance:** Fresh editable install succeeds; unverified live calls fail closed; null P0 values are intentional unresolved measurements, not assumed defaults; initial commit exists.

### P0-T02: Establish RTX 5070 parser runtime

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T01  
**Requirements:** PRD §6 Parse, §12 Platform, P0 | **Decisions:** D-008, D-009  
**Proof:** `proof/P0/environment.md`, `proof/P0/parse_service.log`

**Files:**
- Create: `apps/parse_service/start.sh`, `.env.parse.example`
- Modify: `config/models.yaml`
- Test: `apps/parse_service/tests/test_start_script.py`

**Interfaces:** Produce local `GET http://127.0.0.1:8001/health` and environment keys `PARSE_MODEL_ID`, `PARSE_MAX_MODEL_LEN`.

- [ ] **Step 1: Record host and WSL GPU evidence**

Run on Windows: `nvidia-smi` and `wsl --list --verbose`.  
Run inside selected WSL2/Linux environment: `nvidia-smi && python3.12 --version`.  
Expected: RTX 5070 appears inside the same environment that will run vLLM. Save complete commands, driver/CUDA versions, OS kernel, and output in `environment.md`.

- [ ] **Step 2: Select compatible installs from current official documentation**

Open the official PyTorch installation matrix, vLLM Blackwell compatibility documentation, and Nemotron-3.5-Parse model page linked from `build.nvidia.com`. Record URLs, access date, selected versions, and exact install commands in `environment.md`. Execute those recorded commands inside `.venv-parse`; do not substitute remembered versions.

Run baseline: `python3.12 -m venv .venv-parse && source .venv-parse/bin/activate && python -m pip install --upgrade pip`  
Expected: recorded PyTorch/vLLM imports succeed and `torch.cuda.get_device_name(0)` identifies the RTX 5070.

- [ ] **Step 3: Write a failing startup-contract test**

```python
# apps/parse_service/tests/test_start_script.py
from pathlib import Path


def test_start_script_requires_verified_runtime_values():
    script = Path("apps/parse_service/start.sh").read_text()
    assert 'PARSE_MODEL_ID:?' in script
    assert 'PARSE_MAX_MODEL_LEN:?' in script
    assert "127.0.0.1" in script
    assert "8001" in script
```

Run: `python -m pytest apps/parse_service/tests/test_start_script.py -v`  
Expected: FAIL because `start.sh` does not exist.

- [ ] **Step 4: Implement and start the isolated service**

```bash
# apps/parse_service/start.sh
#!/usr/bin/env bash
set -euo pipefail
: "${PARSE_MODEL_ID:?set from the verified model page}"
: "${PARSE_MAX_MODEL_LEN:?set from measured model constraints}"
source .venv-parse/bin/activate
exec vllm serve "${PARSE_MODEL_ID}" \
  --host 127.0.0.1 \
  --port 8001 \
  --max-model-len "${PARSE_MAX_MODEL_LEN}" \
  --gpu-memory-utilization 0.90
```

Run: `chmod +x apps/parse_service/start.sh && bash -n apps/parse_service/start.sh && python -m pytest apps/parse_service/tests/test_start_script.py -v`  
Expected: syntax valid and 1 PASS. Set values from P0 evidence, start the script in WSL2, and save its sanitized log.

- [ ] **Step 5: Verify readiness and commit**

Run: `curl --fail --silent http://127.0.0.1:8001/health`  
Expected: HTTP success after model load. If installation/serving fails, capture the exact error, test the hosted parse option if currently available, and prepare D-009's Docling fallback decision rather than claiming success.

Commit: `git add apps/parse_service config/models.yaml .env.parse.example proof/P0 && git commit -m "test(P0-T02): verify local parser runtime"`

**Acceptance:** Same GPU environment passes import, device, service health, and model-load checks, or fallback evidence is explicit enough for D-009.

### P0-T03: Parse digital, scanned, and table-heavy sample pages

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T02  
**Requirements:** PRD §6 Parse, P0 smoke tests | **Decisions:** D-004, D-008, D-009, D-010  
**Proof:** `proof/P0/smoke_report.md`, `proof/P0/raw/digital.json`, `proof/P0/raw/scanned.json`, `proof/P0/raw/table.json`, `proof/P0/overlays/{digital,scanned,table}.png`

**Files:**
- Create: `apps/parse_service/parse_service/settings.py`, `apps/parse_service/parse_service/smoke.py`
- Create: `scripts/render_samples.py`, `scripts/overlay.py`
- Test: `apps/parse_service/tests/test_settings.py`

**Interfaces:** Produce `sampling_parameters() -> dict[str, object]`; later worker parsing reuses it unchanged.

- [ ] **Step 1: Write failing exact-parameter tests**

```python
# apps/parse_service/tests/test_settings.py
from parse_service.settings import PARSE_PROMPT, sampling_parameters


def test_parser_parameters_match_prd():
    assert PARSE_PROMPT == "</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>"
    assert sampling_parameters() == {
        "max_tokens": 8744,
        "temperature": 0,
        "top_k": 1,
        "repetition_penalty": 1.1,
        "skip_special_tokens": False,
    }
```

Run: `PYTHONPATH=apps/parse_service python -m pytest apps/parse_service/tests/test_settings.py -v`  
Expected: FAIL on missing `parse_service.settings`.

- [ ] **Step 2: Implement exact settings and verify**

```python
# apps/parse_service/parse_service/settings.py
PARSE_PROMPT = "</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>"


def sampling_parameters() -> dict[str, object]:
    return {
        "max_tokens": 8744,
        "temperature": 0,
        "top_k": 1,
        "repetition_penalty": 1.1,
        "skip_special_tokens": False,
    }
```

Run the Step 1 command again. Expected: 1 PASS.

- [ ] **Step 3: Build smoke requests from the verified model-page shape**

In `smoke.py`, load the request route and multimodal message template recorded in P0-T02, merge `sampling_parameters()` without renaming fields, send the RGB page image, and save the unmodified response body. In `render_samples.py`, use PyMuPDF's RGB conversion and proportional fit to 1664×2048; save actual dimensions beside each raw response.

Run: `PYTHONPATH=apps/parse_service python scripts/render_samples.py --input proof/P0/samples/digital.pdf --output proof/P0/rendered/digital.png` and equivalent commands for scanned and table samples.  
Expected: three RGB PNGs with recorded widths, heights, dpi, and scale.

- [ ] **Step 4: Run parser and postprocess/overlay proof**

Run the documented client command once per rendered PNG. Pass actual render size to the parser's official `postprocess_document`; preserve raw control tokens. Draw every returned `bbox_pixels` with class/text labels using `scripts/overlay.py`.

Expected: three raw JSON files and three overlays exist. Manual review records readable text, nonempty blocks, and whether each bbox encloses its source region. Do not edit raw output to improve appearance.

- [ ] **Step 5: Commit the smoke evidence**

Commit: `git add apps/parse_service scripts config/models.yaml proof/P0 && git commit -m "test(P0-T03): smoke test three parser page types"`

**Acceptance:** Digital, scanned, and table-heavy pages complete end to end; raw outputs, actual dimensions, postprocessed blocks, and overlays are reproducible. Any failed page blocks the primary-parser gate.

### P0-T04: Verify hosted models and capture exact request contracts

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T01  
**Requirements:** PRD §6, P0, §17 | **Decisions:** D-003, D-004  
**Proof:** `proof/P0/model_matrix.md`, `proof/P0/nim_smoke/*.json`, `config/models.yaml`

**Files:**
- Create: `apps/api/nim_gateway/client.py`, `apps/api/nim_gateway/schemas.py`
- Create: `scripts/smoke_nim.py`
- Test: `apps/api/tests/test_nim_client.py`, `apps/api/tests/fixtures/nim/`

**Interfaces:** Produce `NIMClient.post_json(stage: str, payload: dict) -> dict`; no caller supplies API keys directly.

- [ ] **Step 1: Write failing secret and response tests**

```python
# apps/api/tests/test_nim_client.py
import httpx
import pytest
from nim_gateway.client import NIMClient


def test_client_sends_bearer_secret_without_logging_it():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-secret"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = NIMClient("test-secret", "https://integrate.api.nvidia.com", transport=transport)
    assert client.post_json("embed", {"input": "hello"}) == {"ok": True}


def test_client_never_returns_an_api_key_in_errors():
    client = NIMClient("secret-value", "https://integrate.api.nvidia.com")
    with pytest.raises(ValueError) as error:
        client.redact_error("failed secret-value")
    assert "secret-value" not in str(error.value)
```

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_nim_client.py -v`  
Expected: FAIL on missing gateway.

- [ ] **Step 2: Implement the minimal transport with redaction**

```python
# apps/api/nim_gateway/client.py
import httpx


class NIMClient:
    def __init__(self, api_key: str, base_url: str, transport=None):
        self._api_key = api_key
        self._client = httpx.Client(base_url=base_url, timeout=60, transport=transport)

    def redact_error(self, message: str) -> ValueError:
        return ValueError(message.replace(self._api_key, "[REDACTED]"))

    def post_json(self, stage: str, payload: dict) -> dict:
        response = self._client.post(
            f"/v1/{stage}",
            json=payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        if response.status_code >= 400:
            raise self.redact_error(f"NIM {stage} returned HTTP {response.status_code}")
        data = response.json()
        if not isinstance(data, dict):
            raise TypeError("NIM response must be a JSON object")
        return data
```

The generic route above is only a transport test. Before each live call, configure the exact route from the model page; do not assume every stage uses `/v1/{stage}`.

- [ ] **Step 3: Discover and record each live contract**

For embed, rerank, rewrite, answer, and verify, record the current model-page URL, exact model ID, route, minimal request JSON, response schema, reasoning controls, input-type flags, context/input limits, and early-access status. Save one sanitized minimal success response per model. Configure Super VL and Ultra fallbacks only after smoke-testing those fallback IDs too.

- [ ] **Step 4: Run one minimal live call per hosted stage**

Run: `CITERAG_LIVE_BUDGET_ACK=5 PYTHONPATH=apps/api python scripts/smoke_nim.py --stages embed rerank rewrite answer verify --proof proof/P0/nim_smoke`  
Expected: five successful responses or exact recorded failures with fallback calls. The script must reject missing acknowledgment and redact authorization headers.

Run fixture tests: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_nim_client.py -v`  
Expected: PASS with `httpx.MockTransport`, no live calls.

- [ ] **Step 5: Commit verified configuration and evidence**

Commit: `git add apps/api scripts config/models.yaml proof/P0 && git commit -m "test(P0-T04): verify hosted model contracts"`

**Acceptance:** Model matrix covers every hosted stage and fallback; embedding dimension/input limit and rerank score behavior are measured; exact IDs are not blank for any enabled live stage.

### P0-T05: Measure quota, rate limits, and credit consumption

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T04  
**Requirements:** PRD §11, P0 | **Decisions:** D-003, D-004  
**Proof:** `proof/P0/rate_limits.json`, `proof/P0/quota_report.md`

**Files:**
- Create: `scripts/measure_nim_limits.py`, `apps/api/nim_gateway/budget.py`
- Test: `apps/api/tests/test_live_budget.py`
- Modify: `config/models.yaml`

**Interfaces:** Produce `require_live_budget(acknowledged_calls: str | None, planned_calls: int) -> None`.

- [ ] **Step 1: Write the failing live-budget guard test**

```python
# apps/api/tests/test_live_budget.py
import pytest
from nim_gateway.budget import require_live_budget


def test_live_burst_requires_exact_acknowledgment():
    with pytest.raises(RuntimeError, match="explicit live-call budget"):
        require_live_budget(None, 60)
    with pytest.raises(RuntimeError, match="explicit live-call budget"):
        require_live_budget("5", 60)
    require_live_budget("60", 60)
```

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_live_budget.py -v`  
Expected: FAIL on missing budget module.

- [ ] **Step 2: Implement the guard and burst recorder**

```python
# apps/api/nim_gateway/budget.py
def require_live_budget(acknowledged_calls: str | None, planned_calls: int) -> None:
    if acknowledged_calls is None or int(acknowledged_calls) != planned_calls:
        raise RuntimeError("explicit live-call budget acknowledgment must equal planned calls")
    if planned_calls < 1:
        raise ValueError("planned_calls must be positive")
```

Implement `measure_nim_limits.py` to issue exactly 60 minimal calls to the cheapest verified eligible endpoint, record timestamp, sequence, HTTP status, retry-after and rate/credit headers, latency, and sanitized error bodies. Capture the account's credit balance immediately before and after where the account UI/API exposes it; never infer consumption solely from response count.

- [ ] **Step 3: Verify guard and execute the bounded burst**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_live_budget.py -v`  
Expected: 1 PASS.

Run: `CITERAG_LIVE_BUDGET_ACK=60 PYTHONPATH=apps/api python scripts/measure_nim_limits.py --calls 60 --output proof/P0/rate_limits.json`  
Expected: exactly 60 attempted calls unless the script's safety stop detects exhausted credits; a safety stop is reported with attempted count and reason, not mislabeled a 60-call burst.

- [ ] **Step 4: Derive conservative gateway settings and commit**

Calculate observed successful requests per rolling minute and credit delta. Configure token buckets below any measured hard limit; if headers are absent, label the limit unknown and retain a conservative explicit configuration chosen from observed behavior. Document that a 60-call burst cannot prove a long-term quota.

Commit: `git add apps/api scripts config/models.yaml proof/P0 && git commit -m "test(P0-T05): measure hosted quota and rate limits"`

**Acceptance:** Raw measurements and derivation are reproducible; no secret appears in artifacts; gateway limits come from evidence; unexpected credit exhaustion stops live testing.

### P0-T06: Confirm privacy terms and endpoint availability

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T04  
**Requirements:** PRD §12 Privacy, §16 confidential-data risk, P0 | **Decisions:** D-029, D-033  
**Proof:** `proof/P0/privacy_terms.md`

**Files:**
- Create: `README.md`, `docs/privacy.md`
- Modify: `DECISION.md` only if terms contradict an accepted assumption

- [ ] **Step 1: Capture current first-party terms**

Record dated URLs and relevant quoted clauses from NVIDIA's current terms, privacy policy, API/service-specific terms, and each model page. Address input retention, training/use of submitted data, free-credit expiry, endpoint withdrawal, and whether terms differ by endpoint. Third-party summaries may be leads but cannot be evidence.

- [ ] **Step 2: Write the user-facing privacy warning**

```markdown
# Privacy

CiteRAG sends chunk text, questions, retrieved context, answers, and verifier inputs to hosted NVIDIA endpoints unless a collection is marked confidential. Hosted providers may process or retain those inputs under their current terms. Do not mark a collection non-confidential until you have reviewed `docs/privacy.md` and accepted that transfer. API keys are server-only. Proof and parser artifacts may also contain sensitive source text and must be protected locally.
```

- [ ] **Step 3: Review the warning against every verified endpoint**

Check that enabled and fallback models are covered. If any endpoint prohibits the intended use or cannot be terms-verified, disable it in `config/models.yaml` and record the fallback decision. Do not interpret endpoint availability as permission to upload confidential data.

- [ ] **Step 4: Commit terms and privacy documentation**

Commit: `git add README.md docs/privacy.md config/models.yaml DECISION.md proof/P0/privacy_terms.md && git commit -m "docs(P0-T06): document hosted privacy terms"`

**Acceptance:** Every enabled endpoint has dated availability and terms evidence; README warns before setup; unresolved terms block that endpoint rather than being assumed safe.

### P0-T07: Decide Qdrant versus pgvector

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T04  
**Requirements:** PRD §5 vector-store choice, P0 gate | **Decisions:** D-007, D-005, D-015  
**Proof:** `proof/P0/vector_store_decision.md`

**Files:**
- Modify: `DECISION.md`, `config/storage.yaml`
- Create: `docker-compose.yml`

- [ ] **Step 1: Compare measured constraints**

Record measured embedding dimension and input limit, current pgvector index-type dimension limits from first-party documentation, Qdrant dimension support, required payload filters, expected corpus size, backup implications, and operational complexity. Include URLs and access dates. Do not use an old pgvector dimension cap as a timeless fact.

- [ ] **Step 2: Apply D-007's selection rule**

Choose pgvector only if the selected index supports the measured dimension and required filtered retrieval at the expected corpus size. Otherwise choose Qdrant. Write the result, rejected alternative, migration consequence, and reviewer approval into D-007 and the proof file.

```yaml
# config/storage.yaml; set vector_store to exactly one measured choice.
vector_store: qdrant
postgres:
  full_text_config: simple
qdrant:
  url: http://qdrant:6333
  retrieval_collection: citerag_chunks
  cache_collection_prefix: citerag_embed_cache
```

If pgvector wins, replace Qdrant keys with `pgvector` settings. Copy `vector_dim` programmatically from the verified integer in `config/models.yaml`, and add a configuration test asserting equality so a manually transcribed dimension cannot drift.

- [ ] **Step 3: Add only the selected services to Compose**

Define PostgreSQL with a healthcheck and persistent volume; add Qdrant only if selected. Redis is declared with append-only persistence for Celery. No parse service or hosted API key is embedded in an image. Run `docker compose config -q` and save output.

- [ ] **Step 4: Commit the decision and service definition**

Commit: `git add DECISION.md config/storage.yaml docker-compose.yml proof/P0/vector_store_decision.md && git commit -m "chore(P0-T07): select vector store from measured constraints"`

**Acceptance:** Decision cites measured values and current documentation; Compose contains only selected dependencies; D-007 is no longer pending.

### P0-T08: Validate and close the P0 gate

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T01 through P0-T07  
**Requirements:** PRD P0 proof/gate | **Decisions:** D-001, D-004, D-007, D-008, D-009  
**Proof:** `proof/P0/smoke_report.md`, `proof/P0/gate.json`

**Files:**
- Create: `scripts/check_gate.py`, `packages/common/tests/test_gate.py`
- Modify: `proof/P0/smoke_report.md`

**Interfaces:** Produce `validate_gate(manifest: dict) -> list[str]`; all phases reuse the gate checker.

- [ ] **Step 1: Write failing gate tests**

```python
# packages/common/tests/test_gate.py
from scripts.check_gate import validate_gate


def test_gate_requires_every_declared_artifact():
    errors = validate_gate({"artifacts": [{"path": "proof/P0/missing.json", "exists": False}], "acceptance_passed": True})
    assert errors == ["missing artifact: proof/P0/missing.json"]


def test_gate_rejects_failed_acceptance():
    assert validate_gate({"artifacts": [], "acceptance_passed": False}) == ["acceptance criteria failed"]
```

Run: `python -m pytest packages/common/tests/test_gate.py -v`  
Expected: FAIL on missing gate module.

- [ ] **Step 2: Implement deterministic gate validation**

```python
# scripts/check_gate.py
def validate_gate(manifest: dict) -> list[str]:
    errors = [
        f"missing artifact: {item['path']}"
        for item in manifest["artifacts"]
        if not item["exists"]
    ]
    if not manifest["acceptance_passed"]:
        errors.append("acceptance criteria failed")
    return errors
```

The CLI loads a JSON manifest, checks each path itself, verifies nonempty files, prints every error, and exits 1 on any failure. A manifest cannot override filesystem absence by setting `exists=true`.

- [ ] **Step 3: Assemble the P0 manifest and review all evidence**

Include repository/environment reports, three raw parse outputs and overlays, hosted response matrix, measured limits, terms, vector decision, and effective `config/models.yaml`. Verify all six required models respond or D-009/D-004 fallbacks are selected and recorded. Manually sign each acceptance row with pass/fail evidence.

- [ ] **Step 4: Run the gate and commit**

Run: `python scripts/check_gate.py proof/P0/manifest.json --output proof/P0/gate.json`  
Expected: exit 0 and `{"phase":"P0","passed":true}` with artifact hashes. Any failure leaves P0 open.

Commit: `git add scripts packages/common/tests/test_gate.py proof/P0 TASKS.md && git commit -m "test(P0-T08): close environment smoke gate"`

**Acceptance:** Independent reviewer can reproduce every P0 conclusion from committed artifacts; P1 remains blocked until this task is Done.

---

# P1 — Ingestion and Parsing

**Entry:** P0 gate passed; primary parser or approved fallback emits usable structured blocks.  
**Exit gate:** Ten varied pages pass manual text/bbox review; retries and failures are visible; concurrency is selected from measured VRAM/timing.

### P1-T01: Create the relational schema and migration foundation

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T08  
**Requirements:** PRD §8, §12 | **Decisions:** D-005, D-029, D-030, D-031, D-032  
**Proof:** `proof/P1/schema.md`

**Files:**
- Create: `alembic.ini`, `alembic/env.py`, `alembic/versions/0001_initial.py`
- Create: `packages/common/citerag_common/db.py`, `packages/common/citerag_common/models.py`
- Test: `packages/common/tests/test_schema.py`

**Interfaces:** Produce SQLAlchemy `SessionLocal`, `Base`, and all PRD table models; collection confidentiality defaults true.

- [ ] **Step 1: Write failing schema invariant tests against PostgreSQL**

```python
# packages/common/tests/test_schema.py
from sqlalchemy import create_mock_engine
from citerag_common.models import Base


def test_initial_metadata_contains_required_tables():
    expected = {"users", "collections", "documents", "pages", "blocks", "chunks", "chunk_blocks", "embed_cache", "conversations", "messages", "eval_runs", "auth_sessions"}
    assert expected <= set(Base.metadata.tables)


def test_confidential_defaults_true():
    assert Base.metadata.tables["collections"].c.confidential.default.arg is True
```

Run: `python -m pytest packages/common/tests/test_schema.py -v`  
Expected: FAIL on missing models.

- [ ] **Step 2: Implement SQLAlchemy models and initial Alembic migration**

Use UUID primary keys with `gen_random_uuid()`, UTC `timestamptz`, foreign keys, and JSONB for bbox/raw audit fields. Include every PRD column plus `documents.storage_key`, `mime_type`, `byte_count`, `index_status`, `deletion_status`, `chunks.lang`, and `collections.confidential`. Add collection privacy acknowledgment fields `privacy_terms_version`, `privacy_acknowledged_at`, and `privacy_acknowledged_by`. Add `privacy_audit(id,collection_id,actor_user_id,previous_confidential,new_confidential,terms_version,trace_id,created_at)` so early CLI overrides and later API overrides share one audit trail. Add `auth_sessions(id,user_id,token_hash,expires_at,revoked_at,created_at)` and a partial unique index on active `(collection_id,sha256)` documents.

Create `embed_cache` with primary key `(text_sha256,model)` plus `request_semantics_hash`, `vector_dim`, `vector_ref`, and `created_at`. Add `chunk_blocks(chunk_id,block_id,order_idx)` with primary key `(chunk_id,block_id)` and ordered cascade behavior. Do not store original file bytes in PostgreSQL.

- [ ] **Step 3: Verify upgrade, downgrade, and database constraints**

Run: `docker compose up -d postgres && alembic upgrade head && alembic downgrade base && alembic upgrade head`  
Expected: all migrations succeed. Run integration tests proving duplicate active hashes fail, duplicate collection names for one user fail, confidential defaults true, and deleting a user restricts rather than silently leaks related objects.

- [ ] **Step 4: Save schema proof and commit**

Run: `python -m pytest packages/common/tests/test_schema.py -v` and `alembic current`.  
Expected: tests PASS and current revision `0001`. Save `alembic history --verbose`, table DDL, and constraint-test output in `schema.md`.

Commit: `git add alembic.ini alembic packages/common proof/P1/schema.md && git commit -m "feat(P1-T01): add relational persistence schema"`

**Acceptance:** Clean and upgraded databases reach identical schema; provenance links and confidentiality/uniqueness constraints are enforced by PostgreSQL, not only Python.

### P1-T02: Implement private collections and validated upload API

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T01  
**Requirements:** PRD FR-ING-1, FR-UI-1, API collections/upload/file | **Decisions:** D-006, D-011, D-028, D-029, D-032  
**Proof:** `proof/P1/upload_api.md`

**Files:**
- Create: `packages/common/citerag_common/files.py`
- Create: `apps/api/app/dependencies.py`, `apps/api/app/routers/collections.py`, `apps/api/app/routers/documents.py`
- Test: `packages/common/tests/test_files.py`, `apps/api/tests/test_documents.py`

**Interfaces:** Produce `validate_upload(filename: str, header: bytes, size: int, cap: int) -> str`, `FileStore.put(stream, suffix: str, size_cap: int) -> StoredFile`, and upload response `{document_id, duplicate, status}`. `StoredFile` contains `key`, `sha256`, and `byte_count`.

- [ ] **Step 1: Write failing signature, cap, and duplicate tests**

```python
# packages/common/tests/test_files.py
import pytest
from citerag_common.files import validate_upload


def test_validates_real_file_signatures_and_size():
    assert validate_upload("a.pdf", b"%PDF-1.7\n", 9, 100) == "pdf"
    assert validate_upload("a.png", b"\x89PNG\r\n\x1a\n", 12, 100) == "png"
    assert validate_upload("a.jpg", b"\xff\xd8\xff\xe0", 8, 100) == "jpg"
    with pytest.raises(ValueError, match="file type"):
        validate_upload("a.pdf", b"<html>", 6, 100)
    with pytest.raises(ValueError, match="size cap"):
        validate_upload("a.pdf", b"%PDF-1.7\n", 101, 100)
```

Add API tests where two uploads of the same bytes in one collection return the same ID with `duplicate=true`, another collection may accept the file, and a new collection has `confidential=true`.

- [ ] **Step 2: Run tests and confirm missing implementation**

Run: `python -m pytest packages/common/tests/test_files.py apps/api/tests/test_documents.py -v`  
Expected: FAIL on missing file/upload modules, not fixture syntax errors.

- [ ] **Step 3: Implement streaming validation and atomic storage**

```python
# packages/common/citerag_common/files.py
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

_SIGNATURES = {"pdf": b"%PDF-", "png": b"\x89PNG\r\n\x1a\n", "jpg": b"\xff\xd8\xff"}


def validate_upload(filename: str, header: bytes, size: int, cap: int) -> str:
    if size > cap:
        raise ValueError("size cap exceeded")
    suffix = Path(filename).suffix.lower()
    expected = {"pdf": ".pdf", "png": ".png", "jpg": ".jpg"}
    for kind, signature in _SIGNATURES.items():
        if header.startswith(signature):
            if suffix != expected[kind] and not (kind == "jpg" and suffix == ".jpeg"):
                raise ValueError("file type and extension disagree")
            return kind
    raise ValueError("unsupported file type")


@dataclass(frozen=True)
class StoredFile:
    key: str
    sha256: str
    byte_count: int


class FileStore:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root not in path.parents:
            raise ValueError("invalid storage key")
        return path

    def put(self, stream: BinaryIO, suffix: str, size_cap: int) -> StoredFile:
        temporary = self.path_for(f".{uuid4().hex}.tmp")
        digest = sha256()
        size = 0
        try:
            with temporary.open("xb") as output:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    size += len(chunk)
                    if size > size_cap:
                        raise ValueError("size cap exceeded")
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            key = f"{digest.hexdigest()}{suffix}"
            os.replace(temporary, self.path_for(key))
            return StoredFile(key, digest.hexdigest(), size)
        finally:
            temporary.unlink(missing_ok=True)
```

The upload endpoint reserves the duplicate constraint transactionally and returns the existing active document on conflict.

- [ ] **Step 4: Verify endpoints and private file retrieval**

Run: `python -m pytest packages/common/tests/test_files.py apps/api/tests/test_documents.py -v`  
Expected: all PASS. Tests cover GET/POST collections, multipart upload, `GET /documents/{id}`, authorized `GET /documents/{id}/file`, nosniff header, byte-range PDF response, invalid signature, oversized stream, and retry after client disconnect.

- [ ] **Step 5: Save HTTP evidence and commit**

Commit: `git add packages/common apps/api proof/P1/upload_api.md && git commit -m "feat(P1-T02): add private validated document uploads"`

**Acceptance:** No public static upload route exists; path traversal and spoofed extensions fail; duplicates create no second job; original files stream with correct media type.

### P1-T03: Render pages and convert bounding boxes exactly

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T02  
**Requirements:** PRD FR-ING-2, FR-ING-5 | **Decisions:** D-010, D-025  
**Proof:** `proof/P1/render_geometry.md`

**Files:**
- Create: `apps/worker/tasks/render.py`, `packages/common/citerag_common/geometry.py`
- Test: `packages/common/tests/test_geometry.py`, `apps/worker/tests/test_render.py`

**Interfaces:** Produce `fit_render(width: int, height: int) -> tuple[int,int,float]` and `pixels_to_pdf(box, scale_to_pdf: float) -> BBoxPDF`.

- [ ] **Step 1: Write failing downscale and round-trip tests**

```python
# packages/common/tests/test_geometry.py
import pytest
from citerag_common.geometry import fit_render, pixels_to_pdf


def test_oversized_render_preserves_aspect_ratio():
    width, height, scale = fit_render(2000, 4000)
    assert (width, height) == (1024, 2048)
    assert scale == pytest.approx(0.512)


def test_pdf_points_use_actual_scale():
    assert pixels_to_pdf((100.0, 200.0, 300.0, 400.0), 72 / 150) == (48.0, 96.0, 144.0, 192.0)
    assert pixels_to_pdf((100.0, 200.0, 300.0, 400.0), 72 / (150 * 0.5)) == (96.0, 192.0, 288.0, 384.0)
```

`scale_to_pdf` equals `72 / (150 * downscale_factor)`. Also test a no-downscale A4 render against PyMuPDF page dimensions within 0.01 point.

- [ ] **Step 2: Run tests, then implement pure geometry**

Run: `python -m pytest packages/common/tests/test_geometry.py -v`  
Expected: FAIL on missing geometry module.

```python
# packages/common/citerag_common/geometry.py
def fit_render(width: int, height: int) -> tuple[int, int, float]:
    factor = min(1.0, 1664 / width, 2048 / height)
    return round(width * factor), round(height * factor), factor


def pixels_to_pdf(box, scale_to_pdf: float):
    return tuple(round(value * scale_to_pdf, 6) for value in box)
```

Render at 150 dpi first, then pass actual pixel dimensions through `fit_render`. Persist `scale_to_pdf=72/(150*factor)`. RGB conversion must drop alpha rather than composite transparency unpredictably.

- [ ] **Step 3: Add PDF and image rendering**

For PDFs, use `page.get_pixmap(dpi=150, colorspace=fitz.csRGB, alpha=False)` and downscale the rendered image only when required. For PNG/JPG, create one logical 150-dpi page, apply the same size cap, retain original image media type, and store both pixel and logical PDF-point coordinates. P6 uses pixel coordinates against actual image dimensions for image highlights.

- [ ] **Step 4: Verify varied pages and commit**

Run: `python -m pytest packages/common/tests/test_geometry.py apps/worker/tests/test_render.py -v`  
Expected: PASS for A4, Letter, landscape, huge scan, transparent PNG, rotated JPEG, and one-page image documents. Record actual dimensions/scales and overlay spot checks.

Commit: `git add apps/worker packages/common proof/P1/render_geometry.md && git commit -m "feat(P1-T03): render pages with exact citation geometry"`

**Acceptance:** Aspect ratio and page rotation are preserved; conversion uses actual scale; no zero/negative box survives validation; image and PDF provenance remain distinguishable.

### P1-T04: Postprocess parser output into persistent typed blocks

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T03, P1-T03  
**Requirements:** PRD FR-ING-3 through FR-ING-5, FR-CHK-1 | **Decisions:** D-004, D-008, D-009, D-010  
**Proof:** `proof/P1/postprocess_contract.md`, `proof/P1/classes.json`

**Files:**
- Create: `apps/parse_service/parse_service/postprocess.py`, `apps/worker/tasks/parse.py`
- Create: `config/parser_classes.yaml`
- Test: `apps/parse_service/tests/test_postprocess.py`

**Interfaces:** Produce `postprocess_page(raw: str, render_w: int, render_h: int, scale_to_pdf: float) -> tuple[str,list[ParsedBlock]]`.

- [ ] **Step 1: Write a failing real-output fixture test**

Use the unedited P0 table raw output as a fixture. Assert postprocessing returns markdown, ordered blocks, actual class strings, normalized/pixel/PDF bboxes, and exact text. Assert a malformed bbox is rejected with page/block context and raw output remains retrievable.

Run: `PYTHONPATH=apps/parse_service python -m pytest apps/parse_service/tests/test_postprocess.py -v`  
Expected: FAIL on missing adapter.

- [ ] **Step 2: Implement the official postprocess adapter**

Call the parser version's official `postprocess_document` with actual render dimensions. Do not reimplement its control-token grammar. Convert its result into `ParsedBlock`, calculate `bbox_pdf` with P1-T03, preserve source ordering, and validate `0 <= x0 <= x1 <= render_w` and equivalent y bounds. Store raw model output before raising a postprocess error.

- [ ] **Step 3: Persist raw pages and blocks idempotently**

Key parser work by `(page_id, parser_config_hash)`. A repeated successful result updates the same page/blocks in one transaction rather than duplicating blocks. Record `parse_ms`, parser model ID, request settings hash, raw output, markdown, and postprocessor version.

- [ ] **Step 4: Verify fixtures and record actual class names**

Run: `PYTHONPATH=apps/parse_service:packages/common python -m pytest apps/parse_service/tests/test_postprocess.py apps/worker/tests -v`  
Expected: PASS. Generate `classes.json` from real outputs, map header/footer/page-number/table/chart/paragraph classes in `parser_classes.yaml`, and leave unmapped classes visible for review rather than silently indexing them as paragraphs.

- [ ] **Step 5: Commit adapter and class contract**

Commit: `git add apps/parse_service apps/worker config/parser_classes.yaml proof/P1 && git commit -m "feat(P1-T04): persist parsed blocks with provenance"`

**Acceptance:** Raw output survives every failure; reprocessing is idempotent; real class names drive later chunking; bbox and text fixture tests pass.

### P1-T05: Build resumable Celery ingestion with page-level failure isolation

**Status:** Not started | **Owner:** Atharva  
**Requirements:** PRD FR-ING-6 through FR-ING-8, §12 Reliability | **Decisions:** D-003, D-008, D-031, D-033  
**Depends on:** P1-T04  
**Proof:** `proof/P1/reliability.md`, `proof/P1/restart_logs/`

**Files:**
- Create: `apps/worker/celery_app.py`, `apps/worker/tasks/ingest.py`, `apps/worker/tasks/states.py`
- Test: `apps/worker/tests/test_states.py`, `apps/worker/tests/test_ingest_recovery.py`

**Interfaces:** Produce `next_page_state(attempts: int, error: Exception) -> tuple[str,bool]` and idempotent `ingest_document(document_id: str)`.

- [ ] **Step 1: Write failing retry and outage tests**

```python
# apps/worker/tests/test_states.py
from apps.worker.tasks.states import ParseOutage, next_page_state


def test_page_retries_twice_then_fails_without_sibling_failure():
    assert next_page_state(0, ValueError("bad page")) == ("parsing", True)
    assert next_page_state(1, ValueError("bad page")) == ("parsing", True)
    assert next_page_state(2, ValueError("bad page")) == ("failed", False)


def test_outage_pauses_instead_of_consuming_page_retry():
    assert next_page_state(0, ParseOutage("offline")) == ("paused", False)
    assert next_page_state(2, ParseOutage("offline")) == ("paused", False)
```

Run: `python -m pytest apps/worker/tests/test_states.py -v`  
Expected: FAIL on missing state module.

- [ ] **Step 2: Implement explicit state transitions**

```python
# apps/worker/tasks/states.py
class ParseOutage(RuntimeError):
    pass


def next_page_state(attempts: int, error: Exception) -> tuple[str, bool]:
    if isinstance(error, ParseOutage):
        return "paused", False
    if attempts < 2:
        return "parsing", True
    return "failed", False
```

Celery tasks use database-backed leases with expiration, not Celery's redelivery alone. A worker recovers expired leases after restart. Successful page/config pairs are skipped. Queue stages are `queued → rendering → parsing → chunking → embedding → indexed`; any failed pages produce indexed-with-page-errors metadata rather than discarding good pages.

- [ ] **Step 3: Implement health-based pause and confidential indexing guard**

Before parsing, check local service health with a short timeout and raise `ParseOutage` on connection/ready failures. Before embedding, reject collections with `confidential=true` using a non-retryable `ConfidentialCollectionBlocked`; leave locally parsed data intact and status `blocked_confidential`.

- [ ] **Step 4: Run failure injection and restart tests**

Run: `python -m pytest apps/worker/tests -v`  
Expected: PASS for worker kill after page commit, duplicate delivery, two retries then failed page, sibling success, parse outage/resume, and confidential block. Save before/after page counts and job IDs from a real worker restart.

- [ ] **Step 5: Commit the reliable pipeline**

Commit: `git add apps/worker apps/api packages/common proof/P1/reliability.md proof/P1/restart_logs && git commit -m "feat(P1-T05): make ingestion resumable and page isolated"`

**Acceptance:** No duplicate blocks after restart/redelivery; outage consumes zero permanent retries; three unsuccessful page attempts mark only that page failed; confidential content never reaches embedding.

### P1-T06: Expose document progress, blocks, health, and recoverable deletion

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T05  
**Requirements:** PRD FR-ING-7, API document/status/file/blocks/delete/health | **Decisions:** D-005, D-006, D-031, D-033  
**Proof:** `proof/P1/document_api.md`

**Files:**
- Modify: `apps/api/app/routers/documents.py`, `apps/api/app/main.py`
- Create: `apps/api/app/routers/health.py`, `apps/worker/tasks/delete.py`
- Test: `apps/api/tests/test_document_status.py`, `apps/api/tests/test_delete.py`

**Interfaces:** Produce document response `{id,status,page_count,processed_pages,failed_pages,current_stage,trace_id}` and idempotent DELETE response `{id,status:"deleting"}`.

- [ ] **Step 1: Write failing status and deletion tests**

Test queued/rendering/parsing/chunking/embedding/indexed states, page counts, partial page failure, repeated DELETE, a failed vector cleanup retry, file-not-found after completed deletion, and health degradation when parse/Postgres/vector/NIM checks fail. NIM health uses a cached or account-level check and cannot spend a generation call per probe.

- [ ] **Step 2: Implement explicit status serialization and cleanup states**

Use SQL counts grouped by page status; never infer progress from log messages. DELETE transitions `active → deleting → deleted`, disables search immediately, schedules idempotent vector/file/metadata cleanup, and retains a deletion error with retry count on failure. Cache vectors survive per D-015.

- [ ] **Step 3: Verify HTTP contracts and health behavior**

Run: `python -m pytest apps/api/tests/test_document_status.py apps/api/tests/test_delete.py -v`  
Expected: PASS, including `GET /documents/{id}/pages/{n}/blocks` returning one-based page selection and PDF/image coordinate fields.

Run: `curl --fail http://127.0.0.1:8000/health` with dependencies healthy, then stop the parse service and repeat.  
Expected: degraded readiness identifies parse without exposing connection credentials.

- [ ] **Step 4: Save API responses and commit**

Commit: `git add apps/api apps/worker proof/P1/document_api.md && git commit -m "feat(P1-T06): add ingestion status and deletion APIs"`

**Acceptance:** UI can render exact progress without parsing logs; deletion is retryable and non-searchable immediately; health distinguishes liveness/readiness.

### P1-T07: Review ten overlays and lock parser class mappings

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T04, P1-T06  
**Requirements:** PRD P1 proof/gate, FR-CHK-1, FR-CHK-2 | **Decisions:** D-008, D-010, D-012  
**Proof:** `proof/P1/overlays/*.png`, `proof/P1/parse_json/*.json`, `proof/P1/manual_review.md`

**Files:**
- Modify: `scripts/overlay.py`, `config/parser_classes.yaml`
- Test: `apps/parse_service/tests/test_overlay.py`

- [ ] **Step 1: Add failing overlay geometry tests**

Use a known 100×200 image and two boxes; assert saved overlay pixels match expected colors/coordinates and labels do not alter block coordinates. Include downscaled and rotated-page fixtures.

Run: `PYTHONPATH=apps/parse_service python -m pytest apps/parse_service/tests/test_overlay.py -v`  
Expected: FAIL until overlay uses persisted pixel boxes rather than recomputing them from normalized values.

- [ ] **Step 2: Implement overlay output directly from stored blocks**

Draw `bbox_px` over the exact stored render, attach block ID/class/order, and emit a sidecar JSON linking every drawn rectangle to its database block. Verify with Step 1's command; expected PASS.

- [ ] **Step 3: Select and process ten varied pages**

Include digital, scanned, table-heavy, chart, multi-column, landscape, downscaled, Hindi, Marathi, and a deliberately failing page. Process through the real worker. Manually compare every page's text and boxes; record each miss by block ID and severity. Do not hand-edit parse JSON.

- [ ] **Step 4: Finalize class mapping and commit evidence**

Map observed classes to index/exclude behavior. Unknown classes fail a validation report until explicitly mapped. Commit: `git add scripts config/parser_classes.yaml apps/parse_service/tests proof/P1 && git commit -m "test(P1-T07): review parser overlays and semantic classes"`

**Acceptance:** Ten overlays and raw/postprocessed JSON exist; manual text matches source; boxes land on correct regions; failed-page reporting is demonstrated; class mapping covers all observed classes.

### P1-T08: Benchmark parser concurrency and resource use

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T07  
**Requirements:** PRD FR-ING-8, P1 proof/gate | **Decisions:** D-008  
**Proof:** `proof/P1/concurrency.csv`, `proof/P1/concurrency.md`

**Files:**
- Create: `scripts/benchmark_parse.py`, `config/worker.yaml`
- Test: `apps/worker/tests/test_concurrency_config.py`

- [ ] **Step 1: Write failing configuration-bound tests**

Assert configured concurrency is one of measured `[1,2,4,8]`, is positive, and has a proof file with matching value. Run the test; expected FAIL because no selection exists.

- [ ] **Step 2: Implement a repeatable benchmark**

For each concurrency 1, 2, 4, and 8, run the same representative page batch after a warm-up. Record per-request latency, pages/second, failures, GPU utilization, and peak VRAM using synchronized samples from `nvidia-smi`. Do not benchmark all levels simultaneously.

Run: `python scripts/benchmark_parse.py --levels 1 2 4 8 --output proof/P1/concurrency.csv`  
Expected: four complete rows or a recorded OOM/failure row; failed levels remain in the report.

- [ ] **Step 3: Select and verify the operating point**

Choose the highest safe throughput point that leaves documented VRAM headroom and acceptable page latency; do not automatically choose 8. Write value and rationale to `config/worker.yaml`, rerun the configuration test, and confirm PASS.

- [ ] **Step 4: Commit benchmark and selection**

Commit: `git add scripts config/worker.yaml apps/worker/tests proof/P1 && git commit -m "test(P1-T08): select measured parser concurrency"`

**Acceptance:** Timing/VRAM table includes 1/2/4/8; selected concurrency matches config and proof; OOM or instability is documented rather than omitted.

### P1-T09: Close the ingestion gate

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T01 through P1-T08  
**Requirements:** PRD P1 gate | **Decisions:** D-001, D-008, D-010  
**Proof:** `proof/P1/gate.json`, `proof/P1/gate_review.md`

**Files:**
- Create: `proof/P1/manifest.json`, `proof/P1/gate_review.md`, `proof/P1/gate.json`
- Modify: `TASKS.md`

- [ ] **Step 1: Assemble artifact manifest and regression evidence**

Include schema, upload/API, geometry, raw outputs, ten overlays, class mappings, manual review, restart/retry logs, and concurrency results. Run `python -m pytest packages/common/tests apps/api/tests apps/worker/tests apps/parse_service/tests -v`; expected all PASS with zero live NIM requests.

- [ ] **Step 2: Review gate rows against artifacts**

For each PRD P1 sentence, link a file and exact test/manual row. Any unmatched row sets `acceptance_passed=false` and gets a concrete repair task before rerun.

- [ ] **Step 3: Execute gate and commit**

Run: `python scripts/check_gate.py proof/P1/manifest.json --output proof/P1/gate.json`  
Expected: exit 0. Commit: `git add proof/P1 TASKS.md && git commit -m "test(P1-T09): close ingestion parsing gate"`

**Acceptance:** Ten-page manual review, retry/resume, class coverage, and measured concurrency all pass; P2 is unblocked only by committed gate JSON.

# P2 — Chunking and Indexing

**Entry:** P1 gate passed; actual parser classes and measured embedding constraints exist.  
**Exit gate:** Three document chunk dumps pass provenance/size review, ten table chunks retain HTML, and unchanged re-ingestion spends zero embedding calls.

### P2-T01: Implement tokenizer-aware text chunking

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T09  
**Requirements:** PRD FR-CHK-3, FR-CHK-9 | **Decisions:** D-012  
**Proof:** `proof/P2/text_chunk_tests.md`

**Files:**
- Create: `packages/chunking/chunking/policy.py`, `packages/chunking/chunking/text.py`, `packages/chunking/chunking/tokenizer.py`
- Test: `packages/chunking/tests/test_text_chunker.py`, `packages/chunking/tests/factories.py`

**Interfaces:** Produce `ChunkPolicy(target=600, maximum=800, overlap=72)`, `count_tokens(text: str) -> int`, and `pack_blocks(blocks, policy) -> list[list[ParsedBlock]]`.

- [ ] **Step 1: Write failing boundary and overlap tests**

```python
# packages/chunking/tests/test_text_chunker.py
from chunking.policy import ChunkPolicy
from chunking.text import pack_blocks
from factories import block


def test_never_splits_a_normal_block_and_reuses_tail_overlap():
    blocks = [block(str(i), "paragraph", 300) for i in range(5)]
    groups = pack_blocks(blocks, ChunkPolicy(target=600, maximum=800, overlap=72))
    assert [b.id for b in groups[0]] == ["0", "1"]
    assert groups[1][0].id == "1"
    assert all(sum(b.token_count for b in group) <= 800 for group in groups)


def test_only_oversized_block_is_split():
    groups = pack_blocks([block("x", "paragraph", 1600)], ChunkPolicy(600, 800, 72))
    assert len(groups) > 1
    assert all(part.is_split for group in groups for part in group)
```

Use a deterministic whitespace-token fixture for algorithm tests and a separate integration test with the real tokenizer selected below.

```python
# packages/chunking/tests/factories.py
from types import SimpleNamespace


def block(block_id: str, class_name: str, token_count: int):
    return SimpleNamespace(
        id=block_id,
        class_name=class_name,
        token_count=token_count,
        text=" ".join(["word"] * token_count),
        is_split=False,
    )
```

- [ ] **Step 2: Run tests and confirm missing implementation**

Run: `python -m pytest packages/chunking/tests/test_text_chunker.py -v`  
Expected: FAIL on missing chunking modules.

- [ ] **Step 3: Implement policy, tokenizer adapter, and deterministic packing**

```python
# packages/chunking/chunking/policy.py
from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkPolicy:
    target: int = 600
    maximum: int = 800
    overlap: int = 72

    def __post_init__(self):
        if not 0 < self.target <= self.maximum:
            raise ValueError("target must be positive and no greater than maximum")
        if not 0 <= self.overlap < self.target:
            raise ValueError("overlap must be nonnegative and below target")
```

Use the measured embedding tokenizer when available. Otherwise implement a documented Unicode-aware proxy, compare it against samples from the real model tokenizer, and set the effective maximum below the measured input limit by the observed worst-case margin plus 10%. Never change the displayed `text` to include section paths. Packing retains whole blocks, flushes at the target/maximum boundary, and starts the next group with the smallest whole-block tail covering about 12% of the target. Split only a block whose own token count exceeds the effective maximum; split at paragraph, sentence, then Unicode whitespace boundaries without dropping text.

- [ ] **Step 4: Verify token invariants and real tokenizer behavior**

Run: `python -m pytest packages/chunking/tests -v`  
Expected: PASS for empty text, Devanagari, paragraphs, long unbroken strings, exact maximum, overlap loops, and no lost/reordered source text. Record proxy comparison if used.

- [ ] **Step 5: Commit the pure chunker**

Commit: `git add packages/chunking proof/P2/text_chunk_tests.md && git commit -m "feat(P2-T01): add tokenizer aware text chunking"`

**Acceptance:** Deterministic output, no normal block cuts, no infinite overlap loops, all chunks below the lower of 800 and safe embedding limit, and no text loss across splits.

### P2-T02: Implement table and chart chunks with safe display HTML

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P2-T01  
**Requirements:** PRD FR-CHK-4, FR-CHK-5, FR-UI-6 | **Decisions:** D-012, D-028  
**Proof:** `proof/P2/table_chart_contract.md`

**Files:**
- Create: `packages/chunking/chunking/tables.py`, `packages/chunking/chunking/charts.py`
- Test: `packages/chunking/tests/test_tables.py`, `packages/chunking/tests/test_charts.py`

**Interfaces:** Produce `chunk_table(table: TableBlock, policy: ChunkPolicy) -> list[Chunk]` and `chunk_chart(chart: ParsedBlock) -> Chunk`.

- [ ] **Step 1: Write failing row-split and sanitization tests**

```python
# packages/chunking/tests/test_tables.py
from chunking.tables import flatten_rows, split_rows, safe_table_html


def test_split_repeats_header_and_preserves_row_order():
    groups = split_rows(["Name", "Value"], [["A", "1"], ["B", "2"]], lambda rows: len(rows), 2)
    assert groups == [[["Name", "Value"], ["A", "1"]], [["Name", "Value"], ["B", "2"]]]


def test_flattened_text_and_html_are_safe_and_row_wise():
    assert flatten_rows(["Name", "Value"], [["A", "1"]]) == "Name: Name | Value: Value\nName: A | Value: 1"
    assert safe_table_html('<table><tr><td onclick="x()">A</td><script>x()</script></tr></table>') == "<table><tr><td>A</td></tr></table>"
```

Also test a 1,201-token table splits, a table below the safe embedding limit stays whole, a single oversized row uses deterministic cell splitting while retaining header context, and chart text contains only parser-extracted data plus caption.

- [ ] **Step 2: Run tests and implement table/chart transformations**

Run: `python -m pytest packages/chunking/tests/test_tables.py packages/chunking/tests/test_charts.py -v`  
Expected: FAIL on missing modules.

```python
# packages/chunking/chunking/tables.py
from dataclasses import dataclass
import nh3
from citerag_common.contracts import ParsedBlock


@dataclass(frozen=True)
class TableBlock:
    block: ParsedBlock
    header: list[str]
    rows: list[list[str]]


def flatten_rows(header, rows):
    lines = [" | ".join(f"{name}: {name}" for name in header)]
    lines.extend(" | ".join(f"{name}: {value}" for name, value in zip(header, row)) for row in rows)
    return "\n".join(lines)


def safe_table_html(html: str) -> str:
    return nh3.clean(
        html,
        tags={"table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption"},
        attributes={"th": {"colspan", "rowspan"}, "td": {"colspan", "rowspan"}},
    )


def split_rows(header, rows, token_count, maximum):
    if token_count([header] + rows) <= maximum:
        return [[header] + rows]
    groups, current = [], []
    for row in rows:
        candidate = current + [row]
        if current and token_count([header] + candidate) > maximum:
            groups.append([header] + current)
            current = [row]
        else:
            current = candidate
    if current:
        groups.append([header] + current)
    return groups
```

The production token counter includes repeated header and flattening overhead. `chunk_chart` concatenates nonempty extracted data and caption with stable labels, never inferred chart values.

- [ ] **Step 3: Verify fixtures and ten real tables**

Run: `python -m pytest packages/chunking/tests/test_tables.py packages/chunking/tests/test_charts.py -v`  
Expected: PASS. Run ten P1 table blocks through the chunker; save source HTML, sanitized HTML, flattened text, row ranges, and token counts in the proof artifact.

- [ ] **Step 4: Commit special chunk handlers**

Commit: `git add packages/chunking pyproject.toml proof/P2/table_chart_contract.md && git commit -m "feat(P2-T02): add safe table and chart chunks"`

**Acceptance:** Every split repeats headers, order/provenance survive, display HTML is sanitized before storage, chart values are not invented, and no special chunk exceeds the safe embedding limit.

### P2-T03: Add section paths, exclusions, and conservative continuations

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P2-T02  
**Requirements:** PRD FR-CHK-2, FR-CHK-6, FR-CHK-7, FR-CHK-8 | **Decisions:** D-012, D-013  
**Proof:** `proof/P2/continuation_review.md`

**Files:**
- Create: `packages/chunking/chunking/sections.py`, `packages/chunking/chunking/continuation.py`, `packages/chunking/chunking/chunker.py`
- Test: `packages/chunking/tests/test_sections.py`, `packages/chunking/tests/test_continuation.py`

**Interfaces:** Produce `update_section_path(stack: list[str], heading: str) -> list[str]`, `detect_continuation(previous: Chunk, following: Chunk) -> bool`, and `build_chunks(document_id, blocks) -> list[Chunk]`.

- [ ] **Step 1: Write failing section and continuation tests**

```python
# packages/chunking/tests/test_continuation.py
from chunking.continuation import paragraph_continues


def test_paragraph_continuation_requires_adjacent_pages_and_unfinished_text():
    assert paragraph_continues("Revenue increased because", "demand doubled.", 3, 4)
    assert not paragraph_continues("Revenue increased.", "Demand doubled.", 3, 4)
    assert not paragraph_continues("Revenue increased because", "demand doubled.", 3, 5)


def test_devanagari_danda_is_terminal_punctuation():
    assert not paragraph_continues("राजधानी मुंबई आहे।", "हे महाराष्ट्रात आहे.", 1, 2)
```

Test section stack `Report > 3 Risks > 3.2 Credit`, exclusion of configured header/footer/page-number classes from chunks but not blocks storage, and table continuation only when adjacent pages have compatible headers/column counts.

- [ ] **Step 2: Implement deterministic rules and run tests**

```python
# packages/chunking/chunking/continuation.py
def paragraph_continues(previous: str, following: str, previous_page: int, following_page: int) -> bool:
    if following_page != previous_page + 1 or not previous.strip() or not following.strip():
        return False
    return previous.rstrip()[-1] not in ".!?।॥:;"


def update_section_path(stack: list[str], heading: str) -> list[str]:
    parts = heading.strip().split(maxsplit=1)
    if parts and parts[0].count(".") >= 1 and parts[0][0].isdigit():
        depth = parts[0].count(".") + 1
        return stack[: depth - 1] + [heading.strip()]
    if parts and parts[0].isdigit():
        return stack[:1] + [heading.strip()]
    return [heading.strip()]
```

Prepend `section_path` only to `embed_text` as `Section: {path}\n\n{text}`. Link `continues_from` only for adjacent pages with matching chunk type and the tested table/paragraph rules. Retain each chunk's original blocks and page range; never merge source text merely because chunks link.

- [ ] **Step 3: Evaluate heuristic precision on labeled examples**

Create at least 30 adjacent-page candidate pairs covering true/false paragraph and table continuations in English, Hindi, and Marathi. Record false positives and false negatives. Tune only deterministic rules, rerun all tests, and attach labeled predictions to `continuation_review.md`.

- [ ] **Step 4: Commit assembly logic and review**

Commit: `git add packages/chunking proof/P2/continuation_review.md && git commit -m "feat(P2-T03): add sections and continuation links"`

**Acceptance:** Display text has no section prefix; excluded classes remain in blocks; every chunk maps to ordered blocks/bboxes; continuation links are conservative and evaluated on labeled pairs.

### P2-T04: Complete resilient NIM gateway and model-aware embedding cache

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T05, P2-T01  
**Requirements:** PRD FR-IDX-1, FR-IDX-4, §6 fallbacks, §11 | **Decisions:** D-003, D-004, D-014, D-015  
**Proof:** `proof/P2/gateway_cache.md`

**Files:**
- Create: `apps/api/nim_gateway/gateway.py`, `apps/api/nim_gateway/retry.py`, `apps/api/nim_gateway/embeddings.py`, `apps/api/nim_gateway/privacy.py`
- Create: `scripts/set_collection_privacy.py`
- Modify: `packages/common/citerag_common/models.py`
- Test: `apps/api/tests/test_gateway_retry.py`, `apps/api/tests/test_embedding_cache.py`, `apps/api/tests/test_transfer_guard.py`

**Interfaces:** Produce `NIMGateway.call(stage: str, payload: dict, context: CallContext) -> dict`, `EmbeddingService.embed(texts: list[str], collection_id: str, trace_id: str) -> list[list[float]]`, and `cache_key(text: str, model: str) -> tuple[str,str]`. `CallContext` contains `collection_id`, `user_id`, and `trace_id`; content-bearing hosted stages require a non-confidential collection with current terms acknowledgment.

- [ ] **Step 1: Write failing retry, circuit, and cache tests**

Use `httpx.MockTransport` and fake sleep/jitter. Cover bounded retries on 429/500, no retry on 400, Retry-After cap, per-model circuit opening, configured fallback only, dimension mismatch rejection, exact batch ordering, and two identical `embed` calls resulting in one transport request. Assert a model change creates a different key and never reuses the old vector. Assert default-confidential, stale-terms, and missing-collection contexts make zero transport calls across every content-bearing stage, including fallback.

- [ ] **Step 2: Run tests and implement deterministic cache identity**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_gateway_retry.py apps/api/tests/test_embedding_cache.py -v`  
Expected: FAIL on missing gateway/cache services.

```python
# apps/api/nim_gateway/embeddings.py
import hashlib


def cache_key(text: str, model: str) -> tuple[str, str]:
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), model
```

Implement `HostedTransferGuard.authorize(context,stage)` inside `NIMGateway.call` before any provider request. Only P0's content-free smoke client may omit a collection; all application/worker/eval calls supply one. Implement `set_collection_privacy.py --collection ID --actor USER_ID --accept-terms VERSION --allow-hosted-transfer` to require the exact P0 terms version, set confidentiality false, and append a `privacy_audit` row transactionally. Revoking sets confidential true immediately without claiming provider data deletion.

Implement token-bucket acquisition separately per model, exponential backoff with jitter on 429/5xx, maximum elapsed/call budgets, and a circuit breaker with closed/open/half-open states. Redact request contents and secrets from errors. Fallback applies only where `DECISION.md` specifies one; verify fallback uses a smaller configured claim batch in P4.

- [ ] **Step 3: Implement batch embedding and independent cache vectors**

Read model/request flags and maximum batch size from verified config. Read `vector_dim` from the first successful response and fail subsequent mismatches. Store immutable cache points in a model/dimension/request-semantics-namespaced cache collection or table; per-document retrieval points copy those vectors and have independent lifetimes. Cache rows use `(text_sha256,model)` and must also match `request_semantics_hash`. A semantics mismatch is a miss; after a successful new embedding, replace the row's vector reference and semantics hash atomically so incompatible vectors cannot be reused.

- [ ] **Step 4: Verify quota-free repeat behavior and commit**

Run the focused tests with mocked transport; expected PASS and zero external calls. Run one explicitly acknowledged live batch on three non-confidential sample chunks, delete their document, re-ingest in another collection, and assert the second embedding request count is zero despite original retrieval-point deletion.

Commit: `git add apps/api packages/common proof/P2/gateway_cache.md && git commit -m "feat(P2-T04): add resilient cached embedding gateway"`

**Acceptance:** Cache survives document deletion, model changes cannot collide, vector dimension is measured, transient failures are bounded, and unchanged re-ingestion makes zero embedding calls.

### P2-T05: Implement transactional lexical and vector indexing

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T07, P2-T04  
**Requirements:** PRD FR-IDX-1, FR-IDX-2, FR-IDX-3, §8 | **Decisions:** D-005, D-007, D-015, D-031, D-032  
**Proof:** `proof/P2/index_contract.md`

**Files:**
- Create: `packages/common/citerag_common/vector_store.py`
- Create: `apps/worker/tasks/index.py`, `alembic/versions/0002_chunk_search.py`
- Test: `apps/worker/tests/test_indexing.py`

**Interfaces:** Produce `VectorStore.upsert(points)`, `delete_document(document_id)`, `search(vector, filters, limit)`, and `index_chunks(document_id: str)`.

- [ ] **Step 1: Write failing payload and idempotency tests**

Assert every vector payload contains exactly required keys `chunk_id`, `doc_id`, `collection_id`, `page_start`, `page_end`, `section_path`, `chunk_type`, `lang`, plus no source secrets. Reindexing the same document updates identical point IDs without duplicates. Deleting one document leaves sibling documents and embedding cache points intact.

- [ ] **Step 2: Add PostgreSQL simple-tsvector maintenance**

```sql
-- alembic/versions/0002_chunk_search.py core SQL
CREATE OR REPLACE FUNCTION chunks_tsv_update() RETURNS trigger AS $$
BEGIN
  NEW.tsv := to_tsvector('simple', coalesce(NEW.text, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER chunks_tsv BEFORE INSERT OR UPDATE OF text ON chunks
FOR EACH ROW EXECUTE FUNCTION chunks_tsv_update();
CREATE INDEX chunks_tsv_idx ON chunks USING GIN (tsv);
CREATE INDEX chunks_document_idx ON chunks(document_id, id);
```

Test that Hindi/Marathi text produces nonempty lexemes and lexical search respects document/collection predicates.

- [ ] **Step 3: Implement the selected vector adapter**

Generate deterministic point IDs from chunk UUIDs. Create collections/tables only from measured dimension, set payload indexes for collection/document filters, and implement atomic batch upsert/retry. For pgvector, preserve the same `VectorStore` interface and filter SQL. Do not keep a second Qdrant adapter active after a pgvector decision unless the proof documents migration need.

- [ ] **Step 4: Verify cross-store crash recovery and commit**

Run integration tests with a fault after PostgreSQL chunk commit and before vector upsert, then retry `index_chunks`. Expected document becomes indexed with exactly one point per chunk and no duplicate chunk rows. Save payload samples, indexes, and recovery logs.

Commit: `git add alembic packages/common apps/worker proof/P2/index_contract.md && git commit -m "feat(P2-T05): add hybrid searchable chunk indexes"`

**Acceptance:** Lexical `simple` search works for all test languages, vector filters/payload match PRD, and any crash window is safely retryable.

### P2-T06: Produce three-document indexing proof and quota report

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P2-T05  
**Requirements:** PRD P2 proof/gate | **Decisions:** D-001, D-012, D-014, D-015  
**Proof:** `proof/P2/chunks/*.json`, `proof/P2/token_histogram.csv`, `proof/P2/table_chunks.md`, `proof/P2/quota_usage.md`

**Files:**
- Create: `scripts/dump_chunks.py`, `scripts/chunk_report.py`
- Test: `packages/chunking/tests/test_chunk_report.py`

- [ ] **Step 1: Write failing report-invariant tests**

Validate that the report rejects a chunk missing block IDs, exceeding token limit, lacking pages/bboxes, or containing section prefix in displayed text. Histogram buckets must include every chunk exactly once.

Run the report test; expected FAIL on missing validator.

- [ ] **Step 2: Implement deterministic dump and histogram generation**

Dump chunk ID/type/text/embed_text/token count/section path/pages/continuations/block IDs/bboxes in stable ID order. Compute min/max/median/p95 and fixed histogram buckets from actual token counts. List ten table chunks with source document/page, sanitized HTML, flattened text, row range, and split index.

- [ ] **Step 3: Process three documents and re-ingest unchanged content**

Choose one digital report, one scanned/table-heavy document, and one Hindi or Marathi document. For owner-approved hosted transfer, run `python scripts/set_collection_privacy.py --collection "$COLLECTION_ID" --actor "$USER_ID" --accept-terms "$CITERAG_TERMS_VERSION" --allow-hosted-transfer`; otherwise use only locally processable fixtures and do not claim live embedding proof. Record NIM call count/credits before and after first ingestion and exact re-ingestion. Expected second embedding call count zero; other hosted calls are reported separately.

- [ ] **Step 4: Validate all artifacts and commit**

Run: `python scripts/chunk_report.py proof/P2/chunks --validate --histogram proof/P2/token_histogram.csv`  
Expected: exit 0, no oversize/orphan chunks. Commit: `git add scripts packages/chunking/tests proof/P2 && git commit -m "test(P2-T06): prove chunk provenance and embedding reuse"`

**Acceptance:** Three dumps, histogram, ten table HTML examples, and quota report exist; every invariant passes on actual worker output.

### P2-T07: Close the chunking and indexing gate

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P2-T01 through P2-T06  
**Requirements:** PRD P2 gate | **Decisions:** D-001, D-012, D-014  
**Proof:** `proof/P2/gate.json`, `proof/P2/gate_review.md`

**Files:**
- Create: `proof/P2/manifest.json`, `proof/P2/gate_review.md`, `proof/P2/gate.json`
- Modify: `TASKS.md`

- [ ] **Step 1: Run full offline regression suite**

Run: `python -m pytest packages/chunking/tests packages/common/tests apps/api/tests apps/worker/tests -v`  
Expected: all PASS and no live hosted requests. Confirm every chunk in three dumps satisfies size/provenance invariants.

- [ ] **Step 2: Verify zero-call re-ingestion from traces**

Compare embedding gateway call counts and cached model/text hashes for the identical second ingestion. Any network embed call fails the gate even if the returned answer looks correct.

- [ ] **Step 3: Execute gate and commit**

Run: `python scripts/check_gate.py proof/P2/manifest.json --output proof/P2/gate.json`  
Expected: exit 0. Commit: `git add proof/P2 TASKS.md && git commit -m "test(P2-T07): close chunking indexing gate"`

**Acceptance:** P2 proof is complete and independently checked; P3 retrieval work is unblocked.

---

# P3 — Retrieval

**Entry:** P2 gate passed; hybrid indexes contain evaluated sample documents.  
**Exit gate:** Draft gold set and retrieval metrics exist; Recall@8 is at least 0.85 or a written diagnosis/fix plan is accepted; hybrid/rerank ablations are reported.

### P3-T01: Create and validate the draft retrieval gold set

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P2-T07  
**Requirements:** PRD §13, P3 proof/gate | **Decisions:** D-034  
**Proof:** `proof/P3/gold_draft.md`, `packages/eval/gold/draft.jsonl`

**Files:**
- Create: `packages/eval/eval/schema.py`, `packages/eval/gold/draft.jsonl`, `packages/eval/tests/test_gold_schema.py`
- Create: `packages/eval/eval/validate_gold.py`

**Interfaces:** Produce `GoldItem(question_id,question,answer,collection_id,document_ids,gold_chunk_ids,gold_pages,category,language)`.

- [ ] **Step 1: Write failing gold validation tests**

Reject duplicate question IDs, unknown category/language, empty expected answer for answerable items, nonempty gold sources for unanswerable items, missing document/page provenance, and a gold chunk outside the selected collection. Accept `unanswerable` items with empty gold chunks and a rationale instead of an expected factual answer.

- [ ] **Step 2: Implement strict Pydantic schema and validator**

Use categories `factoid`, `table`, `multi_passage`, `cross_document`, `unanswerable`; languages `en`, `hi`, `mr`. Gold chunk IDs may remain empty until traces are frozen, but document IDs and one-based gold pages/block IDs are mandatory for answerable items. Validator resolves those blocks to current chunk IDs and reports stale mappings after chunking changes.

- [ ] **Step 3: Author 40 draft questions from owner documents**

Use 14 factoid, 10 table, 6 multi-passage, 4 cross-document, and 6 unanswerable items. Include at least 6 Hindi/Marathi questions and several conversational follow-ups for rewrite evaluation. Record expected answer, source document/page/block, and rationale without looking at retrieval scores.

- [ ] **Step 4: Validate, freeze baseline, and commit**

Run: `python -m packages.eval.eval.validate_gold packages/eval/gold/draft.jsonl --database "$DATABASE_URL"`  
Expected: 40 valid items, exact category counts, no stale source mapping. Commit: `git add packages/eval proof/P3/gold_draft.md && git commit -m "test(P3-T01): add draft retrieval gold set"`

**Acceptance:** Gold labels are independently readable and source-linked; category/language counts match the draft design; later metrics use frozen IDs and config hashes.

### P3-T02: Add conditional standalone query rewriting

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T04, P3-T01  
**Requirements:** PRD FR-RET-1, §6 Rewrite | **Decisions:** D-003, D-017  
**Proof:** `proof/P3/rewrite_review.md`

**Files:**
- Create: `apps/api/app/retrieval/rewrite.py`, `config/prompts/rewrite.txt`
- Test: `apps/api/tests/test_rewrite.py`

**Interfaces:** Produce `needs_rewrite(question: str, history: list[Message]) -> bool` and `rewrite_query(question,history) -> RewriteResult(original,query,used_rewrite,model_id)`.

- [ ] **Step 1: Write failing conditional-call tests**

Assert a standalone question with no history never calls NIM; a standalone question with history also avoids rewriting; a follow-up such as "Why did it decline?" uses the last few turns; an invalid/empty rewrite falls back to original with `used_rewrite=false`; original question remains unchanged.

- [ ] **Step 2: Implement conservative triggers and exact prompt**

```python
# apps/api/app/retrieval/rewrite.py
import re

_FOLLOW_UP = re.compile(r"\b(it|that|this|they|those|what about|why|how about)\b", re.I)


def needs_rewrite(question: str, history: list) -> bool:
    return bool(history) and bool(_FOLLOW_UP.search(question.strip()))
```

```text
# config/prompts/rewrite.txt
Rewrite the latest question as one standalone search query using only the supplied recent conversation. Preserve names, numbers, language, and document scope. Do not answer the question and do not add facts. Return only the rewritten query. If the question is already standalone, return it unchanged.
```

Use verified low-temperature/short-output parameters and no more than the configured recent turns. Add an owner-reviewed underspecification rule only with test examples; pronoun detection must not rewrite every question containing "this" in a standalone title.

- [ ] **Step 3: Run recorded fixtures and review follow-ups**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_rewrite.py -v`  
Expected: PASS with zero live calls. Record draft follow-up originals/rewrites and manually reject added facts or language switches.

- [ ] **Step 4: Commit rewrite behavior**

Commit: `git add apps/api/app/retrieval config/prompts/rewrite.txt apps/api/tests proof/P3/rewrite_review.md && git commit -m "feat(P3-T02): add conditional query rewriting"`

**Acceptance:** Unnecessary calls are avoided, follow-ups become standalone, original text is retained, and failures degrade explicitly to original query.

### P3-T03: Implement filtered dense/lexical search and RRF

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P2-T05, P3-T02  
**Requirements:** PRD FR-RET-2, FR-RET-3, §8 trace_json | **Decisions:** D-016, D-030  
**Proof:** `proof/P3/hybrid_search.md`

**Files:**
- Create: `apps/api/app/retrieval/rrf.py`, `apps/api/app/retrieval/hybrid.py`, `apps/api/app/retrieval/types.py`
- Test: `apps/api/tests/test_rrf.py`, `apps/api/tests/test_hybrid_filters.py`

**Interfaces:** Produce `reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str,float]]` and `hybrid_search(query, scope, limit=40) -> HybridResult`.

- [ ] **Step 1: Write failing RRF and authorization-filter tests**

```python
# apps/api/tests/test_rrf.py
import pytest
from app.retrieval.rrf import reciprocal_rank_fusion


def test_rrf_uses_rank_and_constant_60():
    result = reciprocal_rank_fusion([["a", "b"], ["b", "c"]], k=60)
    assert result[0][0] == "b"
    assert result[0][1] == pytest.approx(2 / 61)
    assert dict(result)["a"] == pytest.approx(1 / 61)
    assert dict(result)["c"] == pytest.approx(1 / 62)
```

Integration tests insert same-named documents in two collections/users and prove both dense and lexical SQL/vector filters exclude out-of-scope points before ranks are assigned. `doc_ids` outside collection/ownership raise 403/404 without revealing existence.

- [ ] **Step 2: Run tests and implement deterministic RRF**

```python
# apps/api/app/retrieval/rrf.py
from collections import defaultdict


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60):
    scores = defaultdict(float)
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
```

Dense and lexical each return top 40 before fusion. Lexical ranking uses `ts_rank_cd(tsv, plainto_tsquery('simple', query))` plus explicit scope predicates; dense uses the same scope filter and measured query-input flag. Preserve component ranks/scores in `HybridResult` and traces.

- [ ] **Step 3: Verify fixture ranking and cross-tenant isolation**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_rrf.py apps/api/tests/test_hybrid_filters.py -v`  
Expected: PASS, ties resolve by chunk ID, empty lexical/dense branches still return the other branch, and out-of-scope gold items never appear.

- [ ] **Step 4: Commit hybrid retrieval**

Commit: `git add apps/api/app/retrieval apps/api/tests proof/P3/hybrid_search.md && git commit -m "feat(P3-T03): add filtered hybrid retrieval with RRF"`

**Acceptance:** Exact 40/40 and RRF 60 behavior is tested; component scores are traceable; filters apply before ranking and cannot be bypassed by optional `doc_ids`.

### P3-T04: Add measured reranking and complete retrieval traces

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T04, P3-T03  
**Requirements:** PRD FR-RET-4, §6 Rerank, §8 traces | **Decisions:** D-003, D-004, D-016  
**Proof:** `proof/P3/rerank_contract.md`

**Files:**
- Create: `apps/api/app/retrieval/rerank.py`, `apps/api/app/retrieval/pipeline.py`
- Test: `apps/api/tests/test_rerank.py`

**Interfaces:** Produce `rerank(query: str, candidates: list[RankedChunk]) -> list[RankedChunk]` with first 30 in and first 8 out.

- [ ] **Step 1: Write failing rerank fixture tests**

Use recorded P0 response shape. Assert input preserves fused order, output sorts by measured score direction, ties use fused rank then chunk ID, missing/duplicate indices fail, final count is 8, and scores are persisted without normalization. Test endpoint candidate limits smaller than 30 using the P0-documented batching strategy.

- [ ] **Step 2: Implement configured request and trace assembly**

Use exact route/model/max-candidate values from `config/models.yaml`; no assumed route or score range. Populate `dense_rank`, `lexical_rank`, `rrf_score`, `rerank_score`, and `final_rank`. Record candidate text hashes, model ID, route, latency, retry/fallback count, and all scores in `trace_json`.

- [ ] **Step 3: Run recorded tests and one bounded live comparison**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_rerank.py -v`  
Expected: PASS with zero live calls. With explicit `CITERAG_LIVE_BUDGET_ACK=1`, rerank one fixed 30-candidate set twice; expected identical IDs/scores within documented endpoint determinism and one call per run if candidate limit permits.

- [ ] **Step 4: Commit reranking**

Commit: `git add apps/api/app/retrieval apps/api/tests proof/P3/rerank_contract.md && git commit -m "feat(P3-T04): add measured reranking and traces"`

**Acceptance:** Exactly top 30 merged candidates enter rerank and eight leave; traces support offline Recall@k/MRR without another model call.

### P3-T05: Assemble bounded context and implement an uncalibrated abstention gate

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P2-T03, P3-T04  
**Requirements:** PRD FR-RET-5, FR-RET-6 | **Decisions:** D-013, D-018, D-019  
**Proof:** `proof/P3/context_abstention.md`

**Files:**
- Create: `apps/api/app/retrieval/context.py`, `apps/api/app/retrieval/abstain.py`
- Modify: `config/retrieval.yaml`
- Test: `apps/api/tests/test_context.py`, `apps/api/tests/test_abstain.py`

**Interfaces:** Produce `assemble_context(ranked: list[RankedChunk], links: dict[str,str], budget: int) -> AssembledContext` and `abstention_decision(score: float | None, threshold: float | None) -> AbstentionDecision`.

- [ ] **Step 1: Write failing context and threshold tests**

Assert stable C1–C8 primary labels, only `continues_from` neighbors added, no arbitrary adjacent chunk inclusion, budget truncation traced, and no dropped primary while its linked neighbor remains. Primaries use C1–C8; additional linked neighbors receive C9 onward in primary-rank order and count toward the same budget.

```python
# apps/api/tests/test_abstain.py
import pytest
from app.retrieval.abstain import abstention_decision


def test_null_threshold_is_explicitly_uncalibrated_development_mode():
    result = abstention_decision(0.01, None)
    assert not result.abstain
    assert result.state == "uncalibrated"


def test_calibrated_threshold_and_missing_score():
    assert abstention_decision(0.2, 0.5).abstain
    assert not abstention_decision(0.5, 0.5).abstain
    with pytest.raises(ValueError, match="rerank score unavailable"):
        abstention_decision(None, 0.5)
```

- [ ] **Step 2: Run tests and implement deterministic assembly/gate**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_context.py apps/api/tests/test_abstain.py -v`  
Expected: FAIL on missing modules.

```python
# apps/api/app/retrieval/abstain.py
from dataclasses import dataclass


@dataclass(frozen=True)
class AbstentionDecision:
    abstain: bool
    state: str


def abstention_decision(score: float | None, threshold: float | None) -> AbstentionDecision:
    if threshold is None:
        return AbstentionDecision(False, "uncalibrated")
    if score is None:
        raise ValueError("rerank score unavailable for calibrated abstention")
    return AbstentionDecision(score < threshold, "calibrated")
```

Context assembly copies exact chunk text, never `embed_text`, and records included/excluded IDs, labels, neighbor links, token counts, and truncation reasons. It uses the measured answer-model budget and reserves explicit space for instructions and output.

- [ ] **Step 3: Verify fixtures and save traces**

Run focused tests; expected PASS for budget zero, exact budget, long neighbor, cycles in continuation links, multilingual text, and missing linked chunk. A cycle cannot loop assembly or duplicate a label.

- [ ] **Step 4: Commit context and gate mechanism**

Commit: `git add apps/api/app/retrieval config/retrieval.yaml apps/api/tests proof/P3/context_abstention.md && git commit -m "feat(P3-T05): add bounded context and abstention gate"`

**Acceptance:** No guessed threshold is enabled; fixture thresholds exercise both branches; every model-input chunk ID/label is reproducible from trace.

### P3-T06: Build offline retrieval metrics and ablation reports

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P3-T01, P3-T05  
**Requirements:** PRD §4 metrics, §13, P3 proof/gate | **Decisions:** D-034  
**Proof:** `proof/P3/retrieval_metrics.json`, `proof/P3/ablations.md`

**Files:**
- Create: `packages/eval/eval/retrieval_metrics.py`, `packages/eval/eval/retrieval_runner.py`
- Test: `packages/eval/tests/test_retrieval_metrics.py`

**Interfaces:** Produce `recall_at_k(ranked_ids,gold_ids,k) -> float`, `reciprocal_rank(ranked_ids,gold_ids) -> float`, and page-level equivalents from traces.

- [ ] **Step 1: Write failing known-ranking metric tests**

```python
# packages/eval/tests/test_retrieval_metrics.py
import pytest
from eval.retrieval_metrics import recall_at_k, reciprocal_rank


def test_chunk_metrics_have_known_values():
    assert recall_at_k(["a", "b", "c"], {"c"}, 3) == 1.0
    assert recall_at_k(["a", "b", "c"], {"c"}, 2) == 0.0
    assert reciprocal_rank(["a", "b", "c"], {"c"}) == pytest.approx(1 / 3)
    assert reciprocal_rank(["a", "b"], {"missing"}) == 0.0
```

Add page-level tests where any gold page in top k counts, multi-gold items use first relevant rank for MRR, and unanswerable questions are excluded from source Recall/MRR denominators but reported separately.

- [ ] **Step 2: Implement metrics and trace-only runner**

```python
# packages/eval/eval/retrieval_metrics.py
def recall_at_k(ranked_ids, gold_ids, k):
    return float(any(item in gold_ids for item in ranked_ids[:k]))


def reciprocal_rank(ranked_ids, gold_ids):
    return next((1.0 / rank for rank, item in enumerate(ranked_ids, 1) if item in gold_ids), 0.0)
```

Runner replays stored traces for full hybrid, no rerank, dense-only, and lexical-only variants using identical gold/config versions. `no hybrid` is reported as separate dense-only and lexical-only rows so the removed branch is unambiguous.

- [ ] **Step 3: Run draft evaluation and analyze errors**

Run: `python -m packages.eval.eval.retrieval_runner --gold packages/eval/gold/draft.jsonl --trace-dir proof/P3/traces --output proof/P3/retrieval_metrics.json`  
Expected: chunk/page Recall@1/4/8, MRR, latency, and per-language/category slices; no answer/verify calls. Generate ablation deltas and inspect every item below Recall@8.

- [ ] **Step 4: Commit harness and baseline**

Commit: `git add packages/eval proof/P3 && git commit -m "test(P3-T06): measure offline retrieval and ablations"`

**Acceptance:** Hand-computed metrics match fixtures; all draft answerable items have traces; ablations use identical candidates/gold; report includes unanswerable count and multilingual slices.

### P3-T07: Close the retrieval gate

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P3-T01 through P3-T06  
**Requirements:** PRD P3 gate | **Decisions:** D-001, D-016, D-018, D-034  
**Proof:** `proof/P3/gate.json`, `proof/P3/gate_review.md`

**Files:**
- Create: `proof/P3/manifest.json`, `proof/P3/gate_review.md`, `proof/P3/gate.json`
- Modify: `TASKS.md`

- [ ] **Step 1: Verify draft Recall@8 and supporting evidence**

Run retrieval tests and metric command again. If Recall@8 ≥0.85, record pass. If below, keep the numeric miss visible and write diagnosis by failure type—parse/chunk, lexical/dense recall, rewrite, rerank, or gold mapping—with a concrete owner/task fix plan. PRD permits this alternate gate outcome; it does not permit deleting hard questions.

- [ ] **Step 2: Review hybrid/rerank ablation and traces**

Confirm top40/top40/RRF60/top30/top8 counts, authorized filters, exact model/config hashes, and trace-only reproduction. Confirm abstention remains marked uncalibrated.

- [ ] **Step 3: Execute gate and commit**

Run: `python scripts/check_gate.py proof/P3/manifest.json --output proof/P3/gate.json`  
Expected: exit 0 only when numeric gate or accepted diagnosis/fix-plan branch is present. Commit: `git add proof/P3 TASKS.md && git commit -m "test(P3-T07): close retrieval gate"`

**Acceptance:** Retrieval baseline and all caveats are reproducible; accepted fix plan has concrete tasks and does not silently change the 0.85 threshold.

---

# P4 — Generation and Verification

**Entry:** P3 gate passed; labeled context and traces are stable.  
**Exit gate:** Thirty recorded answers include verifier output and removal reasons, five refusals exist, citation metrics are measured, and no answer failing quote checks is displayed.

### P4-T01: Implement strict answer schema, grounded prompt, and one JSON repair

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P3-T07  
**Requirements:** PRD FR-GEN-1, FR-GEN-2, FR-GEN-3, §10 | **Decisions:** D-003, D-020, D-022  
**Proof:** `proof/P4/answer_schema.md`

**Files:**
- Create: `apps/api/app/verifier/schemas.py`, `apps/api/app/verifier/generate.py`, `config/prompts/answer.txt`, `config/prompts/answer_repair.txt`
- Test: `apps/api/tests/test_answer_schema.py`, `apps/api/tests/test_json_repair.py`

**Interfaces:** Produce `Answer`, `Sentence`, `generate_answer(question,context) -> GenerationResult`, and at most one `repair_json(invalid,errors)`.

- [ ] **Step 1: Write failing schema and repair-limit tests**

Test valid claim/connective paragraphs; reject claim without chunk/quote, connective with citation, quote over 25 whitespace-delimited words, citation outside supplied labels, invalid abstain combination, and malformed JSON. Mock transport expects exactly one repair call, then a typed failure on second invalid output.

- [ ] **Step 2: Implement Pydantic contracts and prompt**

```python
# apps/api/app/verifier/schemas.py
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class Sentence(BaseModel):
    text: str
    type: Literal["claim", "connective"]
    chunk_ids: list[str] = Field(default_factory=list)
    quote: str | None = None

    @model_validator(mode="after")
    def check_citation(self):
        if self.type == "claim":
            if not self.chunk_ids or not self.quote:
                raise ValueError("claim requires chunk_ids and quote")
            if len(self.quote.split()) > 25:
                raise ValueError("quote exceeds 25 words")
        elif self.chunk_ids or self.quote is not None:
            raise ValueError("connective cannot have citations")
        return self


class Answer(BaseModel):
    abstain: bool
    abstain_reason: str | None
    summary: str
    paragraphs: list[list[Sentence]] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_abstention(self):
        if self.abstain and (not self.abstain_reason or self.summary or self.paragraphs):
            raise ValueError("abstention requires a reason and empty answer content")
        if not self.abstain and self.abstain_reason is not None:
            raise ValueError("non-abstaining answer cannot have abstain_reason")
        return self
```

```text
# config/prompts/answer.txt
Answer only from the labeled context. Return JSON matching the supplied schema. Write a short draft summary followed by a structured detailed explanation. Every factual sentence must be type claim, list supporting chunk IDs with the primary quote-bearing chunk first, and include one verbatim quote of at most 25 words from the first chunk. Use multiple chunk IDs only when their combined evidence supports the claim. Nonfactual transitions are type connective with empty chunk_ids and null quote. If context is insufficient, set abstain true, give abstain_reason, use an empty summary and paragraphs. Do not use outside knowledge.
```

Use answer-model reasoning off and temperature at/near 0 exactly as verified in P0. JSON repair receives validation errors and invalid text, must return schema-only JSON, and cannot add new context IDs.

- [ ] **Step 3: Verify fixtures and commit**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_answer_schema.py apps/api/tests/test_json_repair.py -v`  
Expected: PASS, zero live calls, exact call-count assertions. Commit: `git add apps/api config/prompts proof/P4/answer_schema.md && git commit -m "feat(P4-T01): add strict grounded answer generation"`

**Acceptance:** Schema matches PRD; quote/citation constraints run before verification; invalid JSON receives one repair only; raw attempts are persisted for audit.

### P4-T02: Implement structural checks and exact-span quote verification

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P4-T01  
**Requirements:** PRD FR-VER-1, FR-VER-2, G1 | **Decisions:** D-020, D-021, D-022  
**Proof:** `proof/P4/quote_matching.md`

**Files:**
- Create: `apps/api/app/verifier/quotes.py`, `apps/api/app/verifier/structure.py`
- Test: `apps/api/tests/test_quotes.py`, `apps/api/tests/test_structure.py`

**Interfaces:** Produce `locate_quote(model_quote: str, chunk_text: str, threshold: float = 92) -> QuoteMatch | None` with exact source span and normalized score.

- [ ] **Step 1: Write failing normalization and verbatim-output tests**

```python
# apps/api/tests/test_quotes.py
from app.verifier.quotes import locate_quote


def test_returns_exact_source_span_not_model_near_quote():
    source = "Revenue rose  12% in FY2025."
    match = locate_quote("revenue rose 12%", source, threshold=92)
    assert match is not None
    assert match.source_quote == "Revenue rose  12%"
    assert source[match.start:match.end] == match.source_quote


def test_low_score_and_long_span_fail_closed():
    assert locate_quote("unrelated words", "Revenue rose 12%", threshold=92) is None
    assert locate_quote(" ".join(str(i) for i in range(26)), " ".join(str(i) for i in range(26))) is None
```

Add Devanagari NFKC, whitespace/case normalization, repeated quote, punctuation variation, and exact threshold 92 tests. Structural tests reject C IDs absent from the exact assembled context even if they exist in PostgreSQL.

- [ ] **Step 2: Implement normalization with source-index mapping**

Normalize each original character with NFKC plus casefold, collapse whitespace, and retain a normalized-index-to-original-index map. Use RapidFuzz `partial_ratio_alignment` on normalized strings. For score ≥92, map alignment destination bounds to original text, trim only surrounding whitespace, require ≤25 words, and return the untouched substring plus score/indices. Below threshold or unmappable/overlong spans return `None`.

```python
# apps/api/app/verifier/quotes.py
from dataclasses import dataclass


@dataclass(frozen=True)
class QuoteMatch:
    score: float
    source_quote: str
    start: int
    end: int
```

The implementation must include the full index map; applying fuzzy matching directly and then returning the model quote is explicitly invalid.

- [ ] **Step 3: Verify and persist both quote forms**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_quotes.py apps/api/tests/test_structure.py -v`  
Expected: PASS. Verifier JSON retains original quote, normalized score, exact matched span/start/end, chunk ID, and failure reason. Failed quote marks claim unsupported before entailment.

- [ ] **Step 4: Commit quote verification**

Commit: `git add apps/api/app/verifier apps/api/tests pyproject.toml proof/P4/quote_matching.md && git commit -m "feat(P4-T02): verify exact source quote spans"`

**Acceptance:** UI-bound quote always satisfies `source[start:end] == quote`; near-quotes cannot be relabeled verbatim; ambiguous block selection passes to P4-T05 rather than inventing a block.

### P4-T03: Add batched entailment verification with strict result coverage

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P0-T04, P4-T02  
**Requirements:** PRD FR-VER-3, FR-VER-6, §6 Verify/fallback | **Decisions:** D-003, D-004, D-023  
**Proof:** `proof/P4/entailment_contract.md`

**Files:**
- Create: `apps/api/app/verifier/entailment.py`, `config/prompts/verify.txt`
- Test: `apps/api/tests/test_entailment.py`

**Interfaces:** Produce `verify_claims(claims: list[ClaimEvidence]) -> VerifierBatch` returning one supported/partial/unsupported verdict per claim.

- [ ] **Step 1: Write failing verdict and fallback tests**

Use recorded Ultra and Lightning fixtures. Assert one batched primary call contains all eligible claims; verdict indices must exactly cover input with no duplicates; unknown verdict/reason type fails verification; quote-failed claims are marked unsupported locally and not sent as viable evidence. Force 429/circuit-open and assert Lightning fallback uses the smaller configured batch size and records both model IDs.

- [ ] **Step 2: Implement exact verifier prompt and response validation**

```text
# config/prompts/verify.txt
For each numbered claim, decide whether the supplied cited chunks support the factual content. Return JSON {"results":[{"claim_index":0,"verdict":"supported","reason":"one line"}]}. Use supported only when every material fact is entailed, partial when some material content is unsupported or overgeneralized, and unsupported when evidence is absent or contradicts the claim. Evaluate combined evidence when multiple chunks are cited. Do not use outside knowledge. Return exactly one result for every requested claim_index.
```

Use verified Ultra reasoning controls/token budget. Validate response against the PRD verifier schema and fail closed on missing/extra indices. Persist raw response, parsed results, model, latency, fallback, and evidence hashes.

- [ ] **Step 3: Run fixtures and commit**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_entailment.py -v`  
Expected: PASS, zero live calls. Commit: `git add apps/api config/prompts/verify.txt proof/P4/entailment_contract.md && git commit -m "feat(P4-T03): add batched claim entailment verification"`

**Acceptance:** One primary batched call per answer under normal conditions; fallback batching is measured/configured; incomplete verifier output cannot release an answer.

### P4-T04: Implement removal, partial badges, regeneration, refusal, and verified summary

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P4-T03  
**Requirements:** PRD FR-VER-4, §10 summary | **Decisions:** D-023, D-024  
**Proof:** `proof/P4/verification_policy.md`

**Files:**
- Create: `apps/api/app/verifier/policy.py`
- Test: `apps/api/tests/test_verification_policy.py`

**Interfaces:** Produce `apply_verification(answer: Answer, verdicts: list[ClaimResult]) -> VerificationPolicyResult` and `summary_claims(surviving_claims) -> list[Sentence]`; the response builder concatenates selected claim texts while retaining their citations.

- [ ] **Step 1: Write failing removal-ratio and summary tests**

Cover 1-of-4 removed (25%, no regeneration), 2-of-4 removed (50%, one regeneration), exactly 30% no regeneration, above 30% regeneration, all removed refusal, partial retained with badge, and second-attempt failure no further calls. Summary must concatenate at most first three surviving claims in original order with citations/partial badges and never use original draft summary text.

- [ ] **Step 2: Implement pure policy and deterministic summary**

```python
# apps/api/app/verifier/policy.py
def should_regenerate(removed: int, total: int, already_regenerated: bool) -> bool:
    if total == 0 or removed == total or already_regenerated:
        return False
    return removed / total > 0.30


def summary_claims(surviving):
    return [claim for claim in surviving if claim.type == "claim"][:3]
```

Remove unsupported claims and orphaned connectives. A connective flagged as factual by a deterministic/verifier review is reclassified and verified or dropped. Keep detailed surviving claims even when summary truncates to three. Persist removal indices/reasons and regeneration allowance.

- [ ] **Step 3: Implement one stricter regeneration path**

Stricter prompt repeats labeled context and removed reasons without exposing removed text as facts. It requires fewer claims and direct single-chunk quotes where possible. Rerun structural, quote, and entailment checks on the regenerated response. At most two generation calls total; each malformed generation response follows P4-T01's one-repair rule.

- [ ] **Step 4: Verify state machine and commit**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_verification_policy.py -v`  
Expected: PASS for every branch and exact call count. Commit: `git add apps/api config/prompts proof/P4/verification_policy.md && git commit -m "feat(P4-T04): enforce verified answer display policy"`

**Acceptance:** Unsupported text never survives; >30% removal regenerates once only; all-removed refuses; summary contains only surviving cited claims.

### P4-T05: Resolve verified claims to block-level citations

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T04, P4-T04  
**Requirements:** PRD FR-VER-5, FR-UI-3, FR-UI-4, FR-UI-6 | **Decisions:** D-021, D-022, D-025  
**Proof:** `proof/P4/citation_resolution.md`

**Files:**
- Create: `apps/api/app/verifier/citations.py`
- Test: `apps/api/tests/test_citations.py`

**Interfaces:** Produce `resolve_citations(claim: VerifiedClaim, chunk_blocks: dict[str,list[ParsedBlock]]) -> list[Citation]`.

- [ ] **Step 1: Write failing primary/supplementary and fallback tests**

Test primary quote unique block, span crossing blocks, tied/no match returns all primary-chunk blocks, supplementary chunks retain role and their own provenance, table chunk includes sanitized HTML, and deleted/missing block raises a citation error. Verify no citation points to a document outside the original scope.

- [ ] **Step 2: Implement deterministic citation resolution**

Use P4-T02's exact source span to locate the primary block. Select one only for a unique best match; otherwise return all blocks in that primary chunk. For supplementary chunks return their linked source blocks and exact stored excerpt for display; combined entailment remains in P4-T03. Return one-based page, PDF-point boxes, pixel boxes for images, chunk/document IDs, quote, role, and table HTML.

- [ ] **Step 3: Verify citation invariants on recorded fixtures**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_citations.py -v`  
Expected: PASS. For every resolved claim assert nonempty citations, primary role exactly once, quote exact in primary chunk, valid page/block IDs, and finite ordered coordinates.

- [ ] **Step 4: Commit citation resolution**

Commit: `git add apps/api/app/verifier apps/api/tests proof/P4/citation_resolution.md && git commit -m "feat(P4-T05): resolve verified claims to source blocks"`

**Acceptance:** Every surviving claim has document/page/block/bbox/verbatim quote; multi-citation chooser data and table side-panel data are complete.

### P4-T06: Orchestrate persisted chat and terminal-safe SSE

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P3-T05, P4-T05  
**Requirements:** PRD §9 `/chat`, messages, FR-UI-2, §8 traces | **Decisions:** D-018, D-023, D-026, D-033  
**Proof:** `proof/P4/chat_sse.md`, `proof/P4/chat_traces/`

**Files:**
- Create: `apps/api/app/services/chat.py`, `apps/api/app/routers/chat.py`, `apps/api/app/routers/conversations.py`, `apps/api/app/sse.py`
- Test: `apps/api/tests/test_chat_sse.py`, `apps/api/tests/test_chat_recovery.py`

**Interfaces:** Produce `POST /chat` SSE events `{id,event,data}` and `GET /conversations/{id}/messages`; terminal event is exactly one of `answer`, `refusal`, `error`.

- [ ] **Step 1: Write failing event-sequence and recovery tests**

Assert normal sequence rewriting/retrieving/reranking/answering/verifying then answer; omitted rewrite emits skipped metadata rather than fake work; below-fixture-threshold returns refusal before answer generation; invalid second JSON emits error; verifier outage emits error and no answer payload; client disconnect leaves one consistent persisted assistant outcome. Messages retain original/rewritten query, answer, verifier, and trace JSON.

- [ ] **Step 2: Implement SSE formatting and heartbeat**

```python
# apps/api/app/sse.py
import json


def sse_event(event_id: int, event: str, data: dict) -> bytes:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"id: {event_id}\nevent: {event}\ndata: {payload}\n\n".encode("utf-8")
```

Use monotonic per-request IDs and trace ID in every event. Heartbeats are SSE comments and cannot be mistaken for terminal events. Do not include answer tokens, removed claims, prompts, stack traces, or secrets in browser events.

- [ ] **Step 3: Implement query orchestration and persistence**

Run rewrite → query embed → hybrid/rerank → calibrated abstention check → context → answer/repair → verify/policy/regenerate → citation resolution → final persistence. Save user message and trace at start; atomically save terminal assistant result. Typical path uses the PRD's five hosted stages, with conditional rewrite skipped and query embed counted explicitly in traces.

- [ ] **Step 4: Verify full recorded pipeline and commit**

Run: `PYTHONPATH=apps/api python -m pytest apps/api/tests/test_chat_sse.py apps/api/tests/test_chat_recovery.py -v`  
Expected: PASS with recorded model fixtures, including reconnect and repeated terminal prevention. Commit: `git add apps/api proof/P4 && git commit -m "feat(P4-T06): add verified persisted chat SSE"`

**Acceptance:** Browser cannot observe unverified answer text; all terminal/failure paths persist audit data; API contracts and trace fields match PRD.

### P4-T07: Record thirty answers and close the verification gate

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P4-T06  
**Requirements:** PRD P4 proof/gate | **Decisions:** D-001, D-021, D-023, D-025, D-034  
**Proof:** `proof/P4/answers/*.json`, `proof/P4/removed_claims.md`, `proof/P4/refusals.md`, `proof/P4/metrics.json`, `proof/P4/gate.json`

**Files:**
- Create: `packages/eval/eval/citation_metrics.py`, `packages/eval/tests/test_citation_metrics.py`
- Create: `scripts/record_answers.py`

- [ ] **Step 1: Write failing citation-metric tests**

Define citation precision as human/gold-judged supporting displayed citations divided by all displayed citations, citation recall as displayed factual claims carrying at least one valid citation divided by all displayed factual claims, and unsupported claim rate as unsupported displayed factual claims divided by all displayed factual claims. Fixtures must distinguish partial badges from unsupported removals and produce zero denominators as `null`, never 1.0.

- [ ] **Step 2: Implement metrics and record thirty diverse answers**

Run 30 draft questions across factoid/table/multi/cross-document and Hindi/Marathi. Store original context, raw generation, quote checks, entailment, removals, regeneration, final displayed claims, resolved citations, and traces. Include at least five insufficient-source questions yielding refusals. Live calls require a precomputed exact budget acknowledgment; recorded fixtures may be reused only for unit regression, not claimed as live P4 answers.

- [ ] **Step 3: Audit every removed and displayed claim**

List every removed claim with quote/verdict reason. Human spot-check displayed citations against source pages and record citation precision/recall/unsupported rate with denominators. Assert programmatically that no final answer contains a quote-failed or structurally invalid claim.

- [ ] **Step 4: Execute gate and commit**

Run: `python -m pytest packages/eval/tests apps/api/tests -v && python scripts/check_gate.py proof/P4/manifest.json --output proof/P4/gate.json`  
Expected: tests PASS and gate exit 0 when 30 answers, five refusals, removal log, and measured metrics exist. Commit: `git add packages/eval scripts proof/P4 TASKS.md && git commit -m "test(P4-T07): close generation verification gate"`

**Acceptance:** P4 measures metrics without silently imposing P5 targets; no failed-quote answer is present in any final UI-bound payload.

# P5 — Evaluation and Tuning

**Entry:** P4 gate passed; answer/verifier traces are complete.  
**Exit gate:** Final 80-question gold set, full metrics, calibrated thresholds, ablations, language slices, worst-15 analysis, and target decisions are committed in `proof/P5/baseline.md`.

### P5-T01: Finalize and adjudicate the 80-question gold set

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P4-T07  
**Requirements:** PRD §13 Gold set, §4 | **Decisions:** D-034  
**Proof:** `proof/P5/gold_review.md`, `packages/eval/gold/final.jsonl`

**Files:**
- Create: `packages/eval/gold/final.jsonl`, `packages/eval/eval/adjudication.py`
- Test: `packages/eval/tests/test_final_gold.py`

**Interfaces:** Reuse P3 `GoldItem`; produce a frozen final manifest with source/config hashes and human adjudication history.

- [ ] **Step 1: Write failing distribution and label-change tests**

Require exactly 80 items: 28 factoid, 20 table, 12 multi-passage, 8 cross-document, and 12 unanswerable. Require at least 10 Hindi/Marathi items; select 12 with six Hindi and six Marathi. Reject duplicate questions, source-free answerable items, and a changed gold answer/source without reviewer rationale and prior value.

- [ ] **Step 2: Implement append-only adjudication records**

```python
# packages/eval/eval/adjudication.py
from datetime import datetime
from pydantic import BaseModel


class Adjudication(BaseModel):
    question_id: str
    field: str
    old_value: str | None
    new_value: str
    reason: str
    reviewer: str
    reviewed_at: datetime
```

Validator compares each changed final item with its draft value when present and requires an adjudication row. Model output may identify a labeling concern but cannot directly change gold data.

- [ ] **Step 3: Expand and independently review labels**

Retain valid draft IDs and add owner-written questions until exact counts are reached. Review expected answer, document/page/block, language, and unanswerable rationale against source documents. Ensure no confidential document is sent to hosted models without explicit override.

- [ ] **Step 4: Validate, freeze, and commit**

Run: `python -m packages.eval.eval.validate_gold packages/eval/gold/final.jsonl --final --database "$DATABASE_URL"`  
Expected: 80 valid items, 28/20/12/8/12 distribution, 12 language-subset items, valid adjudication history. Commit: `git add packages/eval proof/P5/gold_review.md && git commit -m "test(P5-T01): finalize adjudicated evaluation gold set"`

**Acceptance:** Gold set meets PRD size/proportions/language requirements; source labels resolve to current blocks/chunks; changes are justified and auditable.

### P5-T02: Run full metrics with judged correctness and human audit

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P5-T01  
**Requirements:** PRD §4, §13 Metrics/Method, §8 eval_runs | **Decisions:** D-004, D-033, D-034  
**Proof:** `proof/P5/full_metrics.json`, `proof/P5/judge_audit.md`, `proof/P5/traces/`

**Files:**
- Create: `packages/eval/eval/answer_metrics.py`, `packages/eval/eval/judge.py`, `packages/eval/eval/run.py`, `config/prompts/eval_judge.txt`
- Test: `packages/eval/tests/test_answer_metrics.py`, `packages/eval/tests/test_eval_run.py`

**Interfaces:** Produce `run_evaluation(gold_path, config_hash, git_sha) -> EvalRun` persisting all PRD metrics and per-stage latency.

- [ ] **Step 1: Write failing aggregate and denominator tests**

Fixtures cover Recall@8, MRR, citation precision/recall, unsupported claim rate, refusal accuracy, answer correctness, and p50/p95 query latency. Unanswerable items count in refusal accuracy but not source Recall/MRR. Human disagreement always creates an audit row. Zero denominators serialize as `null` with item count zero.

- [ ] **Step 2: Implement strict judge prompt and score parsing**

```text
# config/prompts/eval_judge.txt
Compare the system answer with the gold answer using only the supplied gold evidence. Score factual correctness from 0.0 to 1.0: 1.0 means every material gold fact is answered with no contradiction, 0.5 means material omissions or partial accuracy, and 0.0 means wrong or unsupported. Do not reward extra unsupported detail. Return JSON {"score":0.0,"reason":"one paragraph","material_errors":["error"]}.
```

Validate score bounds and required fields. Judge final displayed answers, not raw model drafts. Record Ultra judge model ID, prompt/config hashes, and raw responses.

- [ ] **Step 3: Execute the final live evaluation with an exact budget**

Before running, calculate answer/verify/judge call counts from enabled stages, possible language subsets, and repair/fallback reserves. Set `CITERAG_LIVE_BUDGET_ACK` to that exact upper bound; stop on credit safety thresholds. Persist each query trace as it completes so interruption is resumable without repeating successful calls.

Run: `python -m packages.eval.eval.run --gold packages/eval/gold/final.jsonl --output proof/P5/full_metrics.json`  
Expected: one `eval_runs` row with config hash/git SHA, all 80 per-item results, stage latencies, and aggregate/slice metrics.

- [ ] **Step 4: Audit 20% and every disagreement**

Select 16 items with a deterministic stratified sample across category/language. A human compares answer, gold, sources, and judge score. Audit every judge/human disagreement in addition to the sample. Record score changes and judge failure modes; do not alter system answers after scoring.

- [ ] **Step 5: Commit full evaluation evidence**

Commit: `git add packages/eval config/prompts/eval_judge.txt proof/P5 && git commit -m "test(P5-T02): run full judged evaluation and audit"`

**Acceptance:** Every PRD metric has definition, denominator, value, and item-level evidence; eval row is reproducible; 16 audit items plus all disagreements are reviewed.

### P5-T03: Calibrate abstention and quote thresholds from measured outcomes

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P5-T02  
**Requirements:** PRD FR-RET-5, FR-VER-2, P5 | **Decisions:** D-018, D-021, D-034  
**Proof:** `proof/P5/threshold_calibration.json`, `proof/P5/threshold_review.md`

**Files:**
- Create: `packages/eval/eval/calibrate.py`
- Modify: `config/retrieval.yaml`, `DECISION.md`
- Test: `packages/eval/tests/test_calibrate.py`

**Interfaces:** Produce `select_abstention_threshold(candidates) -> CalibrationResult` and `select_quote_threshold(candidates) -> CalibrationResult` with all candidate metrics retained.

- [ ] **Step 1: Write failing deterministic selection tests**

For abstention, choose the threshold with highest answerable coverage among candidates meeting refusal accuracy ≥0.90; tie-break by higher refusal accuracy then higher threshold, and reject if no candidate meets the target. For quote matching, choose highest citation recall among candidates meeting citation precision ≥0.95 and unsupported claim rate ≤3%; report if no candidate qualifies.

- [ ] **Step 2: Implement exhaustive measured-candidate sweep**

```python
# packages/eval/eval/calibrate.py
def eligible(rows, metric: str, minimum: float):
    return [row for row in rows if row[metric] is not None and row[metric] >= minimum]


def select_abstention_threshold(rows):
    candidates = eligible(rows, "refusal_accuracy", 0.90)
    if not candidates:
        raise ValueError("no abstention threshold meets refusal accuracy target")
    return max(candidates, key=lambda row: (row["answerable_coverage"], row["refusal_accuracy"], row["threshold"]))
```

Sweep every distinct observed rerank score midpoint, not an arbitrary small grid. Quote candidates include default 92 and all distinct observed alignment scores. Replay stored claims/context for quote calibration; rerun generation only for the selected abstention threshold's final confirmation.

- [ ] **Step 3: Apply selected values and rerun the full suite**

Record score scale/direction, candidate counts, coverage/refusal trade-offs, quote precision/recall trade-offs, and per-language behavior. Update YAML and D-018 with evidence. Rerun all 80 questions and P0–P4 offline regressions; do not select a threshold on one slice that hides unacceptable multilingual behavior.

- [ ] **Step 4: Commit calibrated config and confirmation metrics**

Commit: `git add packages/eval config/retrieval.yaml DECISION.md proof/P5 && git commit -m "test(P5-T03): calibrate refusal and quote thresholds"`

**Acceptance:** Thresholds are numeric, evidence-selected, versioned, and confirmed by a full rerun; no target miss is hidden by an eligibility filter.

### P5-T04: Run baseline ablations and multilingual/worst-item analysis

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P5-T03  
**Requirements:** PRD §13 Ablations, P5 | **Decisions:** D-008, D-016, D-023, D-034  
**Proof:** `proof/P5/ablations.md`, `proof/P5/language_metrics.json`, `proof/P5/worst_15.md`

**Files:**
- Create: `packages/eval/eval/ablations.py`, `packages/eval/eval/error_analysis.py`
- Test: `packages/eval/tests/test_error_analysis.py`

**Interfaces:** Produce comparable ablation rows and deterministic worst-item ranking without exposing verifier-off answers to the UI.

- [ ] **Step 1: Write failing ablation-isolation and ranking tests**

Assert each ablation changes only its named component and has a distinct config hash. Verifier-off output is stored in eval-only artifacts and fails an API-display guard. Worst-item ordering uses answer correctness ascending, citation support ascending, then latency descending and question ID for ties.

- [ ] **Step 2: Implement controlled baseline ablations**

Run full pipeline, no rerank, dense-only, lexical-only, single-pass parse, and verifier-off configurations. Single-pass parsing requires a separate derived index so it cannot contaminate baseline chunks. Reuse identical gold questions and measure retrieval, citation, correctness, refusal, unsupported claims, latency, and hosted calls for every variant.

- [ ] **Step 3: Analyze language slices and worst 15 questions**

Report English, Hindi, and Marathi separately with sample counts. For each worst item record stage evidence, root cause category, erroneous output/source, concrete fix, and whether fix requires a new decision. Do not tune against only the worst 15 and claim full-set improvement without a rerun.

- [ ] **Step 4: Commit ablation and error analysis**

Run: `python -m packages.eval.eval.ablations --baseline proof/P5/full_metrics.json --output proof/P5/ablations.md` followed by full offline tests. Expected all required variants present and display guard tests PASS.

Commit: `git add packages/eval proof/P5 && git commit -m "test(P5-T04): analyze ablations languages and worst items"`

**Acceptance:** Every PRD ablation has a measured delta; verifier-off content is quarantined; Hindi/Marathi results and 15 detailed error analyses exist.

### P5-T05: Publish baseline, decide target misses, and close P5

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P5-T01 through P5-T04  
**Requirements:** PRD §4, P5 gate | **Decisions:** D-001, D-034, D-035  
**Proof:** `proof/P5/baseline.md`, `proof/P5/gate.json`

**Files:**
- Modify: `DECISION.md` for any accepted threshold/target decision
- Create: `packages/eval/eval/baseline_report.py`

- [ ] **Step 1: Generate a complete target comparison**

For each initial target, report measured value, pass/miss, confidence/sample denominator, English/Hindi/Marathi slice where applicable, and proof link: Recall@8 ≥0.90, MRR ≥0.75, citation precision ≥0.95, citation recall ≥0.98, unsupported claim rate ≤3%, refusal accuracy ≥0.90, answer correctness ≥0.85, p95 latency ≤30s.

- [ ] **Step 2: Record a decision for every miss**

A miss includes cause, evidence, fix decision, owner, and follow-up task. If recalibrating, retain old/new target, measured result, reason, reviewer approval, and date in `DECISION.md`; never edit the PRD's initial target table retroactively. A documented miss satisfies the PRD gate only with an explicit decision, not automatic release approval.

- [ ] **Step 3: Validate baseline completeness and commit gate**

Run: `python -m packages.eval.eval.baseline_report --metrics proof/P5/full_metrics.json --output proof/P5/baseline.md --check-targets` and `python scripts/check_gate.py proof/P5/manifest.json --output proof/P5/gate.json`  
Expected: all metrics/decisions/artifacts present; gate exit 0 only when each target passes or has an explicit owner decision.

Commit: `git add packages/eval DECISION.md proof/P5 TASKS.md && git commit -m "test(P5-T05): publish evaluated baseline and tuning decisions"`

**Acceptance:** Baseline contains every target and ablation; eval rows and worst-15 analysis are linked; no metric or target was silently changed.

---

# P6 — Web UI

**Entry:** P5 gate passed; verified chat APIs and calibrated refusal behavior are frozen for UI integration.  
**Exit gate:** Five use cases are recorded, citation navigation works, and 20/20 sampled highlights land on the correct block.

### P6-T01: Scaffold Next.js 15 with typed API and terminal-safe SSE client

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P5-T05  
**Requirements:** PRD §5 Web, FR-UI-2 | **Decisions:** D-002, D-026  
**Proof:** `proof/P6/web_foundation.md`

**Files:**
- Create: `apps/web/package.json`, `apps/web/src/lib/types.ts`, `apps/web/src/lib/api.ts`, `apps/web/src/lib/sse.ts`
- Create: `apps/web/src/app/page.tsx`, `apps/web/vitest.config.ts`
- Test: `apps/web/src/lib/sse.test.ts`, `apps/web/src/lib/api.test.ts`

**Interfaces:** Produce `streamChat(request: ChatRequest, handlers: ChatHandlers): Promise<void>` and typed `AnswerEvent`, `RefusalEvent`, `ErrorEvent` unions.

- [ ] **Step 1: Scaffold the exact Next major version and test runner**

Run: `npx create-next-app@15 apps/web --typescript --eslint --app --src-dir --use-npm --no-tailwind --import-alias "@/*" && npm --prefix apps/web install && npm --prefix apps/web install -D vitest @testing-library/react @testing-library/jest-dom jsdom @playwright/test`  
Expected: Next 15 lockfile, App Router, TypeScript, and Vitest configuration. Commit lockfile so later builds cannot drift to Next 16.

- [ ] **Step 2: Write failing SSE parsing tests**

Test CRLF/LF frames, multiline data, heartbeats, Unicode Hindi/Marathi, terminal answer/refusal/error, error after terminal ignored, missing terminal rejection, HTTP 401/403/500, and that stage events never contain answer text.

- [ ] **Step 3: Implement strict event parsing and API boundaries**

```ts
// apps/web/src/lib/types.ts
export type BBox = [number, number, number, number];
export type Stage = "rewriting" | "retrieving" | "reranking" | "answering" | "verifying";

export interface Citation {
  chunk_id: string;
  document_id: string;
  page: number;
  block_ids: string[];
  bboxes_pdf: BBox[];
  bboxes_px: BBox[];
  quote: string;
  role: "primary" | "supplementary";
  table_html: string | null;
  source_number: number;
}

export interface Claim {
  text: string;
  type: "claim" | "connective";
  citations: Citation[];
  partial: boolean;
  verifier_reason: string | null;
}

export interface VerifiedAnswer {
  summary: { text: string; citations: Citation[] };
  paragraphs: Claim[][];
  sources: Array<Citation & { filename: string }>;
}

export type TerminalEvent =
  | { event: "answer"; trace_id: string; answer: VerifiedAnswer }
  | { event: "refusal"; trace_id: string; reason: string }
  | { event: "error"; trace_id: string; message: string };

export interface ChatRequest {
  collection_id: string;
  conversation_id: string | null;
  question: string;
  doc_ids?: string[];
}

export interface ChatHandlers {
  onStage: (stage: Stage, traceId: string) => void;
  onTerminal: (event: TerminalEvent) => void;
}
```

`streamChat` uses `fetch('/api/chat')` through a same-origin Next route proxy, reads the body with `TextDecoder`, parses SSE `id/event/data`, validates JSON with explicit runtime guards, invokes terminal handler once, and rejects missing terminals on stream close. No NIM key or Python service credential exists in `NEXT_PUBLIC_*` variables.

- [ ] **Step 4: Verify web tests and production build**

Run: `npm --prefix apps/web test -- --run && npm --prefix apps/web run build`  
Expected: tests PASS and Next production build succeeds with no browser secret warnings. Commit: `git add apps/web proof/P6/web_foundation.md && git commit -m "feat(P6-T01): add typed web foundation and SSE client"`

**Acceptance:** Browser handles every terminal/failure shape, cannot render stage text as an answer, and shares generated/runtime-checked API types.

### P6-T02: Build collections, upload, ingestion progress, and deletion library

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T06, P6-T01  
**Requirements:** PRD FR-UI-1, FR-ING-7 | **Decisions:** D-006, D-011, D-028, D-029  
**Proof:** `proof/P6/library.md`

**Files:**
- Create: `apps/web/src/components/library/CollectionList.tsx`, `UploadDialog.tsx`, `DocumentRow.tsx`
- Create: `apps/web/src/app/collections/[id]/page.tsx`
- Test: `apps/web/src/components/library/library.test.tsx`

**Interfaces:** Consume collection/document APIs; produce accessible upload/delete/progress interactions with duplicate and confidential states.

- [ ] **Step 1: Write failing library interaction tests**

Cover collection create/list, PDF/PNG/JPG selection, cap/type error from server, upload progress, duplicate link, queued-to-indexed polling, failed-page counts, paused outage, confidential block, delete confirmation, repeated delete, and keyboard-accessible dialog controls. Progress comes only from API fields, not fabricated timers.

- [ ] **Step 2: Implement library components and polling**

Use semantic forms, labels, progress element, `aria-live="polite"` status, and a confirmation dialog naming the document. Poll `GET /documents/{id}` with bounded backoff only while active; stop on terminal, 404, unmount, or repeated failure. Disable unsupported file accept bypasses in UI while retaining server validation as authoritative.

- [ ] **Step 3: Add explicit confidentiality acknowledgment**

Display `confidential=true` badge and blocked hosted indexing/chat explanation. Override requires a separate unchecked acknowledgment stating hosted transfer risk; changing the flag calls the P7 endpoint added later, with development identity limited to loopback.

- [ ] **Step 4: Verify and commit**

Run: `npm --prefix apps/web test -- --run src/components/library/library.test.tsx`  
Expected: all interaction tests PASS, no unanswered act() warnings. Save screenshots for active, failed-page, duplicate, and confidential states.

Commit: `git add apps/web proof/P6/library.md && git commit -m "feat(P6-T02): add document collection library"`

**Acceptance:** User can complete all library actions and understand partial/failed/paused/confidential states without reading logs.

### P6-T03: Build verified chat, citations, sources, badges, refusals, and failures

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P4-T06, P6-T01  
**Requirements:** PRD FR-UI-2, FR-UI-3, FR-UI-4, FR-UI-5 | **Decisions:** D-022, D-023, D-024, D-026  
**Proof:** `proof/P6/chat_answer.md`

**Files:**
- Create: `apps/web/src/components/chat/ChatPanel.tsx`, `VerifiedAnswer.tsx`, `CitationChip.tsx`, `SourceChooser.tsx`
- Create: `apps/web/src/lib/answer.ts`
- Test: `apps/web/src/components/chat/VerifiedAnswer.test.tsx`, `ChatPanel.test.tsx`

**Interfaces:** Consume terminal `VerifiedAnswer`; produce `onCitationSelect(citation: Citation)` and accessible multi-citation chooser.

- [ ] **Step 1: Write failing rendering tests**

Assert stage order, no answer before terminal event, summary from surviving claims, detailed paragraphs, partial badge/reason, refusal, safe error, one citation direct-open, multiple citations chooser, numbered sources with document/page/exact quote, and keyboard selection. Removed/raw claims must not exist in browser fixtures or DOM.

- [ ] **Step 2: Implement claim/citation association and accessible chips**

```tsx
// apps/web/src/components/chat/CitationChip.tsx
export function CitationChip({ numbers, onSelect }: { numbers: number[]; onSelect: () => void }) {
  return (
    <button type="button" className="citation-chip" onClick={onSelect} aria-label={`Open sources ${numbers.join(", ")}`}>
      {numbers.map((number) => `[${number}]`).join("")}
    </button>
  );
}
```

Render text as React text nodes, never `dangerouslySetInnerHTML`. Keep citation roles and stable source numbers. Partial badges include verifier reason; connectives cannot receive chips.

- [ ] **Step 3: Implement chat terminal state machine**

State union is `idle | working | answer | refusal | failure`; only terminal SSE payload transitions to a content state. On retry create a new question/request rather than mutating removed claims. Persist and reload conversations through `GET /conversations/{id}/messages`.

- [ ] **Step 4: Verify and commit**

Run: `npm --prefix apps/web test -- --run src/components/chat`  
Expected: all tests PASS. Save answer/partial/refusal/failure/chooser screenshots.

Commit: `git add apps/web proof/P6/chat_answer.md && git commit -m "feat(P6-T03): render verified cited chat answers"`

**Acceptance:** Answer layout matches PRD; no unverified/raw content is rendered; every factual sentence exposes valid citation controls and partial/refusal/failure states are clear.

### P6-T04: Add PDF/image highlights and sanitized table side panel

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P1-T06, P6-T03  
**Requirements:** PRD FR-UI-4, FR-UI-6, UC2/UC4, P6 gate | **Decisions:** D-010, D-025, D-027, D-028  
**Proof:** `proof/P6/viewer_geometry.md`

**Files:**
- Create: `apps/web/src/components/viewer/PdfViewer.tsx`, `ImageViewer.tsx`, `TablePanel.tsx`, `HighlightLayer.tsx`
- Create: `apps/web/src/lib/geometry.ts`
- Test: `apps/web/src/lib/geometry.test.ts`, `apps/web/src/components/viewer/TablePanel.test.tsx`

**Interfaces:** Produce `pdfBoxToCss(box: BBoxPDF, viewport: PageViewport) -> CssBox`, `imageBoxToCss(box,renderSize,displaySize) -> CssBox`, and citation-driven document/page/block navigation.

- [ ] **Step 1: Write failing coordinate and sanitization tests**

Use pdf.js viewport fixtures at scale 0.75, 1, 1.5, 2 and rotation 0/90/180/270. Assert left/top/width/height after viewport conversion. Image tests compare native render dimensions with displayed CSS dimensions. Table tests strip scripts, handlers, links, images, and styles even if backend sanitizer regresses.

- [ ] **Step 2: Implement geometry from the actual viewport**

```ts
// apps/web/src/lib/geometry.ts
import type { PageViewport } from "pdfjs-dist";

export function pdfBoxToCss(box: [number, number, number, number], viewport: PageViewport) {
  const [x1, y1, x2, y2] = viewport.convertToViewportRectangle(box);
  return { left: Math.min(x1, x2), top: Math.min(y1, y2), width: Math.abs(x2 - x1), height: Math.abs(y2 - y1) };
}

export function imageBoxToCss(box: [number, number, number, number], render: {w:number;h:number}, display: {w:number;h:number}) {
  const sx = display.w / render.w;
  const sy = display.h / render.h;
  return { left: box[0] * sx, top: box[1] * sy, width: (box[2] - box[0]) * sx, height: (box[3] - box[1]) * sy };
}
```

PDF worker is bundled locally and viewer loads pdf.js only client-side. Citation navigation waits for page render, draws persisted blocks, scrolls the first into view, and recomputes on zoom/resize/rotation. Image citations use `bbox_px`; PDF citations use `bbox_pdf`.

- [ ] **Step 3: Implement defense-in-depth table sanitization and split view**

Use DOMPurify with only table/caption/row/cell tags and colspan/rowspan attributes. Render table HTML beside the highlighted page with a text-quote fallback if sanitization leaves no table. No remote resource or arbitrary link is allowed.

- [ ] **Step 4: Verify geometry and commit**

Run: `npm --prefix apps/web test -- --run src/lib/geometry.test.ts src/components/viewer/TablePanel.test.tsx && npm --prefix apps/web run build`  
Expected: all PASS and pdf.js SSR-free build. Save PDF/image/table screenshots at two zooms.

Commit: `git add apps/web proof/P6/viewer_geometry.md && git commit -m "feat(P6-T04): add source viewers and block highlights"`

**Acceptance:** Citation opens correct document/page/block; highlights track viewport transforms; image sources work; table panel preserves structure without active content.

### P6-T05: Prove five use cases and 20-of-20 citation geometry end to end

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P6-T02, P6-T03, P6-T04  
**Requirements:** PRD UC1–UC5, P6 proof/gate | **Decisions:** D-025, D-027, D-034  
**Proof:** `proof/P6/use_cases.webm`, `proof/P6/citation_geometry.json`, `proof/P6/playwright/`

**Files:**
- Create: `apps/web/e2e/use-cases.spec.ts`, `apps/web/e2e/citation-highlight.spec.ts`, `apps/web/playwright.config.ts`
- Create: `scripts/verify_highlights.py`

- [ ] **Step 1: Implement deterministic browser fixtures and geometry assertions**

Seed real parsed sample documents and recorded verified answers through test APIs; never inject a highlight directly into the DOM. Playwright clicks actual citation chips and compares overlay rectangles with independently calculated expected viewport rectangles. Record document/page/block IDs, zoom, rotation, expected/actual coordinates, and tolerance.

- [ ] **Step 2: Write the five required use-case journeys**

Cover factual question/source passage, exact table cell region, cross-document answer, clickable citation/highlight, and insufficient-source refusal. Each journey begins through the visible UI and asserts final verified state. Capture video and failure screenshots/traces.

- [ ] **Step 3: Run 20 sampled citations across varied sources**

Select 20 citations covering digital/scanned/downscaled/rotated PDFs, tables, images, multi-block fallback, Hindi/Marathi, and zoom levels. Run: `npm --prefix apps/web exec -- playwright test e2e/citation-highlight.spec.ts --workers=1`  
Expected: 20/20 within 2 CSS pixels per edge; any failed row blocks the gate.

- [ ] **Step 4: Record all use cases and commit**

Set `use: { video: "on", trace: "retain-on-failure", screenshot: "only-on-failure" }` in `playwright.config.ts`, then run: `npm --prefix apps/web exec -- playwright test e2e/use-cases.spec.ts --workers=1`  
Expected: all five PASS with video enabled by configuration. Commit: `git add apps/web/e2e apps/web/playwright.config.ts scripts proof/P6 && git commit -m "test(P6-T05): prove source navigation and citation geometry"`

**Acceptance:** Recordings demonstrate all five UCs; geometry JSON has exactly 20 passing independent samples; browser tests do not bypass citation navigation.

### P6-T06: Close the web UI gate

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P6-T01 through P6-T05  
**Requirements:** PRD P6 gate | **Decisions:** D-001, D-026, D-027  
**Proof:** `proof/P6/gate.json`, `proof/P6/gate_review.md`

**Files:**
- Create: `proof/P6/manifest.json`, `proof/P6/gate_review.md`, `proof/P6/gate.json`
- Modify: `TASKS.md`

- [ ] **Step 1: Run production frontend regression**

Run: `npm --prefix apps/web test -- --run && npm --prefix apps/web run build && npm --prefix apps/web exec -- playwright test --workers=1`  
Expected: unit/build/all E2E PASS with no browser console errors or leaked secrets.

- [ ] **Step 2: Audit answer release and citation samples**

Inspect network/event captures to prove no answer-token streaming and no pre-verification answer rendering. Recalculate 20/20 highlight results from saved geometry, not screenshots alone.

- [ ] **Step 3: Execute gate and commit**

Run: `python scripts/check_gate.py proof/P6/manifest.json --output proof/P6/gate.json`  
Expected: exit 0. Commit: `git add proof/P6 TASKS.md && git commit -m "test(P6-T06): close web UI gate"`

**Acceptance:** Five UCs, verified-only display, and 20/20 correct highlights are independently demonstrated; P7 hardening is unblocked.

---

# P7 — Hardening and Release

**Entry:** P6 gate passed; application is loopback-only until auth is enabled.  
**Exit gate:** Auth/ownership, privacy, quota, logs, Compose, README, load test, clean-machine setup, and final eval pass. Stretch tasks remain excluded from required release status.

### P7-T01: Add Argon2id sessions and end-to-end ownership enforcement

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P6-T06  
**Requirements:** PRD API auth, P7 per-user collections, §12 Secrets | **Decisions:** D-030, D-016, D-031  
**Proof:** `proof/P7/auth_ownership.md`

**Files:**
- Create: `apps/api/app/routers/auth.py`, `apps/api/app/security/passwords.py`, `apps/api/app/security/sessions.py`
- Modify: `apps/api/app/dependencies.py`
- Create: `alembic/versions/0003_auth_hardening.py`
- Modify: every collection/document/conversation/chat/file/blocks route and retrieval repository
- Test: `apps/api/tests/test_auth.py`, `apps/api/tests/test_ownership.py`

**Interfaces:** Produce register/login/logout, `get_current_user() -> User`, opaque revocable cookie sessions, and user-scoped repositories.

- [ ] **Step 1: Write failing auth and cross-user tests**

Cover first-user registration, duplicate email, login wrong password, generic credential error, logout revocation, expired session, cookie attributes, Argon2id hash verification, registration-disabled behavior after initial owner unless explicitly enabled, and cross-user 404 for every collection/document/file/block/conversation/chat route. Include out-of-scope dense/lexical results and citation IDs.

- [ ] **Step 2: Implement password and opaque session primitives**

```python
# apps/api/app/security/passwords.py
from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    return _password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return _password_hash.verify(password, encoded)
```

Generate at least 32 random bytes for session tokens, store only SHA-256 token hashes with expiry/revocation, and send raw token only in an HTTP-only Secure `__Host-citerag_session` cookie with `Path=/`, no Domain, and SameSite=Lax. Add constant-time lookup behavior and login throttling.

- [ ] **Step 3: Enforce user scope in every query and browser flow**

Replace development identity outside explicit loopback tests. Authorization belongs in SQL/vector filters and object lookups, not route-only checks. Next route proxy forwards cookies but never exposes session tokens to JavaScript. Preserve original 404 semantics for objects owned by another user.

- [ ] **Step 4: Verify full ownership matrix and commit**

Run: `python -m pytest apps/api/tests/test_auth.py apps/api/tests/test_ownership.py -v && npm --prefix apps/web exec -- playwright test --workers=1`  
Expected: all PASS; non-loopback startup without auth fails closed. Commit: `git add apps/api apps/web alembic proof/P7/auth_ownership.md && git commit -m "feat(P7-T01): add secure sessions and ownership enforcement"`

**Acceptance:** No route, retrieval branch, file, citation, or deletion bypasses ownership; passwords/sessions are hashed, revocable, expired, and never logged.

### P7-T02: Enforce confidentiality controls and browser/network security

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P7-T01  
**Requirements:** PRD §12 Privacy/Secrets, §16 confidential risk | **Decisions:** D-028, D-029, D-033  
**Proof:** `proof/P7/privacy_security.md`

**Files:**
- Create: `apps/api/app/routers/privacy.py`, `apps/api/app/security/headers.py`, `apps/web/src/components/library/ConfidentialityDialog.tsx`
- Modify: `apps/api/nim_gateway/privacy.py`, `apps/api/nim_gateway/gateway.py`
- Modify: NIM gateway, worker guards, Next proxy, `.env.example`
- Test: `apps/api/tests/test_confidentiality.py`, `apps/api/tests/test_security_headers.py`

**Interfaces:** Produce audited collection confidentiality override and a gateway guard evaluated immediately before every hosted call.

- [ ] **Step 1: Write failing hosted-transfer and override tests**

Assert default-confidential collection cannot embed, rewrite, rerank, answer, verify, judge, or use a fallback endpoint. Override requires authenticated owner, explicit current-terms version/date acknowledgment, and collection scope. Revoking confidentiality blocks subsequent calls but does not claim to recall data already sent.

- [ ] **Step 2: Implement central guard and audit record**

Reuse P2-T04's `HostedTransferGuard.authorize(context,stage)` inside `NIMGateway.call`, not only UI/routes. Extend its CLI-only override with an authenticated owner API and the same append-only `privacy_audit` table storing actor, previous/new flag, terms identifier, timestamp, and trace ID. Direct worker/eval calls continue passing the same collection context.

- [ ] **Step 3: Apply network/browser hardening**

Set explicit CORS origin allowlist, Host/TrustedHost config, request/body caps, CSP, `X-Content-Type-Options: nosniff`, frame denial, referrer policy, and secure cookie behavior. Server routes alone access NIM/database/Redis/Qdrant. `.env.example` documents names with empty values and generated development secrets are excluded from commits.

- [ ] **Step 4: Verify blocked calls and browser protections**

Run: `python -m pytest apps/api/tests/test_confidentiality.py apps/api/tests/test_security_headers.py -v && npm --prefix apps/web test -- --run`  
Expected: all PASS and mock transport observes zero requests for blocked stages. Commit: `git add apps/api apps/web .env.example proof/P7/privacy_security.md && git commit -m "feat(P7-T02): enforce confidential data transfer controls"`

**Acceptance:** Hosted transfer cannot bypass guard through worker/eval/fallback; override is explicit/audited; security headers and secret boundaries are tested.

### P7-T03: Add per-model usage accounting and quota dashboard

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P2-T04, P7-T01  
**Requirements:** PRD §11, P7 quota dashboard | **Decisions:** D-003, D-004, D-033  
**Proof:** `proof/P7/quota_dashboard.md`

**Files:**
- Create: `apps/api/app/routers/usage.py`, `apps/web/src/components/usage/QuotaDashboard.tsx`, `alembic/versions/0004_model_calls.py`
- Modify: `apps/api/nim_gateway/gateway.py`
- Test: `apps/api/tests/test_usage.py`, `apps/web/src/components/usage/QuotaDashboard.test.tsx`

**Interfaces:** Produce durable `model_calls` events and `GET /usage?window=24h` aggregated per model/stage/status; supported windows are `24h`, `7d`, and `30d`.

- [ ] **Step 1: Write failing accounting tests**

Record attempted/succeeded/failed/cached/fallback calls, latency, retries, batch item counts, reported credit/token usage when present, and trace/collection IDs without chunk text. Cached embedding reuse increments cache hits, not provider calls. Unknown credit balance displays unknown rather than zero.

- [ ] **Step 2: Implement transactional usage events and aggregation**

Create `model_calls(id,user_id,collection_id,trace_id,stage,model,requested_model,outcome,cached,item_count,retries,latency_ms,reported_credits,created_at)`. Insert usage in the gateway finally path with redacted errors; usage-write failure fails the hosted call before content is released and emits a structured alert.

- [ ] **Step 3: Implement owner-scoped dashboard**

Show current measured RPM/token-bucket state, calls by stage/model, cache savings, failures/fallbacks, reported credits where available, and ingestion-versus-query split. No estimate is labeled as provider truth. Dashboard polls only while visible and uses authenticated user scope.

- [ ] **Step 4: Verify accounting against recorded fixtures and commit**

Run focused tests; expected provider-call totals exactly match mock transport counts, including retries/fallbacks and zero-call cache hits. Commit: `git add apps/api apps/web alembic proof/P7/quota_dashboard.md && git commit -m "feat(P7-T03): add model usage accounting dashboard"`

**Acceptance:** Every hosted attempt is attributable to user/collection/trace/model; quotas/credits distinguish measured, reported, estimated, and unknown values.

### P7-T04: Complete structured observability and dependency health

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P7-T03  
**Requirements:** PRD §12 Observability/Reliability, API health | **Decisions:** D-033, D-026  
**Proof:** `proof/P7/observability.md`, `proof/P7/redaction_tests.md`

**Files:**
- Create: `packages/common/citerag_common/logging.py`, `apps/api/app/middleware/tracing.py`
- Modify: worker/API/eval logging and `/health`
- Test: `packages/common/tests/test_logging.py`, `apps/api/tests/test_health.py`

**Interfaces:** Produce JSON log formatter, trace propagation, redaction, and dependency-specific liveness/readiness.

- [ ] **Step 1: Write failing structured-log and redaction tests**

Assert valid JSON, UTC timestamp, level/service/trace/job/document/conversation/stage/duration fields, and recursive redaction of authorization, API keys, passwords, session cookies, connection-string passwords, and multipart content. Confidential content fields are omitted even under different key casing.

- [ ] **Step 2: Implement formatter and trace middleware**

```python
# packages/common/citerag_common/logging.py
import json
import logging
from datetime import datetime, timezone

_SECRET_KEYS = {"authorization", "api_key", "password", "cookie", "set-cookie", "raw_multipart"}


def redact(value):
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in _SECRET_KEYS else redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"ts": datetime.now(timezone.utc).isoformat(), "level": record.levelname, "message": record.getMessage()}
        for key in ("service", "trace_id", "job_id", "document_id", "conversation_id", "stage", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(redact(payload), ensure_ascii=False)
```

Middleware accepts no untrusted trace ID without validation, generates a UUID by default, and propagates contextvars through API/Celery/NIM/eval. Health checks have short timeouts and cached NIM status so they cannot amplify hosted usage.

- [ ] **Step 3: Verify request/job correlation and degraded health**

Run unit tests, then execute one ingestion and one chat with a deliberate parser outage and verifier failure. Expected same trace ID across stages, terminal failure visible, no secret/content leak, and `/health` identifies exact degraded dependencies without credentials.

- [ ] **Step 4: Commit observability evidence**

Commit: `git add packages/common apps/api apps/worker packages/eval proof/P7 && git commit -m "feat(P7-T04): add redacted structured observability"`

**Acceptance:** Every request/job has correlated JSON traces and per-stage timing; redaction tests cover nested secrets; health does not spend model calls.

### P7-T05: Finish Compose, parse startup, and clean setup documentation

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P7-T01 through P7-T04  
**Requirements:** PRD §12 Portability/Platform/Privacy, P7 | **Decisions:** D-002, D-004, D-006, D-029  
**Proof:** `proof/P7/compose_validation.md`, `proof/P7/setup_prerequisites.md`

**Files:**
- Modify: `docker-compose.yml`, `README.md`, `.env.example`, `apps/parse_service/start.sh`
- Create: `apps/api/Dockerfile`, `apps/worker/Dockerfile`, `apps/web/Dockerfile`, `scripts/bootstrap.sh`, `scripts/doctor.py`

**Interfaces:** Produce one documented Compose startup plus separate Linux/WSL2 parse startup; doctor checks prerequisites without exposing secrets.

- [ ] **Step 1: Add production-like service definitions and healthchecks**

Compose builds API, worker, and web; runs PostgreSQL, Redis, selected vector store; mounts private file/proof volumes; loads secrets only from environment; applies non-root users, read-only root filesystems where compatible, bounded resources, restart policies, and dependency healthchecks. GPU parse service remains outside Compose.

Run: `docker compose config -q && docker compose build`  
Expected: valid resolved config with no literal API key and successful images.

- [ ] **Step 2: Implement bootstrap and doctor checks**

`bootstrap.sh` refuses missing Python/Node/Docker/WSL GPU prerequisites, generates no silent production secrets, runs migrations, and prints exact next steps. `doctor.py` reports OS/WSL, Docker, GPU visibility, parse health, database/vector/Redis health, configured model verification, and environment-key presence as boolean only.

- [ ] **Step 3: Write README as the only required setup guide**

Include exact clone/prerequisite/env/NVIDIA terms/WSL parse/model verification/migration/Compose/worker/web URLs/test/eval commands. Document confidential default, original upload sensitivity, proof artifact sensitivity, backup/restore, logs, fallback behavior, known limits, and clean shutdown. No step relies on an undocumented shell variable or conversation context.

- [ ] **Step 4: Validate fresh containers and commit**

Run: `docker compose down && docker compose up -d --build && python scripts/doctor.py --require-ready`  
Expected: all non-parse services healthy, parse separately healthy, migration current, web reachable. Commit: `git add docker-compose.yml apps scripts README.md .env.example proof/P7 && git commit -m "chore(P7-T05): complete reproducible deployment setup"`

**Acceptance:** `docker compose up` starts every non-GPU service; parse script works under WSL2/Linux; README includes setup and privacy without hidden manual steps.

### P7-T06: Run full CI and sustained 8-questions-per-minute load test

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P7-T05  
**Requirements:** PRD §15 CI, P7 load proof, §4 latency | **Decisions:** D-003, D-033, D-034  
**Proof:** `proof/P7/ci_run.md`, `proof/P7/load_test.json`, `proof/P7/load_test.md`

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create: `scripts/load_test.py`, `apps/api/tests/test_load_scheduler.py`

**Interfaces:** Produce paced load at exactly 8 question starts/minute and a report separating application fixture load from live-hosted final-eval latency.

- [ ] **Step 1: Write failing scheduler and CI-safety tests**

Test 80 starts over ten minutes at 7.5-second intervals, no burst catch-up after stall, graceful cancellation, per-stage latency/error capture, and no live NIM unless exact budget acknowledgment is present. CI configuration test asserts no live smoke scripts or NVIDIA key secrets are invoked.

- [ ] **Step 2: Implement load runner and complete CI matrix**

CI runs Python unit/integration tests, web unit/build, migration checks, Docker config, and Playwright against recorded model fixtures. Live model smoke remains manually dispatched with explicit budget. Load runner uses recorded realistic-latency model fixtures for sustained application load and labels this mode in every artifact.

- [ ] **Step 3: Execute sustained load and inspect correctness**

Run: `python scripts/load_test.py --rate 8 --duration 600 --mode recorded --output proof/P7/load_test.json`  
Expected: 80 question starts, no unsupported/unverified answer, no cross-user data, no unbounded queue/memory growth, and per-stage p50/p95/error rates. Separately cite P5/P7 live final-eval p95 for the PRD's end-to-end latency target; do not substitute fixture timing as hosted-model truth.

- [ ] **Step 4: Commit CI and load evidence**

Commit: `git add .github scripts apps/api/tests proof/P7 && git commit -m "test(P7-T06): verify full CI and eight question load"`

**Acceptance:** CI runs required unit suites on every push without quota; 8/min sustained test is complete and honest about fixture versus live measurements; live latency is reported from real traces.

### P7-T07: Prove clean-machine setup and final release gate

**Status:** Not started | **Owner:** Atharva  
**Depends on:** P7-T01 through P7-T06  
**Requirements:** PRD P7 proof/gate, §4, §12 | **Decisions:** D-001, D-029, D-033, D-034, D-035  
**Proof:** `proof/P7/clean_machine_setup.md`, `proof/P7/final_eval.json`, `proof/P7/release_gate.json`, `proof/P7/release_review.md`

**Files:**
- Create: `scripts/release_check.py`
- Modify: `README.md` only for setup steps discovered during clean validation

- [ ] **Step 1: Perform a fresh-clone installation using README only**

On a clean VM/machine profile with no repository-specific shell state, clone the committed release candidate and follow README verbatim. Record every command, prompt, version, duration, failure, and correction. Do not use notes from this plan unless they are already in README.

- [ ] **Step 2: Reach one verified answer and test security boundaries**

Start the WSL2/Linux parser and Compose stack, ingest a non-confidential sample, ask a factual and unanswerable question, click citations, and verify quote/highlight/verifier trace. Confirm auth required, cross-user denial, confidential default block, no browser secrets, and healthy dependencies.

- [ ] **Step 3: Run final eval and release checks**

Run full final gold evaluation on the release config and commit `eval_runs` row/config hash/git SHA. Compare every P5 target/decision and ensure no prompt/model/threshold/chunking difference lacks an eval. Run all offline tests, CI, and `scripts/release_check.py`; optional stretch tasks are not required checks.

- [ ] **Step 4: Close release gate and commit**

Run: `python scripts/check_gate.py proof/P7/manifest.json --output proof/P7/release_gate.json`  
Expected: exit 0 only after clean README setup reaches a working verified answer and all required evidence exists. Commit: `git add README.md scripts proof/P7 TASKS.md && git commit -m "test(P7-T07): close clean machine release gate"`

**Acceptance:** Fresh clone reaches working verified answer from README alone; final real-model metrics are recorded; auth/privacy/ownership pass; required v1 is complete without stretch features.

---

# P7 Stretch — Optional and Non-Blocking

These tasks begin only after P7-T07. Each requires its own decision update, privacy review, tests, and eval evidence. They are not part of v1 completion percentages.

### P7-T90: Optional DOCX/PPTX conversion through PDF

**Status:** Not started (optional) | **Owner:** Atharva  
**Depends on:** P7-T07  
**Requirements:** PRD §2/P7 stretch only | **Decisions:** D-035, D-028  
**Proof:** `proof/P7/stretch_office.md`

**Files:**
- Create: `apps/worker/tasks/office_convert.py`, `apps/worker/tests/test_office_convert.py`, `proof/P7/stretch_office.md`
- Modify: `DECISION.md`, `apps/api/app/routers/documents.py`, `apps/web/src/components/library/UploadDialog.tsx`

- [ ] **Step 1:** Record a new decision enabling LibreOffice headless conversion, supported MIME signatures, sandbox profile, conversion timeout, page-count/size caps, and failure cleanup.
- [ ] **Step 2:** Write failing tests for DOCX/PPTX signature validation, macro/non-PDF active content rejection, conversion timeout, output PDF signature, and deleted temporary profiles.
- [ ] **Step 3:** Implement isolated conversion to a derived PDF while retaining the original upload and conversion provenance; route only the derived PDF through P1 rendering/parsing.
- [ ] **Step 4:** Run unit/integration tests and a conversion corpus, then rerun final eval before enabling the UI accept extensions.
- [ ] **Step 5:** Commit behind a disabled-by-default flag with `feat(P7-T90): add optional office document conversion`.

**Acceptance:** Original/derived files remain distinguishable, conversion is bounded/sandboxed, citations land on derived PDF pages, and release behavior is unchanged while flag is off.

### P7-T91: Optional page-image retrieval

**Status:** Not started (optional) | **Owner:** Atharva  
**Depends on:** P7-T07  
**Requirements:** PRD P7 stretch only | **Decisions:** D-035, D-007, D-034  
**Proof:** `proof/P7/stretch_page_image.md`

**Files:**
- Create: `apps/api/app/retrieval/page_image.py`, `apps/api/tests/test_page_image.py`, `proof/P7/stretch_page_image.md`
- Modify: `DECISION.md`, `config/models.yaml`, `config/retrieval.yaml`, `packages/common/citerag_common/vector_store.py`

- [ ] **Step 1:** Smoke-test the exact multimodal embed/rerank models, routes, dimensions, image limits, terms, and quota; record a new model/store decision before implementation.
- [ ] **Step 2:** Write failing fixtures for image payload constraints, separate vector namespaces, fused text/image ranking, provenance, and confidential transfer blocking.
- [ ] **Step 3:** Implement a separate disabled-by-default retrieval branch without changing text-only chunk IDs, cache keys, or citation contracts.
- [ ] **Step 4:** Run full text-only regression plus image ablation on final gold; enable only if measured quality/latency/quota trade-off is accepted.
- [ ] **Step 5:** Commit with `feat(P7-T91): add optional page image retrieval` and linked eval/decision.

**Acceptance:** Text-only baseline is unchanged when disabled; image results resolve to valid page/block citations; privacy and quota guards cover new models.

### P7-T92: Optional verified answer cache

**Status:** Not started (optional) | **Owner:** Atharva  
**Depends on:** P7-T07  
**Requirements:** PRD P7 stretch only | **Decisions:** D-035, D-029, D-030, D-034  
**Proof:** `proof/P7/stretch_answer_cache.md`

**Files:**
- Create: `apps/api/app/services/answer_cache.py`, `apps/api/tests/test_answer_cache.py`, `alembic/versions/0005_answer_cache.py`, `proof/P7/stretch_answer_cache.md`
- Modify: `DECISION.md`, `apps/api/app/services/chat.py`, `config/retrieval.yaml`

- [ ] **Step 1:** Record a cache decision defining key `(user,collection,document set,question,rewrite,model/config hash,corpus revision)` and exclusion of confidential collections by default.
- [ ] **Step 2:** Write failing tests for cross-user/collection isolation, document add/delete/update invalidation, model/prompt/threshold invalidation, cached verifier provenance, and no citation to deleted blocks.
- [ ] **Step 3:** Implement storage/lookup behind a disabled flag; return only previously verified answers with complete citations/traces and an explicit cache-hit marker.
- [ ] **Step 4:** Run security, deletion, correctness, and full eval tests; compare latency/quota benefit without changing displayed answer content.
- [ ] **Step 5:** Commit with `feat(P7-T92): add optional verified answer cache`.

**Acceptance:** No stale/cross-user/confidential answer can be served; cache hits preserve verification/citation invariants; disabled path is byte-for-byte compatible with release responses.

---

# Requirement Traceability

| Requirement | Implementing tasks | Proof |
| --- | --- | --- |
| FR-ING-1 accepted inputs, SHA-256, duplicates | P1-T01, P1-T02 | P1 upload API/schema |
| FR-ING-2 RGB 150-dpi render and downscale | P1-T03 | P1 render geometry |
| FR-ING-3 exact parser prompt/settings | P0-T03, P1-T04 | P0 raw output, P1 postprocess |
| FR-ING-4 raw output and postprocessed blocks | P0-T03, P1-T04 | P0 raw output, P1 postprocess |
| FR-ING-5 pixel/PDF coordinate forms | P1-T03 | P1 render geometry |
| FR-ING-6 per-page retry/resume | P1-T05 | P1 reliability |
| FR-ING-7 document/page progress | P1-T06, P6-T02 | P1 document API, P6 library |
| FR-ING-8 measured parse concurrency | P1-T08 | P1 concurrency |
| FR-CHK-1 typed-block chunking | P1-T04, P1-T07, P2-T01 | P1 classes, P2 text chunks |
| FR-CHK-2 header/footer/page-number exclusion | P1-T07, P2-T03 | P1 class review, P2 chunk dumps |
| FR-CHK-3 text size/overlap/boundaries | P2-T01 | P2 text chunks |
| FR-CHK-4 table chunking/HTML/flattening | P2-T02 | P2 table/chart contract |
| FR-CHK-5 chart extracted-data chunks | P2-T02 | P2 table/chart contract |
| FR-CHK-6 section path in embedded text only | P2-T03 | P2 chunk dumps |
| FR-CHK-7 continuation links | P2-T03, P3-T05 | P2 continuation review, P3 context |
| FR-CHK-8 source blocks/pages/bboxes | P2-T03, P2-T05, P2-T06 | P2 chunk dumps/index contract |
| FR-CHK-9 tokenizer and embedding input limit | P2-T01 | P2 text chunks/histogram |
| FR-IDX-1 batch embedding/measured dimension | P2-T04 | P2 gateway/cache |
| FR-IDX-2 vector payload | P2-T05 | P2 index contract |
| FR-IDX-3 PostgreSQL simple tsvector | P2-T05 | P2 index contract |
| FR-IDX-4 embedding cache | P2-T04, P2-T06 | P2 cache/quota report |
| FR-RET-1 standalone conditional rewrite | P3-T02 | P3 rewrite review |
| FR-RET-2 filtered dense/lexical top 40 | P3-T03 | P3 hybrid search |
| FR-RET-3 RRF constant 60 | P3-T03 | P3 hybrid search |
| FR-RET-4 rerank 30-to-8 | P3-T04 | P3 rerank contract |
| FR-RET-5 calibrated abstention | P3-T05, P5-T03 | P3 mechanism, P5 calibration |
| FR-RET-6 labeled bounded context | P3-T05 | P3 context traces |
| FR-GEN-1 grounded prompt/citations | P4-T01 | P4 answer schema |
| FR-GEN-2 JSON schema and one repair | P4-T01 | P4 answer schema |
| FR-GEN-3 exact quotes up to 25 words | P4-T01, P4-T02 | P4 quote matching |
| FR-VER-1 structural/context-ID checks | P4-T01, P4-T02 | P4 answer/structure tests |
| FR-VER-2 normalized fuzzy quote check | P4-T02, P5-T03 | P4 quote matching, P5 calibration |
| FR-VER-3 batched entailment | P4-T03 | P4 entailment contract |
| FR-VER-4 removal/partial/regeneration/refusal | P4-T04 | P4 verification policy |
| FR-VER-5 block citation resolution | P4-T05 | P4 citation resolution |
| FR-VER-6 persisted verifier audit | P4-T03, P4-T06 | P4 chat traces |
| FR-UI-1 library/upload/progress/delete | P6-T02 | P6 library |
| FR-UI-2 chat/SSE/final-only answer | P4-T06, P6-T01, P6-T03 | P4 SSE, P6 chat |
| FR-UI-3 summary/explanation/sources | P6-T03 | P6 chat answer |
| FR-UI-4 inline citations and highlights | P6-T03, P6-T04, P6-T05 | P6 use cases/geometry |
| FR-UI-5 partial/refusal/failure states | P6-T03 | P6 chat answer |
| FR-UI-6 table side panel | P6-T04 | P6 viewer geometry |
| Data model and traces | P1-T01, P3-T04, P4-T06 | Schema/retrieval/chat traces |
| API collections/documents/files/blocks | P1-T02, P1-T06 | P1 upload/document APIs |
| API chat/conversations/health | P4-T06, P7-T04 | P4 SSE, P7 observability |
| API auth/per-user ownership | P7-T01 | P7 auth/ownership |
| Privacy/secrets/confidential block | P0-T06, P2-T04, P7-T02 | P0 terms, P2 guard, P7 privacy security |
| Quota/rate/caching/dashboard | P0-T05, P2-T04, P7-T03 | P0 limits, P2 cache, P7 quota |
| Evaluation and success metrics | P3-T06, P4-T07, P5-T01–T05 | P3/P4/P5 reports |
| Compose/portability/README | P7-T05, P7-T07 | P7 compose/clean-machine |
| CI and load test | P7-T06 | P7 CI/load |
| Stretch isolation | P7-T90–T92 | Optional proof only |

# Final Review Checklist

- [ ] All task IDs are unique and every task has status, owner, dependencies, files, tests, acceptance, and proof.
- [ ] Every PRD functional requirement and P0–P7 proof/gate row maps to a task above.
- [ ] No enabled config contains an unverified model ID, dimension, route, limit, score assumption, or guessed threshold.
- [ ] Offline tests make zero hosted calls; every live command computes and acknowledges an exact budget.
- [ ] No task claims a gate passes from summaries alone; artifacts and independent test/reviewer evidence are committed.
- [ ] Function names and data fields match Canonical Internal Contracts and referenced earlier tasks.
- [ ] No final answer can contain unsupported, quote-failed, unverified, out-of-scope, or provenance-free claims.
- [ ] Original metrics and decisions remain auditable through every calibration or fallback.
- [ ] Required release excludes P7-T90–T92 and works with all stretch flags disabled.

