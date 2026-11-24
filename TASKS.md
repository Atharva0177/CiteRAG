# CiteRAG — Detailed Implementation Tasks

Source of truth: [PRD.md](PRD.md) v1.0, 15 Nov 2026. Decision register: [DECISION.md](DECISION.md). Owner: **Atharva** unless explicitly reassigned.

## How to use this checklist

- **62 task records:** 61 core tasks plus optional `P7-T08`. Every task starts `not_started`.
- Valid statuses: `not_started`, `in_progress`, `blocked`, `in_review`, `done`. Mark `done` only after every acceptance check passes and real proof is committed at the listed path. **Planned proof links are destinations, not claims that evidence exists.**
- Gates are sequential: `P0 gate → P1 gate → … → P7 gate`. Work may run in parallel only inside an unlocked phase when listed dependencies allow it. Record a blocker instead of skipping a dependency.
- Commit convention: `type(Pn-Tnn): message`, where type is `feat`, `fix`, `test`, `docs`, or `chore`; one task per commit where practical. CI runs offline unit tests on every push.
- Every prompt, model, threshold, or chunking change attaches an eval run, config hash, and git SHA. Initial P0/P1 selections use gate evidence and applicable config/version identifiers; they do not require a future full evaluation baseline.
- Ordinary tests use recorded fixtures and consume **zero NIM quota**. Live smoke tests, the 60-call burst, judge calls, and load tests are separate, explicitly initiated procedures.
- Exact hosted model IDs, request shapes, vector dimensions, input limits, quotas, parser classes, rerank ranges, and calibrated thresholds must come from evidence—not assumptions.
- Pre-P7 APIs use a development-only single-user identity. This is not multi-user authentication and must not be exposed as such. Collection-level confidential flags block hosted indexing from P1 until a local model path exists.
- Create PRD §18 directories at repository root `E:\RAG`; do **not** add another nested `citerag/` directory.
- Paths below are planned implementation files. Final file placement may be refined without dropping required behavior or proof.

## P0 — Environment and smoke tests

**Entry:** PRD and decision register approved. **Exit:** all P0 gate checks and required proof pass.

<a id="p0-t01"></a>
### P0-T01 — Bootstrap repository, configuration, and offline CI

- **Status:** `in_review` | **Owner:** Atharva
- **PRD:** §5, §11, §12, §15, §18 | **Depends:** none
- **Decisions:** [D-F02](DECISION.md#d-f02), [D-F10](DECISION.md#d-f10)
- **Files:** `pyproject.toml`, `package.json` or workspace bootstrap files, `.env.example`, `.gitignore`, `config/`, `apps/`, `packages/`, `proof/`, `.github/workflows/ci.yml`, `tests/fixtures/README.md`
- **Steps:**
  - [x] Create root PRD §18 directories without nesting another `citerag/`; pin package managers and Python/Node versions.
  - [x] Add reproducible setup commands, ignored secret/storage paths, and `.env.example` containing names only—never real keys.
  - [x] Establish configuration loading, redacted structured logging, development-only single-user identity, and fixture-only hosted-call policy.
  - [x] Add CI that installs locked dependencies and runs offline unit/lint checks; prove network-disabled fixture tests cannot call NIM.
- **Verify:** run documented clean bootstrap and `pytest`; CI is green with no credentials and no hosted calls.
- **Acceptance:** second setup follows one documented path; secrets are absent from browser bundles/logs; all initial directories and fixture policies exist.
- **Proof (planned):** [`proof/P0/bootstrap.md`](proof/P0/bootstrap.md), [`proof/P0/offline_ci.md`](proof/P0/offline_ci.md)

<a id="p0-t02"></a>
### P0-T02 — Validate RTX 5070, CUDA, PyTorch, and vLLM

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §6, §12 Platform, §14 P0, §16 risk 1, §17 | **Depends:** P0-T01
- **Decisions:** [D-F01](DECISION.md#d-f01), [D-F03](DECISION.md#d-f03), [D-P0-01](DECISION.md#d-p0-01)
- **Files:** `apps/parse_service/start.sh`, `apps/parse_service/requirements*.txt`, `apps/parse_service/smoke_gpu.py`
- **Steps:**
  - [ ] Inventory RTX 5070 12 GB, Windows/WSL2 or native Linux, driver, CUDA runtime, and available VRAM.
  - [ ] Select and pin compatible CUDA/PyTorch/vLLM builds from authoritative compatibility documentation; do not guess Blackwell support.
  - [ ] Run GPU tensor and model-load smoke tests for local `Nemotron-3.5-Parse` (0.631B), capturing exact versions and errors.
  - [ ] Exercise vLLM inference and a clean restart; if blocked, test Docling and check hosted parse availability without claiming either works.
- **Verify:** record exact setup/smoke commands, console results, and `nvidia-smi` output; restart reproduces a successful inference or documented fallback.
- **Acceptance:** supported Linux/WSL2 path and compatible versions are evidenced; VRAM is recorded; D-P0-01 has sufficient evidence for resolution.
- **Proof (planned):** [`proof/P0/gpu_stack.md`](proof/P0/gpu_stack.md), [`proof/P0/gpu_smoke.log`](proof/P0/gpu_smoke.log)

<a id="p0-t03"></a>
### P0-T03 — Run local parser on three representative pages

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §6, §7.1 FR-ING-2–4, §14 P0, §16 risks 1/4 | **Depends:** P0-T02
- **Decisions:** [D-F01](DECISION.md#d-f01), [D-F04](DECISION.md#d-f04), [D-P0-01](DECISION.md#d-p0-01)
- **Files:** `apps/parse_service/server.py`, `apps/parse_service/client.py`, `apps/parse_service/render.py`, `apps/parse_service/README.md`, `tests/fixtures/parse/`
- **Steps:**
  - [ ] Serve the parser locally and render digital, scanned, and table-heavy sample pages to RGB at 150 dpi; downscale proportionally to fit 1664 × 2048 when needed.
  - [ ] Use exact prompt `</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>`, `max_new_tokens=8744`, temperature 0, `top_k=1`, `repetition_penalty=1.1`, `skip_special_tokens=false`.
  - [ ] Preserve raw control tokens; run `postprocess_document` with actual render dimensions and retain markdown, class, normalized bbox, pixel bbox, and text.
  - [ ] Produce one overlay PNG per sample, inspect text/regions, and record double-pass behavior and any Docling fallback result.
- **Verify:** run the documented parse smoke command; compare all three raw outputs and overlays against source pages.
- **Acceptance:** three end-to-end samples have raw output, postprocessed JSON, actual dimensions, and overlays; failures/fallbacks are explicit.
- **Proof (planned):** [`proof/P0/parse_digital.json`](proof/P0/parse_digital.json), [`proof/P0/parse_scanned.json`](proof/P0/parse_scanned.json), [`proof/P0/parse_table.json`](proof/P0/parse_table.json), [`proof/P0/overlay_digital.png`](proof/P0/overlay_digital.png), [`proof/P0/overlay_scanned.png`](proof/P0/overlay_scanned.png), [`proof/P0/overlay_table.png`](proof/P0/overlay_table.png)

<a id="p0-t04"></a>
### P0-T04 — Smoke five hosted model roles through one gateway

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5, §6, §17 | **Depends:** P0-T01
- **Decisions:** [D-F03](DECISION.md#d-f03), [D-P0-02](DECISION.md#d-p0-02)
- **Files:** `apps/api/nim_gateway/`, `apps/api/smoke_models.py`, `tests/fixtures/nim/`, `tests/test_nim_gateway.py`
- **Steps:**
  - [ ] Read current build.nvidia.com model pages; configure exact IDs and request shapes for embed, rerank, rewrite, answer, and verify without hardcoding remembered values.
  - [ ] Route every hosted request through a Python gateway using environment credentials, safe serialization, timeouts, redaction, and response metadata capture.
  - [ ] After explicit authorization, make one minimal live request per role; record status, request/response shape, latency, model/version, and reasoning controls.
  - [ ] Test Super VL answer and Ultra verify roles; activate `llama-3.3-nemotron-super-49b-v1.5` only if Super VL changes/is withdrawn, and Lightning with lower claim batch size only if verify is too slow/rate limited.
- **Verify:** offline replay passes without NIM; separate live smoke report contains five role outcomes and zero exposed secrets.
- **Acceptance:** each hosted role responds or has an evidenced fallback; request shapes, answer JSON support, and available reasoning controls are documented.
- **Proof (planned):** [`proof/P0/hosted_smoke.md`](proof/P0/hosted_smoke.md), [`proof/P0/model_responses/`](proof/P0/model_responses/)

<a id="p0-t05"></a>
### P0-T05 — Measure embedding/rerank contracts and multilingual quality

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5, §7.2 FR-CHK-9, §7.3, §17 | **Depends:** P0-T04
- **Decisions:** [D-P0-03](DECISION.md#d-p0-03), [D-P0-04](DECISION.md#d-p0-04), [D-P0-05](DECISION.md#d-p0-05)
- **Files:** `apps/api/nim_gateway/capabilities.py`, `packages/eval/p0_multilingual.py`, `tests/fixtures/nim/embed_rerank/`
- **Steps:**
  - [ ] Derive vector dimension from the first real embedding response; test empty/invalid input handling and verify consistent dimensions across responses.
  - [ ] Measure embed input-token limit, tokenizer availability or documented proxy, query/passage flags, maximum safe chunk input, and endpoint batch limits.
  - [ ] Verify rerank request route, candidate capacity, output ordering, and observed score range; do not infer calibration from one sample.
  - [ ] Run bounded English/Hindi/Marathi quality probes with labeled samples, expected sources, fixed method, and per-language results; record limitations and keep full evaluation in P5.
- **Verify:** replay recorded contract fixtures offline; live report contains raw measurements and per-language source/rank outcomes, not merely successful HTTP responses.
- **Acceptance:** D-P0-03/04/05 evidence covers dimensions, limits, tokenizer/flags, route/capacity/range, and preliminary multilingual quality with explicit limits.
- **Proof (planned):** [`proof/P0/model_limits.md`](proof/P0/model_limits.md), [`proof/P0/multilingual_probe.md`](proof/P0/multilingual_probe.md), [`proof/P0/multilingual_samples.jsonl`](proof/P0/multilingual_samples.jsonl)

<a id="p0-t06"></a>
### P0-T06 — Measure quota/credits and exercise gateway resilience

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §11, §16 risk 2 | **Depends:** P0-T04
- **Decisions:** [D-P0-06](DECISION.md#d-p0-06)
- **Files:** `apps/api/nim_gateway/rate_limit.py`, `apps/api/nim_gateway/retry.py`, `packages/eval/p0_burst.py`, `tests/fixtures/nim/errors/`
- **Steps:**
  - [ ] Build a request/credit ledger with timestamp, role, model, latency, HTTP result, retry count, and reported usage; redact all content/secrets as appropriate.
  - [ ] After explicit authorization, run a bounded **60-call burst** at controlled concurrency; stop on unsafe quota depletion or provider restrictions.
  - [ ] Measure actual RPM and credit consumption rather than treating third-party 1,000-credit/40-RPM figures as fact.
  - [ ] Replay 429/5xx/timeout fixtures to validate exponential backoff with jitter, per-model token bucket, circuit breaker, and fallback routing.
- **Verify:** offline error tests pass; burst ledger reconciles attempted/succeeded/limited calls and measured credit deltas.
- **Acceptance:** measured limits and test boundaries are reported; retry/circuit behavior is deterministic under fixtures; no routine test consumes quota.
- **Proof (planned):** [`proof/P0/quota_ledger.csv`](proof/P0/quota_ledger.csv), [`proof/P0/burst_report.md`](proof/P0/burst_report.md), [`proof/P0/backoff_tests.md`](proof/P0/backoff_tests.md)

<a id="p0-t07"></a>
### P0-T07 — Verify endpoint status, free-tier terms, and privacy

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §6, §11, §12 Privacy, §16 risks 1–3/8, §17 | **Depends:** P0-T04
- **Decisions:** [D-F10](DECISION.md#d-f10), [D-P0-02](DECISION.md#d-p0-02), [D-P0-06](DECISION.md#d-p0-06)
- **Files:** `config/privacy.yaml`, `docs/provider_terms.md`
- **Steps:**
  - [ ] Capture current official URLs and access dates for each hosted role and fallback, including early-access or withdrawal notices.
  - [ ] Confirm free endpoint/gating/credit terms and request quotas from authoritative sources, distinguishing observed behavior from written terms.
  - [ ] Record input retention/privacy terms and whether hosted processing is acceptable; never index confidential documents on hosted free tier.
  - [ ] Define enforced confidential-collection policy and README warning requirements; flag uncertain terms rather than implying safety.
- **Verify:** every claim links to an official source/access date or observed smoke/burst evidence; secret and confidential-data checks pass.
- **Acceptance:** current endpoint, quota, and privacy posture is explicit; hosted confidential indexing is prohibited; unresolved terms block affected usage.
- **Proof (planned):** [`proof/P0/provider_terms.md`](proof/P0/provider_terms.md), [`proof/P0/privacy_checklist.md`](proof/P0/privacy_checklist.md)

<a id="p0-t08"></a>
### P0-T08 — Freeze measured model configuration and P0 decisions

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5–6, §11–12, §14 P0, §17 | **Depends:** P0-T02, P0-T03, P0-T04, P0-T05, P0-T06, P0-T07
- **Decisions:** [D-P0-01](DECISION.md#d-p0-01), [D-P0-02](DECISION.md#d-p0-02), [D-P0-03](DECISION.md#d-p0-03), [D-P0-04](DECISION.md#d-p0-04), [D-P0-05](DECISION.md#d-p0-05), [D-P0-06](DECISION.md#d-p0-06)
- **Files:** `config/models.yaml`, `config/retrieval.yaml`, `config/settings.yaml`, `docs/configuration.md`
- **Steps:**
  - [ ] Resolve six P0 decision records with evidence/config identifiers, rationale, fallbacks, and Atharva approval; update decision history.
  - [ ] Write exact model IDs, request shapes, reasoning controls, generation settings, dimension, limits, batch sizes, and measured gateway settings to versioned config.
  - [ ] Keep Qdrant default unless dimension evidence supports the allowed pgvector simplification; record selection and reversal trigger.
  - [ ] Consolidate raw parse outputs, three overlays, hosted outcomes, limits/terms, and fallback records in the smoke report; audit unresolved values.
- **Verify:** config schema validation and offline gateway tests pass; every configured value traces to proof or an accepted PRD requirement.
- **Acceptance:** all six model roles respond or have recorded fallbacks; six P0 decisions are resolved; no guessed IDs/dimensions/limits remain.
- **Proof (planned):** [`proof/P0/smoke_report.md`](proof/P0/smoke_report.md), [`proof/P0/model_limits.md`](proof/P0/model_limits.md), [`config/models.yaml`](config/models.yaml)

### P0 gate checklist

- [ ] `proof/P0/smoke_report.md` links all required artifacts and commands.
- [ ] Three raw parse outputs and three overlays exist; digital/scanned/table samples were reviewed.
- [ ] Hosted model/limit table includes dimensions, limits, routes, reasoning controls, preliminary multilingual quality, quotas, and terms evidence.
- [ ] All six roles respond or have recorded fallbacks; `config/models.yaml` validates.
- [ ] D-P0-01 through D-P0-06 are resolved and proof is committed before P1 begins.

## P1 — Ingestion and parsing

**Entry:** P0 gate passed and committed. **Exit:** ingestion pipeline, ten reviewed pages, retry proof, and concurrency decision pass.

<a id="p1-t01"></a>
### P1-T01 — Create metadata schema and processing-state migrations

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.1 FR-ING-6–7, §8, §12 | **Depends:** P0 gate
- **Decisions:** [D-F09](DECISION.md#d-f09), [D-F10](DECISION.md#d-f10)
- **Files:** `apps/api/db/`, `apps/api/migrations/`, `tests/test_migrations.py`
- **Steps:**
  - [ ] Add initial migrations/models for `users`, `collections`, `documents`, `pages`, and `blocks` with all PRD key columns and relational constraints.
  - [ ] Add collection ownership/confidential flag, document state/page counts, per-page parse state/timing, job checkpoints, and trace IDs as explicit additive fields.
  - [ ] Define legal transitions for queued, rendering, parsing, chunking, embedding, indexed, and failed, including partial page failure semantics.
  - [ ] Add unique/check/foreign-key indexes needed for collection duplicates, page ordering, idempotent recovery, and block provenance.
- **Verify:** upgrade/downgrade or documented forward migration test passes on empty PostgreSQL; rollback recovery and constraints are tested.
- **Acceptance:** all required fields/tables exist; no impossible status transition is accepted; confidential and restart metadata are durable.
- **Proof (planned):** [`proof/P1/schema.md`](proof/P1/schema.md), [`proof/P1/migration_tests.log`](proof/P1/migration_tests.log)

<a id="p1-t02"></a>
### P1-T02 — Implement collections, validated upload, duplicates, and privacy block

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.1 FR-ING-1, §8–9, §12 Privacy, §16 risk 8 | **Depends:** P1-T01
- **Decisions:** [D-F09](DECISION.md#d-f09), [D-F10](DECISION.md#d-f10), [D-P1-03](DECISION.md#d-p1-03)
- **Files:** `apps/api/routers/collections.py`, `apps/api/routers/documents.py`, `apps/api/services/storage.py`, `apps/worker/tasks/ingest.py`, `tests/test_upload.py`
- **Steps:**
  - [ ] Implement `GET/POST /collections` and `POST /collections/{id}/documents`; accept PDF/PNG/JPG multipart files under configurable size cap and return document ID.
  - [ ] Validate extension and actual file signature, sanitize filenames, store original files outside executable/web-public paths, and compute streaming SHA-256.
  - [ ] Select and test collection-scoped duplicate reject-versus-link behavior before freezing response schema; keep same bytes in different collections independent.
  - [ ] Enforce confidential collection hosted-indexing denial before any chunk/question leaves the machine; document development-only identity.
- **Verify:** `pytest tests/test_upload.py`; cover unsupported/corrupt/oversized files, duplicate scope, unauthorized paths, and confidential denial with zero hosted calls.
- **Acceptance:** accepted formats and cap are enforced; duplicate choice D-P1-03 has implementation tests; confidential uploads cannot reach hosted indexing.
- **Proof (planned):** [`proof/P1/upload_tests.md`](proof/P1/upload_tests.md), [`proof/P1/duplicate_policy.md`](proof/P1/duplicate_policy.md), [`proof/P1/confidential_block.md`](proof/P1/confidential_block.md)

<a id="p1-t03"></a>
### P1-T03 — Render pages and persist exact geometry

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.1 FR-ING-2, §8, §14 P1 | **Depends:** P1-T02
- **Decisions:** [D-F04](DECISION.md#d-f04)
- **Files:** `apps/worker/tasks/render.py`, `apps/parse_service/render.py`, `tests/test_render.py`
- **Steps:**
  - [ ] Render every PDF page to RGB using PyMuPDF at **150 dpi**; normalize PNG/JPG input into the same page-processing model.
  - [ ] If render exceeds **1664 × 2048**, downscale to fit while preserving aspect ratio; do not unnecessarily downscale A4/Letter at 150 dpi.
  - [ ] Persist actual `render_dpi`, `render_w`, `render_h`, `scale_to_pdf`, source page dimensions, and rendered artifact reference.
  - [ ] Test portrait, landscape, large-format, rotated, empty, scanned, and image inputs, including pixel geometry before/after downscale.
- **Verify:** `pytest tests/test_render.py`; independently assert dimensions, RGB mode, aspect ratio, and PDF scale for fixture pages.
- **Acceptance:** renderer always emits bounded RGB pages with reproducible actual dimensions and correct downscale metadata; failures identify their page.
- **Proof (planned):** [`proof/P1/render_geometry.md`](proof/P1/render_geometry.md), [`proof/P1/render_fixtures/`](proof/P1/render_fixtures/)

<a id="p1-t04"></a>
### P1-T04 — Implement exact parse client and coordinate postprocessing

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.1 FR-ING-3–5, §8, §16 risk 4 | **Depends:** P1-T03, P0-T03
- **Decisions:** [D-F04](DECISION.md#d-f04), [D-P1-01](DECISION.md#d-p1-01)
- **Files:** `apps/worker/tasks/parse.py`, `apps/parse_service/client.py`, `apps/parse_service/postprocess.py`, `tests/test_parse_postprocess.py`, `tests/test_bbox.py`
- **Steps:**
  - [ ] Send exact prompt `</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>` and `max_new_tokens=8744` with temperature 0, `top_k=1`, `repetition_penalty=1.1`, `skip_special_tokens=false`.
  - [ ] Persist unmodified raw output including control tokens; run `postprocess_document` with actual render size to obtain markdown/blocks.
  - [ ] Store class, normalized bbox, `bbox_px`, `bbox_pdf`, text, HTML, order, and parse status; preserve raw normalized and pixel values.
  - [ ] Convert pixel coordinates using `pixels * 72 / render_dpi`, adjusted for downscale; test round trips, rotations, clipping, degenerate boxes, and page boundaries.
- **Verify:** `pytest tests/test_parse_postprocess.py tests/test_bbox.py` using recorded raw outputs; compare hand-calculated PDF-point boxes.
- **Acceptance:** raw outputs remain lossless; every persisted block has valid provenance and both coordinate forms; bbox tests agree with independent calculations.
- **Proof (planned):** [`proof/P1/coordinate_validation.md`](proof/P1/coordinate_validation.md), [`proof/P1/bbox_tests.log`](proof/P1/bbox_tests.log)

<a id="p1-t05"></a>
### P1-T05 — Make Celery ingestion idempotent, resumable, and failure-safe

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5, §7.1 FR-ING-6, §12 Reliability | **Depends:** P1-T04
- **Decisions:** [D-F02](DECISION.md#d-f02), [D-F10](DECISION.md#d-f10)
- **Files:** `apps/worker/celery_app.py`, `apps/worker/tasks/ingest.py`, `apps/worker/services/checkpoints.py`, `tests/test_ingestion_recovery.py`
- **Steps:**
  - [ ] Chain render → parse → postprocess → later chunk/embed stages using deterministic job/page keys and durable checkpoints.
  - [ ] Retry each failed page **twice**, then mark that page failed without failing the whole document; retain error category, attempts, and timing.
  - [ ] Resume from last good page after worker restart and skip/reconcile already committed work without duplicate pages/blocks or repeated side effects.
  - [ ] Detect parse-service outage and pause affected jobs rather than terminally failing them; prove recovery after service restart and poison-page isolation.
- **Verify:** integration test kills/restarts worker and parse service; assert two retries, partial document continuation, no duplicates, and resumed completion.
- **Acceptance:** restart and outage tests pass; a failed page remains visible without discarding good pages; idempotent reruns preserve provenance.
- **Proof (planned):** [`proof/P1/retry_failure.md`](proof/P1/retry_failure.md), [`proof/P1/restart_recovery.log`](proof/P1/restart_recovery.log)

<a id="p1-t06"></a>
### P1-T06 — Expose document progress and ingestion traces

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.1 FR-ING-7, §8–9, §12 Observability | **Depends:** P1-T05
- **Decisions:** [D-F09](DECISION.md#d-f09), [D-F10](DECISION.md#d-f10)
- **Files:** `apps/api/routers/documents.py`, `apps/api/schemas/documents.py`, `apps/worker/observability.py`, `tests/test_document_status.py`
- **Steps:**
  - [ ] Implement `GET /documents/{id}` with queued, rendering, parsing, chunking, embedding, indexed, or failed state and processed/total/failed page counts.
  - [ ] Return page-level state/errors and timestamps needed to diagnose partial failures without leaking stack traces or secrets.
  - [ ] Propagate one ingestion trace ID through API, Celery, parser, and structured logs; record stage latency and call counts.
  - [ ] Test every state, zero-page/invalid documents, in-flight updates, page failure with document continuation, and terminal completion.
- **Verify:** API integration tests follow a document through all legal states; logs correlate by trace ID and contain no credential/raw confidential text.
- **Acceptance:** all seven required document states and page counts are observable; partial failures and trace timings reconcile with persisted pages.
- **Proof (planned):** [`proof/P1/status_transitions.md`](proof/P1/status_transitions.md), [`proof/P1/ingestion_trace.json`](proof/P1/ingestion_trace.json)

<a id="p1-t07"></a>
### P1-T07 — Review ten overlays and inventory observed parser classes

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.1 FR-ING-4, §7.2 FR-CHK-1–2, §14 P1, §16 risk 4 | **Depends:** P1-T04
- **Decisions:** [D-F05](DECISION.md#d-f05), [D-P1-01](DECISION.md#d-p1-01)
- **Files:** `apps/parse_service/overlay.py`, `packages/eval/review_parse.py`, `config/parser_classes.yaml`, `proof/P1/reviewed_pages/`
- **Steps:**
  - [ ] Build an overlay CLI that draws stored PDF/pixel boxes and labels on rendered pages from persisted block JSON.
  - [ ] Select ten varied pages covering digital, scanned, tables, charts, columns, headers/footers, and multilingual text where available.
  - [ ] Manually compare extracted text and bboxes to sources; record corrections/issues without silently editing raw parser output.
  - [ ] Record only observed semantic class names and map each to chunk behavior, including headers/footers/page numbers retained in blocks but excluded from index.
- **Verify:** rerun overlay generation from stored blocks; reviewer signs each page as pass/fail and all observed classes have an explicit mapping.
- **Acceptance:** ten overlays plus parse JSON and review notes exist; parsed text/regions pass manual gate or block release; D-P1-01 is evidence-ready.
- **Proof (planned):** [`proof/P1/overlay_review.md`](proof/P1/overlay_review.md), [`proof/P1/reviewed_pages/`](proof/P1/reviewed_pages/), [`proof/P1/parser_classes.md`](proof/P1/parser_classes.md)

<a id="p1-t08"></a>
### P1-T08 — Benchmark concurrency and select parse operating mode

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §6, §7.1 FR-ING-8, §14 P1, §16 risk 4 | **Depends:** P1-T05, P1-T07
- **Decisions:** [D-F04](DECISION.md#d-f04), [D-P1-02](DECISION.md#d-p1-02)
- **Files:** `packages/eval/benchmark_parse.py`, `config/parser.yaml`, `apps/parse_service/start.sh`
- **Steps:**
  - [ ] Start at parse concurrency **4**, then benchmark **1, 2, 4, and 8** on the same representative corpus with warm-up and documented repetitions.
  - [ ] Capture per-page/document latency, throughput, failures/retries, peak/allocated VRAM, GPU utilization, and queueing behavior.
  - [ ] Compare double-pass quality with single-pass; test `guarded` merge when duplicate table hypotheses pollute the index and record single-pass fast-fallback criteria.
  - [ ] Choose production concurrency and parse/merge mode from quality, throughput, and 12 GB VRAM evidence; resolve D-P1-02 and pin configuration.
- **Verify:** rerun benchmark command from committed config; report includes raw runs, environment identity, variance, failures, and quality comparison.
- **Acceptance:** all four concurrency levels and parse modes are compared; selected values are reproducible and justified, not automatically 4 or 8.
- **Proof (planned):** [`proof/P1/concurrency_vram.md`](proof/P1/concurrency_vram.md), [`proof/P1/parse_mode_comparison.md`](proof/P1/parse_mode_comparison.md), [`proof/P1/benchmark_results.csv`](proof/P1/benchmark_results.csv)

### P1 gate checklist

- [ ] Ten varied overlays and corresponding parse JSON exist; text and bboxes pass documented manual review.
- [ ] Timing/VRAM results exist at concurrency 1, 2, 4, and 8, with selected setting and reason.
- [ ] Failed pages were retried twice and reported; worker restart and parse outage recovery are demonstrated.
- [ ] Observed parser class inventory/mapping and duplicate policy are approved; D-P1-01 through D-P1-03 are resolved.
- [ ] All proof is committed before P2 begins.

## P2 — Chunking and indexing

**Entry:** P1 gate passed. **Exit:** three indexed documents satisfy limits, provenance, quota, and zero-call reingestion checks.

<a id="p2-t01"></a>
### P2-T01 — Build class-aware block text chunker

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.2 FR-CHK-1–3/8, §8 | **Depends:** P1 gate
- **Decisions:** [D-F05](DECISION.md#d-f05), [D-P1-01](DECISION.md#d-p1-01)
- **Files:** `packages/chunking/block_chunker.py`, `packages/chunking/models.py`, `tests/test_chunker.py`
- **Steps:**
  - [ ] Consume ordered parsed blocks—not raw document text—and apply observed P1 class mappings deterministically.
  - [ ] Target **400–800 tokens** per text chunk with about **12% overlap**, splitting on block and paragraph boundaries.
  - [ ] Never cut inside a block unless that block alone exceeds the maximum; route such blocks through P2-T04 safe splitting.
  - [ ] Exclude headers, footers, and page numbers from indexable chunks while retaining their block rows and source provenance.
- **Verify:** `pytest tests/test_chunker.py`; cover short/long text, overlap reconstruction, paragraph/block boundaries, excluded classes, and oversized blocks.
- **Acceptance:** chunking is deterministic; overlap is measured; every chunk maps to ordered source blocks/pages/bboxes and no prohibited intra-block split occurs.
- **Proof (planned):** [`proof/P2/chunker_tests.md`](proof/P2/chunker_tests.md), [`proof/P2/text_chunk_examples.jsonl`](proof/P2/text_chunk_examples.jsonl)

<a id="p2-t02"></a>
### P2-T02 — Handle tables and charts without losing display or provenance

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.2 FR-CHK-4–5/8, §16 risk 4 | **Depends:** P2-T01
- **Decisions:** [D-F05](DECISION.md#d-f05), [D-P1-01](DECISION.md#d-p1-01)
- **Files:** `packages/chunking/tables.py`, `packages/chunking/charts.py`, `tests/test_table_chunks.py`, `tests/test_chart_chunks.py`
- **Steps:**
  - [ ] Keep each table as one chunk; above **1,200 tokens**, split only by rows and repeat the header row in every part.
  - [ ] Preserve sanitized-render-ready table HTML for display and produce flattened row-wise text for embedding and lexical search.
  - [ ] Turn each chart block into one chunk from extracted data and caption, retaining meaningful labels/values when present.
  - [ ] Maintain table/chart source-block order, page ranges, bboxes, continuation metadata, and row/header integrity across splits.
- **Verify:** fixture tests cover threshold boundaries, wide/long tables, repeated headers, malformed HTML, empty charts, and multilingual cells.
- **Acceptance:** no non-row table split occurs; all parts repeat headers; stored HTML and flattened text agree; every part remains drawable on source pages.
- **Proof (planned):** [`proof/P2/table_chart_tests.md`](proof/P2/table_chart_tests.md), [`proof/P2/table_examples/`](proof/P2/table_examples/)

<a id="p2-t03"></a>
### P2-T03 — Add section paths and cross-page continuation links

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.2 FR-CHK-6–7, §8 | **Depends:** P2-T01, P2-T02
- **Decisions:** [D-F05](DECISION.md#d-f05)
- **Files:** `packages/chunking/sections.py`, `packages/chunking/continuations.py`, `tests/test_continuations.py`
- **Steps:**
  - [ ] Derive section paths from observed heading structure, e.g. `Report > 3 Risks > 3.2 Credit`, with a fallback for missing headings.
  - [ ] Prepend section path only to `embed_text`; leave displayed `text`, raw blocks, and quotes unchanged.
  - [ ] Implement conservative heuristics for paragraphs/tables continuing across page breaks; set `continues_from` only when supported by layout/text evidence.
  - [ ] Build positive/negative fixtures for repeated headers, page-number interruptions, columns, new headings, and table boundaries; evaluate false links/misses.
- **Verify:** unit tests prove display text is unchanged and continuation graph is directed, local, acyclic, and never crosses documents.
- **Acceptance:** section prefixes are embedding-only; continuation precision/recall on labeled fixtures is reported and bad links have actionable diagnostics.
- **Proof (planned):** [`proof/P2/continuation_eval.md`](proof/P2/continuation_eval.md), [`proof/P2/section_path_examples.jsonl`](proof/P2/section_path_examples.jsonl)

<a id="p2-t04"></a>
### P2-T04 — Enforce tokenizer counts and measured embed limits

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.2 FR-CHK-3/9, §17 | **Depends:** P2-T01, P0-T05
- **Decisions:** [D-F05](DECISION.md#d-f05), [D-P0-04](DECISION.md#d-p0-04)
- **Files:** `packages/chunking/tokenizer.py`, `packages/chunking/limits.py`, `config/chunking.yaml`, `tests/test_token_limits.py`
- **Steps:**
  - [ ] Use embedding model tokenizer when available; otherwise implement and version the documented proxy with calibration against real responses.
  - [ ] Count the actual embedding input including section path and required query/passage markers, not display text alone.
  - [ ] Set chunk maximum below measured embed input limit with documented headroom and enforce endpoint batch constraints separately.
  - [ ] Split only an individually oversized block at safe text/row boundaries while retaining ordered source-block/bbox mappings; report unavoidable failures.
- **Verify:** property tests cover exact boundary, multibyte Hindi/Marathi, section prefixes, oversized blocks/tables, and tokenizer/proxy discrepancies.
- **Acceptance:** every emitted chunk and batch passes measured input constraints; counting method/config version is stored and no unknown maximum is assumed.
- **Proof (planned):** [`proof/P2/token_limit_report.md`](proof/P2/token_limit_report.md), [`proof/P2/tokenizer_calibration.csv`](proof/P2/tokenizer_calibration.csv)

<a id="p2-t05"></a>
### P2-T05 — Complete resilient NIM gateway controls

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5–6, §11, §12 Secrets | **Depends:** P0-T06, P0-T08
- **Decisions:** [D-F03](DECISION.md#d-f03), [D-F10](DECISION.md#d-f10), [D-P0-06](DECISION.md#d-p0-06)
- **Files:** `apps/api/nim_gateway/`, `tests/test_nim_resilience.py`, `tests/fixtures/nim/`
- **Steps:**
  - [ ] Centralize all hosted embed/rerank/rewrite/answer/verify calls; enforce per-model measured token buckets and largest safe embedding batches.
  - [ ] Apply bounded exponential backoff with jitter on 429/5xx, timeout handling, per-model circuit breakers, and concurrency limits.
  - [ ] Implement deterministic caches keyed by model/request content and automatic PRD fallback routes with reason/latency audit fields.
  - [ ] Redact API keys and sensitive payloads from logs/errors; make ordinary tests replay success, malformed, throttled, unavailable, and fallback fixtures offline.
- **Verify:** `pytest tests/test_nim_resilience.py` under blocked network; assert no retry storms, cross-model limiter leakage, credential leakage, or silent fallback.
- **Acceptance:** gateway is sole hosted-call path; measured limits are enforced; cache/fallback/circuit transitions are audited and fixture tests consume zero quota.
- **Proof (planned):** [`proof/P2/gateway_resilience.md`](proof/P2/gateway_resilience.md), [`proof/P2/offline_gateway_tests.log`](proof/P2/offline_gateway_tests.log)

<a id="p2-t06"></a>
### P2-T06 — Implement cached embeddings and chunk provenance persistence

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.3 FR-IDX-1/4, §8, §11, §14 P2 | **Depends:** P2-T04, P2-T05
- **Decisions:** [D-F05](DECISION.md#d-f05), [D-F09](DECISION.md#d-f09), [D-P0-03](DECISION.md#d-p0-03), [D-P0-04](DECISION.md#d-p0-04)
- **Files:** `apps/worker/tasks/embed.py`, `apps/api/migrations/`, `apps/api/repositories/chunks.py`, `tests/test_embedding_cache.py`
- **Steps:**
  - [ ] Migrate `chunks`, `chunk_blocks`, and `embed_cache` with all PRD columns, ordered many-to-many provenance, model identity, vector dimension/reference, and indexes.
  - [ ] Embed `embed_text` in gateway batches; read vector size from first real response, assert every later vector matches, and never configure a guessed dimension.
  - [ ] Cache by normalized text hash **and model**, handling collisions/vector-store transaction failures without returning a different model's vector.
  - [ ] Make chunk/vector/cache writes idempotent and auditable; verify identical reingestion uses cached vectors and makes **zero embedding API calls**.
- **Verify:** integration tests count gateway calls on first and identical second ingestion; test model changes, empty text, dimension mismatch, and partial failure.
- **Acceptance:** all chunks/provenance/cache rows are complete; dimension comes from response; identical reingestion spends zero embedding calls and produces no duplicates.
- **Proof (planned):** [`proof/P2/reingestion_zero_calls.md`](proof/P2/reingestion_zero_calls.md), [`proof/P2/embedding_call_ledger.csv`](proof/P2/embedding_call_ledger.csv)

<a id="p2-t07"></a>
### P2-T07 — Index dense vectors and PostgreSQL lexical search

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5, §7.3 FR-IDX-1–4, §8 | **Depends:** P2-T06, P0-T08
- **Decisions:** [D-F02](DECISION.md#d-f02), [D-F05](DECISION.md#d-f05), [D-P0-03](DECISION.md#d-p0-03)
- **Files:** `apps/api/repositories/vector_store.py`, `apps/api/repositories/lexical.py`, `apps/api/migrations/`, `tests/test_index_stores.py`
- **Steps:**
  - [ ] Implement selected Qdrant store or evidence-approved pgvector simplification behind one interface; preserve collection/document ownership scope.
  - [ ] Store payload `chunk_id`, `doc_id`, `collection_id`, `page_start`, `page_end`, `section_path`, `chunk_type`, `lang`, and validate filter indexes.
  - [ ] Maintain PostgreSQL `tsvector` over chunk text using **`simple`** configuration so Hindi and Marathi tokens are not dropped.
  - [ ] Test PostgreSQL/vector consistency, deletes/retries, scoped filters, dimension mismatch, English/Hindi/Marathi lexical tokens, and failure reconciliation.
- **Verify:** store integration tests assert required payload/fields and language fixtures; audit orphaned/missing vectors and mismatched chunk rows.
- **Acceptance:** both indexes return only authorized scoped chunks; lexical search works on multilingual fixtures; selected vector store matches resolved D-P0-03.
- **Proof (planned):** [`proof/P2/index_contract.md`](proof/P2/index_contract.md), [`proof/P2/multilingual_lexical_tests.md`](proof/P2/multilingual_lexical_tests.md)

<a id="p2-t08"></a>
### P2-T08 — Produce three-document indexing and provenance audit

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.2–7.3, §11, §14 P2 | **Depends:** P2-T02, P2-T03, P2-T04, P2-T06, P2-T07
- **Decisions:** [D-F05](DECISION.md#d-f05), [D-F10](DECISION.md#d-f10), [D-P0-06](DECISION.md#d-p0-06)
- **Files:** `packages/eval/audit_index.py`, `packages/eval/report_quota.py`, `proof/P2/documents/`
- **Steps:**
  - [ ] Index three representative documents including tables and multilingual content; save complete chunk dumps with source mappings and config/model identities.
  - [ ] Generate token-count histogram, limit-headroom report, and a list of **10 table chunks** with stored HTML and flattened text.
  - [ ] Audit every chunk to source blocks, pages, bboxes, vector payload, lexical row, and cache identity; detect missing/orphaned/cross-document links.
  - [ ] Reconcile quota ledger to gateway counts, rerun identical ingestion, and document any corpus reductions or quality limitations.
- **Verify:** run committed audit CLI; it fails on over-limit chunks, unmapped provenance, duplicate rows/vectors, or nonzero calls on identical reingestion.
- **Acceptance:** all three dumps and required reports exist; no chunk exceeds embed limit; every chunk maps to blocks/bboxes; zero-call proof is reproducible.
- **Proof (planned):** [`proof/P2/chunk_dump.jsonl`](proof/P2/chunk_dump.jsonl), [`proof/P2/token_histogram.md`](proof/P2/token_histogram.md), [`proof/P2/table_chunks.md`](proof/P2/table_chunks.md), [`proof/P2/quota_usage.md`](proof/P2/quota_usage.md), [`proof/P2/provenance_audit.md`](proof/P2/provenance_audit.md)

### P2 gate checklist

- [ ] Chunk dumps for three documents, token histogram, ten table chunks with HTML, and quota report are committed.
- [ ] No chunk exceeds measured embed limit; tokenizer/proxy and section-prefix counting are documented.
- [ ] Every chunk maps back to ordered source blocks, pages, and bboxes; continuation links pass fixture evaluation.
- [ ] Identical file reingestion spends zero embedding calls; dense and `simple` lexical stores pass scoped multilingual tests.
- [ ] P2 proof and acceptance checks pass before P3 begins.

## P3 — Retrieval

**Entry:** P2 gate passed. **Exit:** draft retrieval metrics and ablations meet gate or have approved diagnosis/fix plan.

<a id="p3-t01"></a>
### P3-T01 — Persist conversations and conditionally rewrite queries

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §6, §7.4 FR-RET-1, §8–9 | **Depends:** P2 gate
- **Decisions:** [D-F03](DECISION.md#d-f03), [D-F06](DECISION.md#d-f06), [D-F09](DECISION.md#d-f09)
- **Files:** `apps/api/routers/conversations.py`, `apps/api/services/rewrite.py`, `apps/api/migrations/`, `config/prompts/rewrite.txt`, `tests/test_rewrite.py`
- **Steps:**
  - [ ] Migrate `conversations` and `messages` with every PRD key column, collection ownership, original question, rewritten query, answer/verifier/trace JSON, and timestamps.
  - [ ] Implement `GET /conversations/{id}/messages` and conversation creation/loading with development-only identity boundaries.
  - [ ] Rewrite with Lightning at low temperature/short output only when prior turns exist or query is under-specified; use last few turns without changing collection/doc scope.
  - [ ] Retain original question for display/audit, version prompt/config, and safely fall back to original when rewrite is unnecessary, unavailable, or invalid.
- **Verify:** recorded fixtures cover first turn, pronoun follow-up, under-specified query, multilingual query, malicious history, and unavailable rewrite; assert call condition.
- **Acceptance:** original and standalone queries are persisted correctly; unnecessary rewrite calls are zero; history cannot broaden selected document scope.
- **Proof (planned):** [`proof/P3/rewrite_cases.md`](proof/P3/rewrite_cases.md), [`proof/P3/conversation_api_tests.log`](proof/P3/conversation_api_tests.log)

<a id="p3-t02"></a>
### P3-T02 — Implement scoped dense and lexical top-40 retrieval

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.4 FR-RET-2, §7.3, §8 | **Depends:** P3-T01, P2-T07
- **Decisions:** [D-F06](DECISION.md#d-f06), [D-P0-03](DECISION.md#d-p0-03), [D-P0-04](DECISION.md#d-p0-04)
- **Files:** `apps/api/services/retrieval/dense.py`, `apps/api/services/retrieval/lexical.py`, `apps/api/services/retrieval/service.py`, `tests/test_retrieval_scope.py`
- **Steps:**
  - [ ] Embed standalone query using measured query-input flags and gateway; retrieve dense **top 40** with collection and optional document filters.
  - [ ] Retrieve PostgreSQL `simple` full-text lexical **top 40** with identical collection/doc restrictions and deterministic tie-breaking.
  - [ ] Normalize result contracts with chunk ID, source rank/score, document/page/section metadata, and trace fields without mixing incomparable raw scores.
  - [ ] Test empty indexes, fewer than 40 results, ties, deleted/failed documents, multilingual terms, cross-collection isolation, and optional `doc_ids` subsets.
- **Verify:** integration tests seed known chunks and assert exact top-k/filter behavior; no result outside selected collection/documents is permitted.
- **Acceptance:** dense and lexical each return at most 40 eligible candidates with stable ranks and complete provenance; query embedding flows only through gateway.
- **Proof (planned):** [`proof/P3/retrieval_scope_tests.md`](proof/P3/retrieval_scope_tests.md), [`proof/P3/candidate_examples.json`](proof/P3/candidate_examples.json)

<a id="p3-t03"></a>
### P3-T03 — Fuse with RRF 60 and rerank 30 candidates to 8

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §6, §7.4 FR-RET-3–4, §8, §15 | **Depends:** P3-T02, P0-T05
- **Decisions:** [D-F06](DECISION.md#d-f06), [D-P0-05](DECISION.md#d-p0-05)
- **Files:** `apps/api/services/retrieval/rrf.py`, `apps/api/services/retrieval/rerank.py`, `tests/test_rrf.py`, `tests/test_rerank.py`
- **Steps:**
  - [ ] Merge dense/lexical ranks using Reciprocal Rank Fusion constant **k=60**, with deterministic handling of shared chunks and ties.
  - [ ] Send top **30** merged candidates through measured rerank route and keep top **8**, respecting capacity/fallback behavior from P0.
  - [ ] Persist dense/lexical ranks and scores, RRF score, rerank input/output rank and score, model IDs, and latency in query trace.
  - [ ] Hand-calculate RRF fixtures including overlap/disjoint lists/ties; test rerank duplicates, missing candidates, invalid responses, and service failure.
- **Verify:** `pytest tests/test_rrf.py tests/test_rerank.py`; independent expected scores/ranks match exactly and all eight final IDs trace to merged candidates.
- **Acceptance:** RRF 60 and actual 30 → 8 path are verified; score semantics are not invented; traces reproduce every ranking stage.
- **Proof (planned):** [`proof/P3/rrf_hand_calculation.md`](proof/P3/rrf_hand_calculation.md), [`proof/P3/rerank_trace.json`](proof/P3/rerank_trace.json)

<a id="p3-t04"></a>
### P3-T04 — Assemble labeled C1–C8 context under token budget

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.4 FR-RET-6, §7.2 FR-CHK-7, §10 | **Depends:** P3-T03
- **Decisions:** [D-F05](DECISION.md#d-f05), [D-F06](DECISION.md#d-f06)
- **Files:** `apps/api/services/context.py`, `config/retrieval.yaml`, `tests/test_context_assembly.py`
- **Steps:**
  - [ ] Label final ranked chunks **C1 through C8** consistently across prompt, trace, citations, and persisted answer.
  - [ ] Add neighbor chunks only through explicit `continues_from` links; do not infer adjacency from page/chunk numbers.
  - [ ] Enforce configurable context token budget with deterministic inclusion/truncation policy that never silently drops a cited source or cuts table rows arbitrarily.
  - [ ] Include source document/page/section metadata and displayed text without confusing model-only labels with database IDs.
- **Verify:** fixtures cover eight chunks, continuation chains/cycles, budget boundaries, duplicate neighbors, missing links, and multilingual token counts.
- **Acceptance:** context never exceeds configured budget; only linked neighbors are added; labels are unique/stable and all included text is source-faithful.
- **Proof (planned):** [`proof/P3/context_contract.md`](proof/P3/context_contract.md), [`proof/P3/context_examples.json`](proof/P3/context_examples.json)

<a id="p3-t05"></a>
### P3-T05 — Implement abstention gate without guessing threshold

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.4 FR-RET-5, §4 Refusal accuracy, §17 | **Depends:** P3-T03
- **Decisions:** [D-F06](DECISION.md#d-f06), [D-P5-01](DECISION.md#d-p5-01)
- **Files:** `apps/api/services/abstention.py`, `config/retrieval.yaml`, `tests/test_abstention.py`
- **Steps:**
  - [ ] Implement comparison of top rerank score against a configured threshold; below threshold skips generation and returns a clear refusal with reason.
  - [ ] Leave production threshold explicitly unset pending P5 labeled calibration; allow synthetic fixture thresholds only in tests, never present them as calibrated values.
  - [ ] Define safe behavior for missing/invalid rerank scores and ensure an abstention decision is persisted with score, threshold version, and outcome.
  - [ ] Generate calibration-ready traces with answerability labels joined later; do not infer a universal threshold from P0 score-range probes.
- **Verify:** synthetic fixtures exercise just below/equal/above, empty candidates, NaN/missing score, and disabled-unset pre-calibration behavior; zero generation calls below gate.
- **Acceptance:** gate mechanics and refusal path are correct; no guessed production threshold is enabled; D-P5-01 remains open with required labeled evidence.
- **Proof (planned):** [`proof/P3/abstention_fixtures.md`](proof/P3/abstention_fixtures.md), [`proof/P3/abstention_config_audit.md`](proof/P3/abstention_config_audit.md)

<a id="p3-t06"></a>
### P3-T06 — Create versioned draft retrieval gold set

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §13 Gold set, §14 P3, §16 risk 7 | **Depends:** P2-T08
- **Decisions:** [D-F11](DECISION.md#d-f11)
- **Files:** `packages/eval/gold/draft_v1.jsonl`, `packages/eval/gold/schema.json`, `packages/eval/gold/README.md`
- **Steps:**
  - [ ] Write draft questions from owner's documents with expected answer, expected source page, expected source block, and chunk/page answerability labels.
  - [ ] Include factoid, table, multi-passage, cross-document, unanswerable, and English/Hindi/Marathi examples with stable IDs and collection/document scope.
  - [ ] Validate labels against stored block provenance; have a second review pass for ambiguous/multiple valid sources.
  - [ ] Version dataset/config and document size, category/language distribution, known composition gaps, and why it is not yet the final 60–100 set.
- **Verify:** schema/provenance validator passes; every labeled source resolves to existing document/page/block and no answer is copied without review.
- **Acceptance:** draft supports reproducible Recall/MRR; gaps and target composition are explicit; P5 expansion requirements remain unclaimed.
- **Proof (planned):** [`proof/P3/gold_set_draft.md`](proof/P3/gold_set_draft.md), [`packages/eval/gold/draft_v1.jsonl`](packages/eval/gold/draft_v1.jsonl)

<a id="p3-t07"></a>
### P3-T07 — Build LLM-free retrieval metrics and trace harness

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §4 Recall@8/MRR, §8 `trace_json`/`eval_runs`, §13 Metrics/Method | **Depends:** P3-T03, P3-T06
- **Decisions:** [D-F10](DECISION.md#d-f10), [D-F11](DECISION.md#d-f11)
- **Files:** `packages/eval/retrieval_metrics.py`, `packages/eval/run_retrieval.py`, `apps/api/migrations/`, `tests/test_retrieval_metrics.py`
- **Steps:**
  - [ ] Compute chunk- and page-level Recall@k and MRR from stored candidate/rerank traces without answer/judge LLM calls.
  - [ ] Handle multiple valid sources, unanswerable items, ties, missing final eight, and zero denominators with documented formulas.
  - [ ] Record dataset/config versions, config hash, git SHA, model IDs, per-stage latency/call counts, and per-question diagnostics; create `eval_runs` schema with PRD fields.
  - [ ] Validate metrics against hand-worked examples and export slice results by category/language/document for error analysis.
- **Verify:** `pytest tests/test_retrieval_metrics.py`; replaying same traces produces byte-stable metric output and no hosted model calls.
- **Acceptance:** Recall@8 and first-gold reciprocal rank match independent calculations; traces and eval rows fully identify code/config/data used.
- **Proof (planned):** [`proof/P3/metric_validation.md`](proof/P3/metric_validation.md), [`proof/P3/eval_trace_example.json`](proof/P3/eval_trace_example.json)

<a id="p3-t08"></a>
### P3-T08 — Run retrieval baseline, ablations, and error diagnosis

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §4, §13 Ablations, §14 P3, §16 risk 7 | **Depends:** P3-T04, P3-T05, P3-T07
- **Decisions:** [D-F06](DECISION.md#d-f06), [D-F11](DECISION.md#d-f11), [D-P5-01](DECISION.md#d-p5-01)
- **Files:** `packages/eval/ablate_retrieval.py`, `packages/eval/error_analysis.py`, `proof/P3/results/`
- **Steps:**
  - [ ] Run baseline hybrid + RRF + rerank on frozen draft set using explicit live/embed/rerank quota procedure or recorded complete traces.
  - [ ] Run no-hybrid and no-rerank ablations with otherwise identical data/config; save per-query rankings and aggregate/slice metrics.
  - [ ] Report chunk/page Recall@8 and MRR with stage latency, failures, and English/Hindi/Marathi slices; preserve final targets Recall@8 ≥0.90 and MRR ≥0.75.
  - [ ] If draft Recall@8 <0.85, write evidence-backed diagnosis and fix plan instead of lowering target; inspect retrieval vs parsing/chunking/rerank causes.
- **Verify:** rerun harness from committed traces/config; compare baseline/ablation outputs and ensure eval rows identify every run.
- **Acceptance:** draft Recall@8 ≥0.85 **or** approved diagnosis/fix plan exists; both required ablations and error categories are reported with no hidden omissions.
- **Proof (planned):** [`proof/P3/retrieval_metrics.md`](proof/P3/retrieval_metrics.md), [`proof/P3/retrieval_ablations.md`](proof/P3/retrieval_ablations.md), [`proof/P3/error_analysis.md`](proof/P3/error_analysis.md)

### P3 gate checklist

- [ ] Draft gold set with expected answers/pages/blocks and documented composition gaps is versioned.
- [ ] Retrieval report and no-hybrid/no-rerank ablation table are committed with config hash/git SHA.
- [ ] Draft Recall@8 ≥0.85 or written diagnosis/fix plan is approved; final ≥0.90 target remains unchanged.
- [ ] Production abstention threshold remains unset pending P5; context/retrieval traces pass offline metric tests.
- [ ] P3 proof is committed before P4 begins.

## P4 — Generation and verification

**Entry:** P3 gate passed. **Exit:** 30 verified answer records, removal audit, five refusals, and measured draft quality satisfy gate.

<a id="p4-t01"></a>
### P4-T01 — Implement versioned grounded answer prompt and schema

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §6 Answer settings, §7.5 FR-GEN-1/3, §10 | **Depends:** P3 gate
- **Decisions:** [D-F03](DECISION.md#d-f03), [D-F07](DECISION.md#d-f07)
- **Files:** `config/prompts/answer_v1.txt`, `config/prompts/answer_strict_v1.txt`, `apps/api/schemas/answer.py`, `apps/api/services/answer.py`, `tests/test_answer_schema.py`
- **Steps:**
  - [ ] Use hosted `nemotron-3.5-super-vl-120b-a12b` with reasoning off and temperature at/near 0 as supported; instruct answers only from labeled C1–C8 context and abstain on insufficiency.
  - [ ] Require every factual sentence to be a `claim` with at least one provided chunk ID and verbatim quote ≤25 words; `connective` sentences contain no facts, IDs, or quote.
  - [ ] Enforce exact answer JSON shape below; summary is not independently generated from unsupported prose and is composed only from verified surviving claims.
  - [ ] Version prompt/model/config and record fallback to `llama-3.3-nemotron-super-49b-v1.5` with an eval run on any model/prompt change.

```json
{
  "abstain": false,
  "abstain_reason": null,
  "summary": "string",
  "paragraphs": [[
    {"text":"one sentence","type":"claim","chunk_ids":["C3"],"quote":"verbatim text from C3, 25 words or fewer"},
    {"text":"transition sentence","type":"connective","chunk_ids":[],"quote":null}
  ]]
}
```

- **Verify:** schema tests reject missing/extra claim evidence, factual connectives, >25-word quotes, unknown types, malformed paragraphs, and unsupported abstention combinations.
- **Acceptance:** prompt and parser enforce grounded-only output and exact schema; every factual sentence carries evidence; config identity is traceable.
- **Proof (planned):** [`proof/P4/answer_prompt_contract.md`](proof/P4/answer_prompt_contract.md), [`proof/P4/answer_schema_tests.log`](proof/P4/answer_schema_tests.log)

<a id="p4-t02"></a>
### P4-T02 — Parse JSON with exactly one repair attempt

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.5 FR-GEN-2, §15 | **Depends:** P4-T01
- **Decisions:** [D-F03](DECISION.md#d-f03), [D-F07](DECISION.md#d-f07)
- **Files:** `apps/api/services/json_repair.py`, `config/prompts/json_repair.txt`, `tests/test_json_repair.py`, `tests/fixtures/answers/`
- **Steps:**
  - [ ] Parse answer JSON strictly and classify syntax vs schema/context validation errors without executing model-provided content.
  - [ ] On invalid JSON, issue **exactly one** bounded automatic repair request that supplies only the invalid output, schema, and allowed context as needed.
  - [ ] Re-run full structural, quote, and entailment checks after repair; a second invalid result becomes a visible failure state, never raw/unverified answer text.
  - [ ] Persist initial output, repair status/output, validation errors, model calls, and timings with redaction/retention appropriate to document privacy.
- **Verify:** fixture tests count calls for valid, repairable, twice-invalid, oversized, markdown-fenced, truncated, and prompt-injection outputs.
- **Acceptance:** no case exceeds one repair; repaired output receives all checks; terminal failure is explicit and contains no displayed failed answer.
- **Proof (planned):** [`proof/P4/json_repair_tests.md`](proof/P4/json_repair_tests.md), [`proof/P4/repair_failure_example.json`](proof/P4/repair_failure_example.json)

<a id="p4-t03"></a>
### P4-T03 — Verify structure, context IDs, and normalized quote matches

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.5 FR-GEN-3, §7.6 FR-VER-1–2, §15 | **Depends:** P4-T01
- **Decisions:** [D-F07](DECISION.md#d-f07), [D-F08](DECISION.md#d-f08), [D-P5-02](DECISION.md#d-p5-02)
- **Files:** `apps/api/verifier/structural.py`, `apps/api/verifier/quotes.py`, `config/verification.yaml`, `tests/test_quote_matcher.py`
- **Steps:**
  - [ ] Require valid JSON, valid claim/connective fields, and every cited chunk ID to be present in provided C1–C8 context; reject hallucinated IDs.
  - [ ] Enforce ≤25 words per quote and compare against the cited chunk text, never against a different chunk or generated answer.
  - [ ] Normalize both sides using Unicode **NFKC**, whitespace, and case; use fuzzy partial ratio at configured threshold, initial/default **92**, pending P5 calibration.
  - [ ] Mark failed quotes unsupported with reason; test Unicode compatibility, whitespace/case variants, transposed text, empty quotes, multilingual text, and threshold boundaries.
- **Verify:** `pytest tests/test_quote_matcher.py`; independently calculate normalized inputs/ratios on boundary fixtures and assert failed claims cannot pass downstream.
- **Acceptance:** structural/quote failures are deterministic and audited; threshold 92 is identified as provisional until D-P5-02 resolution; no failed quote is displayed as supported.
- **Proof (planned):** [`proof/P4/quote_matcher_tests.md`](proof/P4/quote_matcher_tests.md), [`proof/P4/quote_failures.jsonl`](proof/P4/quote_failures.jsonl)

<a id="p4-t04"></a>
### P4-T04 — Add batched Ultra entailment verification and audit output

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §6 Verify settings/fallbacks, §7.6 FR-VER-3/6, §10 | **Depends:** P4-T03, P0-T08
- **Decisions:** [D-F03](DECISION.md#d-f03), [D-F08](DECISION.md#d-f08)
- **Files:** `apps/api/verifier/entailment.py`, `apps/api/verifier/schemas.py`, `config/prompts/verify.txt`, `tests/test_entailment.py`
- **Steps:**
  - [ ] Send **all claims together in one batched Ultra call per answer**, with reasoning on and token budget only if endpoint supports it; quote-stage failures remain independently marked unsupported.
  - [ ] Require exact verifier JSON `results` array; each entry has `claim_index`, verdict `supported`, `partial`, or `unsupported`, and a one-line `reason`.
  - [ ] Validate complete one-to-one claim coverage and reject duplicate/out-of-range indices, missing reasons, unsupported verdicts, or mismatched answer context.
  - [ ] On verify slowness/rate limiting, use Lightning fallback with lower claim batch size as configured; persist raw/parsed verifier output, model, fallback, reasons, and latency.
- **Verify:** recorded fixtures cover all verdicts, omitted/duplicate claims, invalid JSON, timeout/fallback, and mixed quote failures; ordinary tests make zero live calls.
- **Acceptance:** normal path makes one entailment call per answer containing all claims; every claim has one validated verdict plus any independent quote-stage failure; verifier output is persisted for audit/evaluation.
- **Proof (planned):** [`proof/P4/entailment_contract.md`](proof/P4/entailment_contract.md), [`proof/P4/verifier_output_examples.json`](proof/P4/verifier_output_examples.json)

<a id="p4-t05"></a>
### P4-T05 — Apply removal, partial, refusal, and one-time regeneration policy

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.6 FR-VER-4, §10 summary rule, §4 Refusal accuracy | **Depends:** P4-T04
- **Decisions:** [D-F07](DECISION.md#d-f07), [D-F08](DECISION.md#d-f08)
- **Files:** `apps/api/verifier/policy.py`, `apps/api/services/regenerate.py`, `config/prompts/answer_strict_v1.txt`, `tests/test_verifier_policy.py`
- **Steps:**
  - [ ] Remove every unsupported claim from displayed paragraphs; retain `partial` claims with explicit visible badge state and preserve audit of removals.
  - [ ] If every factual claim is removed, return a clear refusal; do not leave a factual summary or unsupported connective-only explanation.
  - [ ] If **more than 30%** of factual claims were removed, regenerate **once** with stricter prompt and apply the same structural, quote, and entailment checks.
  - [ ] Compose summary only from claims surviving final verification; bound regeneration to one attempt and expose final failure/refusal honestly.
- **Verify:** table-driven tests cover exactly 30% vs >30%, zero/all removed, partial-only, regeneration success/failure, and second-attempt policy violations.
- **Acceptance:** displayed summary/details contain only surviving verified claims; no more than one regeneration occurs; all-removed and >30% branches match PRD exactly.
- **Proof (planned):** [`proof/P4/verification_policy_tests.md`](proof/P4/verification_policy_tests.md), [`proof/P4/regeneration_example.json`](proof/P4/regeneration_example.json)

<a id="p4-t06"></a>
### P4-T06 — Resolve surviving claims to page and block bboxes

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.6 FR-VER-5, §7.2 FR-CHK-8, §8–9 | **Depends:** P4-T05, P2-T06
- **Decisions:** [D-F05](DECISION.md#d-f05), [D-F08](DECISION.md#d-f08)
- **Files:** `apps/api/verifier/citations.py`, `apps/api/routers/documents.py`, `apps/api/schemas/citations.py`, `tests/test_citation_resolution.py`
- **Steps:**
  - [ ] For each surviving claim, search only blocks inside its cited chunk and select the block best matching the normalized quote.
  - [ ] Return document ID, page number, block ID/order, PDF bbox, source chunk, quote, and verdict; handle multiple citations per claim independently.
  - [ ] If no single block matches uniquely, return **all blocks of the chunk** rather than guessing a region; preserve multi-page table/continuation mappings.
  - [ ] Implement `GET /documents/{id}/pages/{n}/blocks` and original-file endpoint `GET /documents/{id}/file` with scope checks and correct content disposition.
- **Verify:** fixtures cover exact/partial/multiple/no block match, tables across pages, excluded blocks, malformed bboxes, and unauthorized document access.
- **Acceptance:** every displayed citation resolves to correct source page/bbox or all-chunk-blocks fallback; no block outside cited chunk is selected.
- **Proof (planned):** [`proof/P4/citation_resolution_tests.md`](proof/P4/citation_resolution_tests.md), [`proof/P4/citation_regions.json`](proof/P4/citation_regions.json)

<a id="p4-t07"></a>
### P4-T07 — Orchestrate POST /chat with SSE and complete traces

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.7 FR-UI-2, §8–9, §12 Observability | **Depends:** P4-T02, P4-T06, P3-T01, P3-T04, P3-T05
- **Decisions:** [D-F08](DECISION.md#d-f08), [D-F09](DECISION.md#d-f09), [D-F10](DECISION.md#d-f10)
- **Files:** `apps/api/routers/chat.py`, `apps/api/services/chat_orchestrator.py`, `apps/api/schemas/events.py`, `tests/test_chat_sse.py`
- **Steps:**
  - [ ] Implement `POST /chat` body `collection_id`, `conversation_id`, `question`, optional `doc_ids`; validate ownership/scope and confidential hosted-query rules.
  - [ ] Stream status events `rewriting`, `retrieving`, `reranking`, `answering`, `verifying`, then final `answer` event; stream refusal/failure states without answer text.
  - [ ] Never emit answer tokens or unverified claims; release only final verified summary/details/citations after all policies and citation resolution pass.
  - [ ] Persist messages, original/rewritten query, answer/verifier JSON, and `trace_json` with per-stage latency, call counts, model IDs, retrieved chunk IDs/scores, and trace ID.
- **Verify:** SSE integration tests assert event order, disconnect/retry behavior, malformed request, retrieval abstention, repair failure, verifier failure, and no premature answer event.
- **Acceptance:** answer event is last and verified; all required trace fields are durable; no token streaming or unverified failure answer reaches clients.
- **Proof (planned):** [`proof/P4/sse_event_contract.md`](proof/P4/sse_event_contract.md), [`proof/P4/chat_trace_example.json`](proof/P4/chat_trace_example.json)

<a id="p4-t08"></a>
### P4-T08 — Record answer/verifier corpus and measure draft quality

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §4, §13 Metrics, §14 P4, §16 risk 6 | **Depends:** P4-T07
- **Decisions:** [D-F08](DECISION.md#d-f08), [D-F11](DECISION.md#d-f11)
- **Files:** `packages/eval/run_answer_draft.py`, `packages/eval/citation_metrics.py`, `proof/P4/answers/`
- **Steps:**
  - [ ] Generate **30 recorded answers** from representative draft questions through the full pipeline, preserving answer JSON, verifier output, citations, traces, config hash, and git SHA.
  - [ ] Save **five refusal examples** covering retrieval abstention mechanics/model insufficiency/all-claims-removed as applicable, without forcing artificial production outcomes.
  - [ ] List every verifier-removed claim, initial/final answer association, verdict, failed check, one-line reason, and regeneration result.
  - [ ] Measure draft citation precision and unsupported claim rate with gold labels/spot checks; also report citation coverage to prepare final citation-recall evaluation.
- **Verify:** audit script fails if displayed claim lacks valid quote/citation or if a quote-failed claim appears in final output; manually review supporting sources.
- **Acceptance:** 30 answers, all removals/reasons, and five refusals exist; citation precision and unsupported claim rate are measured; summary uses verified surviving claims only.
- **Proof (planned):** [`proof/P4/answer_corpus.md`](proof/P4/answer_corpus.md), [`proof/P4/removed_claims.jsonl`](proof/P4/removed_claims.jsonl), [`proof/P4/refusals.md`](proof/P4/refusals.md), [`proof/P4/draft_metrics.md`](proof/P4/draft_metrics.md)

### P4 gate checklist

- [ ] Thirty answer records include verifier output, citations, traces, config hash, and git SHA; five refusal examples are present.
- [ ] Every removed claim and reason is listed; >30% removal triggers at most one regeneration and complete recheck.
- [ ] Citation precision and unsupported claim rate are measured on draft set; no failed-quote claim is displayed.
- [ ] Summary is composed only from verified surviving claims; all-removed cases refuse; partial claims retain badge state.
- [ ] SSE emits no answer before verification and P4 proof is committed before P5 begins.

## P5 — Evaluation and tuning

**Entry:** P4 gate passed. **Exit:** final baseline, calibration, ablations, human audit, and target decisions are evidenced.

<a id="p5-t01"></a>
### P5-T01 — Finalize 60–100-question gold set and required slices

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §3–4, §13 Gold set, §14 P5 | **Depends:** P4 gate
- **Decisions:** [D-F11](DECISION.md#d-f11)
- **Files:** `packages/eval/gold/final_v1.jsonl`, `packages/eval/gold/schema.json`, `packages/eval/gold/README.md`
- **Steps:**
  - [ ] Curate **60–100 questions** from owner's documents, each with expected answer, expected source page, expected source block, stable IDs, scope, category, and language.
  - [ ] Meet composition: about **35% factoid**, **25% table lookup**, **15% multi-passage**, **10% cross-document**, and **at least 15% unanswerable**.
  - [ ] Include **at least 10 Hindi or Marathi questions**, with per-language counts and source-quality notes; retain sufficient English comparison items.
  - [ ] Review ambiguity, alternate valid sources, answerability, and label accuracy; freeze dataset version/hash and document deviations from approximate category proportions.
- **Verify:** schema, count, category, language, duplicate, and source-provenance validators pass; sampled labels receive independent human review.
- **Acceptance:** all size/mix/minimum-language requirements are met or approximate-category deviations explained; every item has answer/page/block labels and reproducible version.
- **Proof (planned):** [`proof/P5/final_gold_set.md`](proof/P5/final_gold_set.md), [`packages/eval/gold/final_v1.jsonl`](packages/eval/gold/final_v1.jsonl), [`proof/P5/gold_validation.log`](proof/P5/gold_validation.log)

<a id="p5-t02"></a>
### P5-T02 — Run full metric harness and persist reproducible eval runs

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §4, §8 `eval_runs`/`trace_json`, §13 Metrics, §15 | **Depends:** P5-T01, P3-T07, P4-T08
- **Decisions:** [D-F10](DECISION.md#d-f10), [D-F11](DECISION.md#d-f11)
- **Files:** `packages/eval/metrics.py`, `packages/eval/run_full.py`, `packages/eval/schemas.py`, `tests/test_eval_metrics.py`
- **Steps:**
  - [ ] Compute chunk/page Recall@k, final Recall@8, MRR, citation precision/recall, unsupported claim rate, refusal accuracy, answer correctness, and question-to-verified-answer latency.
  - [ ] Use PRD definitions: citation precision via gold labels/spot checks; citation recall as factual claims carrying citation; unsupported claims include verifier/human-identified failures.
  - [ ] Record per-stage latency/call counts and p50/p95 query latency, including verification/regeneration; separately identify answer/refusal populations and denominators.
  - [ ] Insert `eval_runs` rows with config hash, git SHA, metrics JSON, dataset/model/prompt identities, timestamps, and links to raw traces; fail incomplete/dirty provenance explicitly.
- **Verify:** unit-test every formula on hand-labeled small sets; replay full run without judge where possible and reconcile aggregates to per-question rows.
- **Acceptance:** all eight §4 metrics plus per-stage latency are reported with denominators; every aggregate is reproducible from stored traces and eval metadata.
- **Proof (planned):** [`proof/P5/metric_definitions.md`](proof/P5/metric_definitions.md), [`proof/P5/full_metrics.json`](proof/P5/full_metrics.json), [`proof/P5/eval_run_rows.jsonl`](proof/P5/eval_run_rows.jsonl)

<a id="p5-t03"></a>
### P5-T03 — Calibrate abstention threshold on labeled results

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.4 FR-RET-5, §4 Refusal accuracy, §13–14 P5 | **Depends:** P5-T01, P3-T05, P3-T08
- **Decisions:** [D-P5-01](DECISION.md#d-p5-01), [D-F11](DECISION.md#d-f11)
- **Files:** `packages/eval/calibrate_abstention.py`, `config/retrieval.yaml`, `tests/test_abstention.py`
- **Steps:**
  - [ ] Join top rerank scores to answerable/unanswerable gold labels and ensure examples represent categories, languages, collections, and hard negatives.
  - [ ] Sweep observed score range without assuming scale; report selection curve of coverage, refusal accuracy, false refusal, and false acceptance at each candidate threshold.
  - [ ] Choose threshold using stated objective/constraints and validation split or other leakage-safe procedure; resolve D-P5-01 with evidence and limitations.
  - [ ] Pin threshold/version, add boundary regression tests, rerun full suite, and attach eval run/config hash/git SHA to the change.
- **Verify:** report includes every labeled item, candidate threshold, confusion counts, and selected operating point; offline gate tests replay selected value.
- **Acceptance:** production threshold is no longer unset or guessed; selection evidence targets refusal accuracy ≥0.90 while documenting answer coverage tradeoff.
- **Proof (planned):** [`proof/P5/abstention_calibration.md`](proof/P5/abstention_calibration.md), [`proof/P5/abstention_curve.csv`](proof/P5/abstention_curve.csv), [`proof/P5/abstention_labeled_scores.jsonl`](proof/P5/abstention_labeled_scores.jsonl)

<a id="p5-t04"></a>
### P5-T04 — Calibrate fuzzy quote threshold around default 92

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.6 FR-VER-2, §13–15, §4 Citation precision | **Depends:** P5-T01, P4-T03
- **Decisions:** [D-P5-02](DECISION.md#d-p5-02), [D-F11](DECISION.md#d-f11)
- **Files:** `packages/eval/calibrate_quotes.py`, `config/verification.yaml`, `tests/test_quote_matcher.py`
- **Steps:**
  - [ ] Build labeled valid/invalid quote pairs from recorded answers and adversarial cases, including Unicode, whitespace/case, multilingual, near-copy, wrong-block, and >25-word samples.
  - [ ] Sweep thresholds around initial partial-ratio **92**; report false acceptance, false rejection, precision/recall, and examples near each decision boundary.
  - [ ] Retain 92 or select another value only from evidence; resolve D-P5-02 with rationale, affected claims, and limitations.
  - [ ] Pin threshold/config version, add regression cases, rerun answer evaluation, and attach eval run/config hash/git SHA.
- **Verify:** every chosen threshold has reproducible curve/confusion matrix; existing failed-quote fixtures remain rejected and valid normalization cases retain intended behavior.
- **Acceptance:** calibrated threshold is documented and versioned; no failed-quote claim becomes displayable; any change improves measured tradeoff without hiding regressions.
- **Proof (planned):** [`proof/P5/quote_calibration.md`](proof/P5/quote_calibration.md), [`proof/P5/quote_threshold_curve.csv`](proof/P5/quote_threshold_curve.csv), [`proof/P5/quote_regression_cases.jsonl`](proof/P5/quote_regression_cases.jsonl)

<a id="p5-t05"></a>
### P5-T05 — Run all four baseline ablations safely

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §13 Method, §14 P5, §16 risks 4/6 | **Depends:** P5-T02
- **Decisions:** [D-F04](DECISION.md#d-f04), [D-F11](DECISION.md#d-f11)
- **Files:** `packages/eval/ablate_all.py`, `packages/eval/ablation_config/`, `proof/P5/ablation_runs/`
- **Steps:**
  - [ ] Run **no rerank**, **no hybrid**, and **single versus double parse pass** against the same gold set with controlled configs and complete per-query results.
  - [ ] Run **verifier off** strictly in isolated evaluation; never expose its unverified answers through production chat/UI or use it as a runtime fallback.
  - [ ] Compare all applicable retrieval, citation, unsupported-claim, correctness, refusal, and latency metrics, including per-language/table/multi-document slices.
  - [ ] Explain what each stage earns, regressions/variance, config differences, and any follow-up; do not silently drop a failed ablation.
- **Verify:** every ablation has eval row/config hash/git SHA and raw results; production config audit proves verifier remains mandatory.
- **Acceptance:** all four comparisons are complete and reproducible; verifier-off is evaluation-only; parse quality effect is measured rather than assumed.
- **Proof (planned):** [`proof/P5/ablations.md`](proof/P5/ablations.md), [`proof/P5/ablation_metrics.csv`](proof/P5/ablation_metrics.csv), [`proof/P5/verifier_off_isolation.md`](proof/P5/verifier_off_isolation.md)

<a id="p5-t06"></a>
### P5-T06 — Judge answers with Ultra and audit 20% plus disagreements

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §4 Answer correctness, §13 Method, §14 P5, §16 risks 6–7 | **Depends:** P5-T02
- **Decisions:** [D-F03](DECISION.md#d-f03), [D-F11](DECISION.md#d-f11)
- **Files:** `packages/eval/judge_answers.py`, `config/prompts/judge.txt`, `packages/eval/human_audit.py`, `proof/P5/judge/`
- **Steps:**
  - [ ] As a separately authorized live procedure, use Ultra to judge final verified answers against gold answers with versioned rubric/prompt and recorded raw judgments.
  - [ ] Manually audit a representative **20% of items**, selected before seeing judgments; record human scores, rationale, and auditor decision independently.
  - [ ] Review **every judge/human disagreement**, adjudicate final labels, categorize verifier false support/false removal, and report judge agreement/limitations.
  - [ ] Report answer correctness and other applicable metrics separately for English, Hindi, and Marathi, plus combined results and sample sizes.
- **Verify:** judge/audit join covers all required items; no disagreement lacks adjudication; routine tests replay recorded judgments without NIM quota.
- **Acceptance:** answer correctness ≥0.85 is measured against adjudicated labels or miss is escalated to P5-T07; language slices and audit are complete.
- **Proof (planned):** [`proof/P5/answer_judging.md`](proof/P5/answer_judging.md), [`proof/P5/human_audit.csv`](proof/P5/human_audit.csv), [`proof/P5/disagreement_review.md`](proof/P5/disagreement_review.md), [`proof/P5/language_results.md`](proof/P5/language_results.md)

<a id="p5-t07"></a>
### P5-T07 — Compare all targets, analyze worst 15, and decide every miss

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §4, §13–15, §16 | **Depends:** P5-T03, P5-T04, P5-T05, P5-T06
- **Decisions:** [D-F11](DECISION.md#d-f11), [D-P5-03](DECISION.md#d-p5-03)
- **Files:** `packages/eval/target_report.py`, `packages/eval/error_analysis.py`, `docs/evaluation.md`
- **Steps:**
  - [ ] Compare baseline against all initial targets: Recall@8 ≥0.90, MRR ≥0.75, citation precision ≥0.95, citation recall ≥0.98, unsupported claim rate ≤3%, refusal accuracy ≥0.90, answer correctness ≥0.85, query latency p95 ≤30 s.
  - [ ] Analyze worst **15 questions** end to end: parsing, chunking, retrieval, rerank, context, answer, quote, entailment, refusal, citation region, and latency.
  - [ ] For every metric miss, document cause, user impact, remediation/follow-up owner, and explicit Atharva decision; record accepted residual limitations.
  - [ ] Recalibrate targets only during P5 with evidence and written reason; later target changes require formally reopened P5, new evidence, and approval—never silent lowering.
- **Verify:** baseline generator checks all eight metrics and links raw eval rows/traces; every miss maps to D-P5-03 and a concrete decision.
- **Acceptance:** targets are met or each miss is individually explained/decided; worst-15 analysis and resolved calibration decisions are complete; no target changed elsewhere.
- **Proof (planned):** [`proof/P5/baseline.md`](proof/P5/baseline.md), [`proof/P5/worst_15.md`](proof/P5/worst_15.md), [`proof/P5/target_decisions.md`](proof/P5/target_decisions.md), [`proof/P5/eval_run_rows.jsonl`](proof/P5/eval_run_rows.jsonl)

### P5 gate checklist

- [ ] `proof/P5/baseline.md` contains all eight metrics against §4 targets, denominators, per-language results, and config/git/dataset identities.
- [ ] `eval_runs` rows, all four ablations, threshold calibration, Ultra judge, 20% human audit, and every disagreement review are committed.
- [ ] Worst-15 error analysis is complete; every miss has cause, user impact, decision, and follow-up.
- [ ] D-P5-01 and D-P5-02 are resolved; D-P5-03 records misses/recalibration. No target was silently changed.
- [ ] Production verifier remains mandatory; P5 proof is committed before P6 begins.

## P6 — Web UI

**Entry:** P5 gate passed. **Exit:** five recorded use cases pass and 20/20 sampled citation highlights land correctly.

<a id="p6-t01"></a>
### P6-T01 — Build Next.js 15 shell and typed API/SSE client

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5, §7.7, §9, §12 Secrets | **Depends:** P5 gate
- **Decisions:** [D-F02](DECISION.md#d-f02), [D-F09](DECISION.md#d-f09), [D-F10](DECISION.md#d-f10)
- **Files:** `apps/web/app/`, `apps/web/components/`, `apps/web/lib/api.ts`, `apps/web/lib/sse.ts`, `apps/web/package.json`, `apps/web/tests/`
- **Steps:**
  - [ ] Create Next.js **15 App Router** TypeScript shell with locked dependencies, formatting/lint/typecheck, component/test conventions, and accessible base layout.
  - [ ] Generate or define typed REST/SSE contracts matching backend schemas, including malformed event, disconnect, retry, refusal, and failure handling.
  - [ ] Configure API base URL without exposing NIM keys; keep provider credentials and privileged API calls server-side and test built client/server bundles for secrets.
  - [ ] Set up component tests and Playwright with deterministic API/SSE fixtures for all ingestion and chat states.
- **Verify:** `npm run lint`, `npm run typecheck`, `npm test`, and production build pass; browser network/storage inspection reveals no provider secret.
- **Acceptance:** typed client handles complete API/event surface without `any` escapes at trust boundaries; locked test tooling runs offline and SSE never fabricates final answers.
- **Proof (planned):** [`proof/P6/web_bootstrap.md`](proof/P6/web_bootstrap.md), [`proof/P6/secret_bundle_audit.md`](proof/P6/secret_bundle_audit.md)

<a id="p6-t02"></a>
### P6-T02 — Implement collections, library, upload, delete, and live progress

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.7 FR-UI-1, §7.1 FR-ING-7, §9 | **Depends:** P6-T01
- **Decisions:** [D-F09](DECISION.md#d-f09), [D-P1-03](DECISION.md#d-p1-03)
- **Files:** `apps/web/app/library/`, `apps/web/components/collections/`, `apps/web/components/documents/`, `apps/web/tests/library.spec.ts`
- **Steps:**
  - [ ] Implement collection list/create and document library with filename, status, page counts, timestamps, and accessible empty/loading/error states.
  - [ ] Upload PDF/PNG/JPG with client-side hints plus server-enforced type/size errors; display duplicate response according to resolved reject/link policy.
  - [ ] Poll or subscribe to `GET /documents/{id}` for queued, rendering, parsing, chunking, embedding, indexed, failed and processed/total/failed page counts.
  - [ ] Implement `DELETE /documents/{id}` with clear confirmation and failure handling; prevent accidental deletion while request is pending and refresh dependent views.
- **Verify:** Playwright fixtures cover all seven states, partial page failures, invalid/oversized/duplicate upload, delete cancel/confirm/error, and collection isolation.
- **Acceptance:** users can complete library workflows and see truthful live progress; no success state is shown before server confirmation; destructive action is explicit.
- **Proof (planned):** [`proof/P6/library_workflows.md`](proof/P6/library_workflows.md), [`proof/P6/library_playwright.log`](proof/P6/library_playwright.log)

<a id="p6-t03"></a>
### P6-T03 — Implement chat, SSE status, verified answer, and failure states

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.7 FR-UI-2/3/5, §9, §10 | **Depends:** P6-T01
- **Decisions:** [D-F07](DECISION.md#d-f07), [D-F08](DECISION.md#d-f08), [D-F09](DECISION.md#d-f09)
- **Files:** `apps/web/app/chat/`, `apps/web/components/chat/`, `apps/web/components/answer/`, `apps/web/tests/chat.spec.ts`
- **Steps:**
  - [ ] Build question box, collection/document scope controls, conversation history, original-question display, pending/cancel/retry states, and accessible status line.
  - [ ] Consume SSE statuses rewriting, retrieving, reranking, answering, verifying; show answer only after final verified `answer` event, never answer-token streaming.
  - [ ] Render short summary, detailed explanation, and numbered sources with document, page, quote, verdict state, and stable claim/citation associations.
  - [ ] Render clear retrieval/model refusals, all-claims-removed refusals, JSON/verification failures, disconnects, and confidential-query denial without fake citations or partial answers.
- **Verify:** scripted SSE tests assert event order and UI at every status, delayed/out-of-order/disconnected streams, refusal/failure, and absence of pre-verification answer DOM.
- **Acceptance:** all answer layouts and non-answer states work; original question stays visible; only final verified content appears as answer.
- **Proof (planned):** [`proof/P6/chat_states.md`](proof/P6/chat_states.md), [`proof/P6/sse_ui_tests.log`](proof/P6/sse_ui_tests.log)

<a id="p6-t04"></a>
### P6-T04 — Add citation chips, chooser, partial badges, and quotes

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.7 FR-UI-3–5, §16 risk 5 | **Depends:** P6-T03
- **Decisions:** [D-F07](DECISION.md#d-f07), [D-F08](DECISION.md#d-f08)
- **Files:** `apps/web/components/citations/`, `apps/web/components/answer/claim.tsx`, `apps/web/tests/citations.spec.ts`
- **Steps:**
  - [ ] Render numbered inline citation chips associated with each surviving claim and matching numbered source entries.
  - [ ] Open a keyboard/screen-reader-accessible chooser when one sentence has multiple citations; preserve selected citation through viewer navigation.
  - [ ] Display visible `partial` badges without implying full support; show exact quote beside source/page and eventual highlight to address coarse block granularity.
  - [ ] Hide removed unsupported claims from normal answer presentation while keeping failures/refusals clear and preventing orphaned chips.
- **Verify:** component/Playwright tests cover one/multiple/missing citations, chooser keyboard navigation, partial verdict, long multilingual quotes, and source wrapping.
- **Acceptance:** every factual claim has usable citation UI; multiple citations are unambiguous; quote and partial state remain visible next to source navigation.
- **Proof (planned):** [`proof/P6/citation_interactions.md`](proof/P6/citation_interactions.md), [`proof/P6/citation_accessibility.md`](proof/P6/citation_accessibility.md)

<a id="p6-t05"></a>
### P6-T05 — Navigate pdf.js and highlight exact stored block regions

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5, §7.7 FR-UI-4, §7.1 FR-ING-5, §14 P6 | **Depends:** P6-T04, P4-T06
- **Decisions:** [D-F02](DECISION.md#d-f02), [D-F04](DECISION.md#d-f04), [D-F08](DECISION.md#d-f08)
- **Files:** `apps/web/components/pdf/viewer.tsx`, `apps/web/components/pdf/highlight.tsx`, `apps/web/lib/pdf_geometry.ts`, `apps/web/tests/pdf_highlight.spec.ts`
- **Steps:**
  - [ ] Integrate pdf.js with authenticated original-file loading, page navigation, zoom/resize, loading/error states, and safe cleanup of document/worker resources.
  - [ ] On citation click, navigate to cited page, load stored blocks, transform `bbox_pdf` into viewport coordinates, and draw highlighted block overlay.
  - [ ] Handle pdf.js viewport scale/rotation, CSS/device pixel ratio, multi-block fallback, multi-page tables, and repeated navigation without stale overlays.
  - [ ] Display verbatim quote beside highlight; preserve block—not word-level—granularity and make source page/region obvious.
- **Verify:** geometry unit tests and Playwright screenshots/assertions cover portrait/landscape, rotation, zoom/resize, downscaled scans, multiple blocks, and cross-page citations.
- **Acceptance:** click lands on correct page and highlight matches stored PDF coordinates at supported zoom/rotation; no highlight silently selects wrong block.
- **Proof (planned):** [`proof/P6/pdf_geometry_tests.md`](proof/P6/pdf_geometry_tests.md), [`proof/P6/highlight_examples/`](proof/P6/highlight_examples/)

<a id="p6-t06"></a>
### P6-T06 — Render sanitized table HTML beside highlighted page

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §7.7 FR-UI-6, §7.2 FR-CHK-4, §3 UC2 | **Depends:** P6-T05
- **Decisions:** [D-F05](DECISION.md#d-f05), [D-F08](DECISION.md#d-f08)
- **Files:** `apps/web/components/pdf/table_panel.tsx`, `apps/web/lib/sanitize_html.ts`, `apps/web/tests/table_panel.spec.ts`
- **Steps:**
  - [ ] For table citations, render stored table HTML in a responsive side panel next to highlighted PDF page while preserving quote and page/region context.
  - [ ] Sanitize stored HTML with an allowlist for table structure; remove scripts, event handlers, active URLs, foreign objects, and unsafe CSS before rendering.
  - [ ] Keep table headers/rows/cells aligned after chunk row splitting and repeated headers; support wide-table scrolling and multilingual content.
  - [ ] Provide accessible table semantics, panel close/mobile behavior, and fallback to flattened text if safe HTML cannot be rendered.
- **Verify:** XSS fixtures and Playwright tests cover malicious HTML, split tables, wide/multilingual tables, missing HTML, side-panel layout, and citation switching.
- **Acceptance:** table citation opens exact cited table/chunk beside correct page; unsafe markup never executes; repeated headers and source region remain understandable.
- **Proof (planned):** [`proof/P6/table_side_panel.md`](proof/P6/table_side_panel.md), [`proof/P6/table_sanitization_tests.log`](proof/P6/table_sanitization_tests.log)

<a id="p6-t07"></a>
### P6-T07 — Validate UC1–UC5 and 20-citation highlight gate

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §3 UC1–UC5, §14 P6, §15 | **Depends:** P6-T02, P6-T06
- **Decisions:** [D-F08](DECISION.md#d-f08), [D-F11](DECISION.md#d-f11)
- **Files:** `apps/web/e2e/use_cases.spec.ts`, `apps/web/e2e/citation_gate.spec.ts`, `packages/eval/audit_highlights.py`, `proof/P6/recordings/`
- **Steps:**
  - [ ] Record end-to-end UC1 factual answer/source passage, UC2 exact table cell region, UC3 cross-document answer, UC4 citation-to-highlight, and UC5 clear refusal.
  - [ ] Add Playwright citation-click test that asserts page number, selected block ID, and highlight geometry/position—not merely that viewer opened.
  - [ ] Sample **20 citations** across documents, pages, text/tables, multi-block fallback, and zoom/rotation cases; compare expected and actual page/bbox regions.
  - [ ] Save recordings, traces, screenshots, failures/fixes, and 20-item audit; rerun complete flow after fixes rather than cropping out errors.
- **Verify:** CI Playwright tests pass; independent reviewer checks all recordings and 20 sampled highlights against stored source blocks.
- **Acceptance:** all five use cases pass on recording; **20 of 20** sampled citations highlight the correct block/page with citation quote available.
- **Proof (planned):** [`proof/P6/use_case_recordings.md`](proof/P6/use_case_recordings.md), [`proof/P6/citation_click_tests.log`](proof/P6/citation_click_tests.log), [`proof/P6/highlight_audit.csv`](proof/P6/highlight_audit.csv), [`proof/P6/recordings/`](proof/P6/recordings/)

### P6 gate checklist

- [ ] Screen recordings demonstrate UC1–UC5 with no hidden unverified answer state.
- [ ] Playwright clicks citations and asserts page/block/highlight position, including table side panel and multi-citation chooser.
- [ ] Twenty of twenty sampled citations highlight correct page/block; quote is visible alongside coarse block region.
- [ ] Secret-bundle, table-sanitization, responsive, keyboard, refusal/failure, and SSE ordering checks pass.
- [ ] P6 proof is committed before P7 begins.

## P7 — Hardening and release

**Entry:** P6 gate passed. **Exit:** seven core tasks and release gate pass. `P7-T08` is optional and never blocks release.

<a id="p7-t01"></a>
### P7-T01 — Add authentication and per-user authorization everywhere

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5, §8–9, §12 Privacy/Secrets, §14 P7, §16 risk 8 | **Depends:** P6 gate
- **Decisions:** [D-F09](DECISION.md#d-f09), [D-F10](DECISION.md#d-f10)
- **Files:** `apps/api/auth/`, `apps/api/routers/`, `apps/web/app/auth/`, `apps/web/middleware.ts`, `tests/test_authorization.py`
- **Steps:**
  - [ ] Implement `POST /auth/register` and `POST /auth/login` with established password hashing/session protections, generic credential errors, expiration/logout, and secret-safe configuration.
  - [ ] Replace development-only identity with authenticated principal; associate users/collections/conversations and scope every document, file, block, message, chat, delete, and indexing operation.
  - [ ] Authorize object ownership server-side on every route and worker/vector/lexical query; prevent ID enumeration and cross-user cache/source leakage.
  - [ ] Retain and test confidential-collection hosted indexing/query block until a local model path exists; ensure authentication does not imply multi-tenant SaaS/collaboration scope.
- **Verify:** two-user integration matrix attempts every object route and cross-user IDs; auth/session/password storage tests and browser credential inspection pass.
- **Acceptance:** unauthenticated/cross-user access is denied consistently; all queries preserve user/collection/doc filters; confidential content cannot use hosted path.
- **Proof (planned):** [`proof/P7/authorization_matrix.md`](proof/P7/authorization_matrix.md), [`proof/P7/auth_tests.log`](proof/P7/auth_tests.log), [`proof/P7/confidential_enforcement.md`](proof/P7/confidential_enforcement.md)

<a id="p7-t02"></a>
### P7-T02 — Add quota and usage dashboard without secret exposure

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §11, §12 Secrets, §14 P7 | **Depends:** P7-T01
- **Decisions:** [D-F10](DECISION.md#d-f10), [D-P0-06](DECISION.md#d-p0-06)
- **Files:** `apps/api/routers/usage.py`, `apps/api/services/usage.py`, `apps/web/app/usage/`, `apps/web/components/usage/`, `tests/test_usage.py`
- **Steps:**
  - [ ] Aggregate user-visible hosted calls, tokens/credits when reported, cache hits, throttling, fallbacks, and ingestion/query consumption from redacted gateway ledgers.
  - [ ] Show measured per-model limits/current usage and distinguish known values from unavailable provider metrics; never display the unverified 1,000-credit/40-RPM report as fact.
  - [ ] Expose only minimum necessary usage API with per-user authorization, sensible time ranges, empty/error states, and no document text/request payloads by default.
  - [ ] Audit API responses, browser bundles, screenshots, logs, and client storage for API keys, environment values, or other users' usage.
- **Verify:** usage totals reconcile to ledger fixtures; cross-user tests deny access; secret scan and dashboard component tests pass offline.
- **Acceptance:** dashboard accurately explains quota consumption/throttling/cache benefit and never invents balances or exposes secrets/content.
- **Proof (planned):** [`proof/P7/usage_dashboard.md`](proof/P7/usage_dashboard.md), [`proof/P7/usage_reconciliation.csv`](proof/P7/usage_reconciliation.csv), [`proof/P7/dashboard_secret_scan.log`](proof/P7/dashboard_secret_scan.log)

<a id="p7-t03"></a>
### P7-T03 — Harden structured observability and full health checks

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §8 `trace_json`, §9 `GET /health`, §12 Observability/Reliability | **Depends:** P7-T01
- **Decisions:** [D-F09](DECISION.md#d-f09), [D-F10](DECISION.md#d-f10)
- **Files:** `apps/api/observability.py`, `apps/api/routers/health.py`, `apps/worker/observability.py`, `apps/parse_service/health.py`, `tests/test_health.py`
- **Steps:**
  - [ ] Standardize structured JSON logs with request/ingestion trace IDs, stage/model/outcome/latency/call counts, and correlation across API, workers, gateway, and parser.
  - [ ] Apply centralized redaction to credentials, authorization headers/cookies, connection strings, sensitive prompts/chunks/questions, raw model payloads, and error traces.
  - [ ] Implement `GET /health` reporting parse service, selected vector store/Qdrant, PostgreSQL, and NIM reachability with timeout/degraded semantics and no sensitive details.
  - [ ] Add trace inspection/runbook for ingestion pause/retry, gateway circuit/fallback, query verification/refusal, and missing provenance.
- **Verify:** fault-injection tests make each dependency unavailable; assert health degradation/timeouts and complete traces; automated canary secrets/content stay out of logs.
- **Acceptance:** all required dependencies are covered; traces reconstruct query/ingestion stages; logs are structured, useful, and pass redaction tests.
- **Proof (planned):** [`proof/P7/health_fault_matrix.md`](proof/P7/health_fault_matrix.md), [`proof/P7/log_redaction.md`](proof/P7/log_redaction.md), [`proof/P7/trace_examples.json`](proof/P7/trace_examples.json)

<a id="p7-t04"></a>
### P7-T04 — Package Compose stack and separate GPU parser startup

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5, §12 Portability/Platform, §14 P7, §18 | **Depends:** P7-T03
- **Decisions:** [D-F02](DECISION.md#d-f02), [D-F10](DECISION.md#d-f10), [D-P0-01](DECISION.md#d-p0-01)
- **Files:** `docker-compose.yml`, `apps/*/Dockerfile`, `scripts/bootstrap.*`, `apps/parse_service/start.sh`, `.env.example`, `docs/deployment.md`
- **Steps:**
  - [ ] Configure `docker compose up` for web, API, workers, Redis, PostgreSQL, selected vector store/Qdrant, migrations, networks, volumes, health dependencies, and non-root runtime where practical.
  - [ ] Keep GPU parse service outside Compose with separate documented Linux/WSL2 start script, pinned environment, GPU passthrough checks, readiness endpoint, and restart instructions.
  - [ ] Make bootstrap idempotent: validate env without printing secrets, run migrations, initialize stores/indexes, wait bounded time for health, and preserve uploaded files/data.
  - [ ] Test fresh start, restart, upgrade/migration, stopped parser, persistent volumes, and Windows-host/WSL2 networking against documented supported topology.
- **Verify:** from clean checkout with test env, Compose and separate parser procedures reach healthy state; restart retains collections/documents and resumes ingestion safely.
- **Acceptance:** one documented Compose command starts everything except parser; parser start works independently; no manual undocumented schema/data step is required.
- **Proof (planned):** [`proof/P7/compose_startup.log`](proof/P7/compose_startup.log), [`proof/P7/restart_persistence.md`](proof/P7/restart_persistence.md), [`proof/P7/gpu_parser_start.log`](proof/P7/gpu_parser_start.log)

<a id="p7-t05"></a>
### P7-T05 — Write complete reproducible README and operating guides

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §5–6, §11–12, §14 P7, §16, §18 | **Depends:** P7-T04
- **Decisions:** [D-F10](DECISION.md#d-f10), [D-F11](DECISION.md#d-f11), [D-P0-06](DECISION.md#d-p0-06)
- **Files:** `README.md`, `docs/architecture.md`, `docs/configuration.md`, `docs/privacy.md`, `docs/testing.md`, `docs/proof.md`
- **Steps:**
  - [ ] Document architecture/model roles, exact parse contract, chunk/index/retrieval/verification flow, configuration, fallbacks, and block-level—not word-level—citation granularity.
  - [ ] Give fresh-clone setup for Windows/WSL2 or supported Linux, GPU parser plus Compose, migrations, seed/sample document, first verified answer, tests, and proof reproduction.
  - [ ] Explain measured quota/cost behavior, fixture-vs-live test separation, eval attachments, troubleshooting, privacy terms/URLs/access dates, and confidential-collection block.
  - [ ] State limitations/non-goals: no web search/agents/fine-tuning/billing/collaboration, no core DOCX/PPTX, hosted input exposure, parser/language limits, and unresolved eval misses.
- **Verify:** links/commands/config examples are checked against repository; a reader following README alone reaches healthy services and verified answer without tribal knowledge.
- **Acceptance:** setup, privacy, security, configuration, fallbacks, evaluation, limitations, and proof links are complete and match implemented behavior.
- **Proof (planned):** [`proof/P7/readme_review.md`](proof/P7/readme_review.md), [`proof/P7/documentation_link_check.log`](proof/P7/documentation_link_check.log)

<a id="p7-t06"></a>
### P7-T06 — Run controlled 8-questions/minute load and latency test

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §4 Query latency, §11, §14 P7, §16 risk 2 | **Depends:** P7-T04, P5-T07
- **Decisions:** [D-F11](DECISION.md#d-f11), [D-P0-06](DECISION.md#d-p0-06)
- **Files:** `packages/eval/load_test.py`, `packages/eval/load_report.py`, `config/load_test.yaml`, `proof/P7/load_results/`
- **Steps:**
  - [ ] Define authorized live load corpus, duration, concurrency, warm-up, arrival schedule, and stop conditions at controlled **8 questions per minute** with nothing else running.
  - [ ] Measure question-to-verified-answer latency p50/p95/error rate, per-stage latency, five potential hosted calls/question, rewrite bypasses, queueing, retries, throttling, and fallbacks.
  - [ ] Check gateway fairness/token buckets, cache correctness, answer verification, source accuracy on sample, and confidential/privacy behavior under load.
  - [ ] Reconcile request/credit ledger and system/GPU resources; report sustained vs throttled throughput and compare p95 to ≤30 s target without dropping failed/slow requests.
- **Verify:** rerun from committed traces/config; totals reconcile sent/completed/failed/throttled calls and every reported percentile uses documented denominator.
- **Acceptance:** 8 questions/minute procedure and report are complete; query p95 ≤30 s or miss has cause/user impact/remediation decision; verification was never bypassed.
- **Proof (planned):** [`proof/P7/load_test.md`](proof/P7/load_test.md), [`proof/P7/latency_distribution.csv`](proof/P7/latency_distribution.csv), [`proof/P7/load_quota_ledger.csv`](proof/P7/load_quota_ledger.csv)

<a id="p7-t07"></a>
### P7-T07 — Perform final evaluation, clean-machine run, and release audit

- **Status:** `not_started` | **Owner:** Atharva
- **PRD:** §2, §4, §12–16 | **Depends:** P7-T01, P7-T02, P7-T03, P7-T04, P7-T05, P7-T06
- **Decisions:** [D-F10](DECISION.md#d-f10), [D-F11](DECISION.md#d-f11), [D-P5-03](DECISION.md#d-p5-03)
- **Files:** `packages/eval/release_audit.py`, `docs/release_checklist.md`, `proof/P7/final_eval/`
- **Steps:**
  - [ ] Run final frozen gold-set evaluation on release config; store all metrics, per-language results, eval rows, config hash, git SHA, and comparison to P5 baseline/targets.
  - [ ] On a clean machine or equivalent fresh environment, follow README alone from fresh clone through upload, indexing, question, verified cited answer, and citation highlight; log every step.
  - [ ] Audit all task/proof links, decision statuses, eval attachments, auth matrix, confidential block, secrets/logs/browser bundles, fixture/live separation, dependency licenses, and non-goal leakage.
  - [ ] Verify no done task lacks real committed proof; reopen failures or document accepted misses with owner/follow-up, then make explicit release/no-release decision.
- **Verify:** independent release checklist uses code and artifacts—not agent summaries; clean run and final metrics are reproducible from committed identifiers.
- **Acceptance:** fresh clone reaches working verified answer by README alone; final eval and clean-machine log exist; security/privacy/proof audits pass or block release.
- **Proof (planned):** [`proof/P7/clean_machine_setup.md`](proof/P7/clean_machine_setup.md), [`proof/P7/final_eval.md`](proof/P7/final_eval.md), [`proof/P7/release_audit.md`](proof/P7/release_audit.md), [`proof/P7/release_decision.md`](proof/P7/release_decision.md)

<a id="p7-t08"></a>
### P7-T08 — OPTIONAL: independently evaluate DOCX/PPTX, page images, and answer cache

- **Status:** `not_started` | **Owner:** Atharva | **Scope:** optional stretch; non-blocking
- **PRD:** §2 Non-goals, §14 P7 Stretch | **Depends:** release gate; each subfeature separately approved
- **Decisions:** [D-F01](DECISION.md#d-f01), [D-F11](DECISION.md#d-f11)
- **Files:** `docs/stretch/`, `apps/worker/tasks/convert.py`, `apps/api/services/retrieval/page_images.py`, `apps/api/services/answer_cache.py`, `proof/P7/stretch/`
- **Steps:**
  - [ ] Treat DOCX/PPTX-to-PDF conversion, page-image retrieval with multimodal embed/rerank, and answer cache as three independent experiments; completing none is valid for v1.
  - [ ] Before each experiment, define threat/privacy model, supported input/conversion fidelity, exact provider contracts, cache key/invalidation/ownership, and isolated acceptance criteria.
  - [ ] Evaluate each independently against gold/regression sets with config hash/git SHA; answer cache must preserve collection/model/config/threshold scope and mandatory verification.
  - [ ] Keep disabled by default unless evidence shows no quality/security/privacy regression and Atharva approves; never claim stretch work as required core proof.
- **Verify:** each enabled subfeature has its own tests/eval/privacy evidence and rollback switch; core release suite passes with all stretch features disabled.
- **Acceptance:** optional status remains explicit; no experiment delays release, weakens citations/verifier/auth, or sends confidential data to hosted models.
- **Proof (planned):** [`proof/P7/stretch/README.md`](proof/P7/stretch/README.md), [`proof/P7/stretch/evaluations.md`](proof/P7/stretch/evaluations.md)

### P7 release gate checklist

- [ ] Seven core tasks are done; optional `P7-T08` is complete, deferred, or rejected without blocking release.
- [ ] Clean-machine setup log, controlled 8-questions/minute load report, and final eval run are committed.
- [ ] Fresh clone reaches verified cited answer and correct highlight by following README alone.
- [ ] Authorization, confidential-data, secrets/log/browser, health, restart, and fixture/live separation checks pass.
- [ ] Every target is met or carries approved cause/user-impact/decision/follow-up; no unverified-answer bypass or silent target change exists.

## Requirement traceability

Every requirement below has an owning implementation task and proof route. Multiple task links indicate implementation plus verification, not optional coverage.

### Functional requirements — all 42

| Requirement | Owning task(s) | Completion evidence |
| --- | --- | --- |
| FR-ING-1 PDF/PNG/JPG, cap, SHA-256, collection duplicates | [P1-T02](#p1-t02) | Upload/duplicate tests and policy |
| FR-ING-2 RGB 150 dpi, 1664 × 2048 bound, actual size | [P1-T03](#p1-t03), [P0-T03](#p0-t03) | Geometry tests and smoke pages |
| FR-ING-3 exact prompt, 8744 tokens, vLLM sampling/control tokens | [P1-T04](#p1-t04), [P0-T03](#p0-t03) | Raw output and parse contract tests |
| FR-ING-4 raw output and postprocessed class/bbox/text blocks | [P1-T04](#p1-t04), [P1-T07](#p1-t07) | Parse JSON and ten overlays |
| FR-ING-5 pixel/PDF-point bboxes with downscale adjustment | [P1-T04](#p1-t04), [P6-T05](#p6-t05) | Hand calculations and viewer geometry |
| FR-ING-6 two page retries, failure isolation, idempotent resume | [P1-T05](#p1-t05) | Retry/restart/outage logs |
| FR-ING-7 seven document states and page counts | [P1-T06](#p1-t06), [P6-T02](#p6-t02) | Status API and live library tests |
| FR-ING-8 start concurrency 4; tune from throughput/VRAM | [P1-T08](#p1-t08) | Concurrency 1/2/4/8 benchmark |
| FR-CHK-1 block/chunk semantics from observed classes | [P2-T01](#p2-t01), [P1-T07](#p1-t07) | Class mapping and chunk fixtures |
| FR-CHK-2 exclude headers/footers/page numbers; retain blocks | [P2-T01](#p2-t01) | Exclusion/provenance tests |
| FR-CHK-3 400–800 tokens, ~12% overlap, safe boundaries | [P2-T01](#p2-t01), [P2-T04](#p2-t04) | Chunker/property tests and histogram |
| FR-CHK-4 table chunking >1,200 rows/header/HTML/flat text | [P2-T02](#p2-t02), [P2-T08](#p2-t08) | Table tests and ten HTML examples |
| FR-CHK-5 one chart chunk from data/caption | [P2-T02](#p2-t02) | Chart fixtures |
| FR-CHK-6 section path only in embedding text | [P2-T03](#p2-t03) | Display/embed text assertions |
| FR-CHK-7 tested cross-page `continues_from` heuristics | [P2-T03](#p2-t03), [P3-T04](#p3-t04) | Continuation evaluation/context tests |
| FR-CHK-8 source blocks/pages/bboxes for every chunk | [P2-T01](#p2-t01), [P2-T06](#p2-t06), [P2-T08](#p2-t08) | Provenance schema and audit |
| FR-CHK-9 real tokenizer/proxy below measured embed limit | [P2-T04](#p2-t04), [P0-T05](#p0-t05) | Limit/calibration report |
| FR-IDX-1 batched gateway embeddings; response-derived dimension | [P2-T06](#p2-t06), [P2-T07](#p2-t07) | Dimension/cache/store tests |
| FR-IDX-2 eight required vector payload fields | [P2-T07](#p2-t07) | Payload/filter contract audit |
| FR-IDX-3 PostgreSQL `simple` tsvector multilingual lexical search | [P2-T07](#p2-t07) | English/Hindi/Marathi tests |
| FR-IDX-4 text-hash embedding cache, no repeat quota | [P2-T06](#p2-t06), [P2-T08](#p2-t08) | Zero-call identical reingestion |
| FR-RET-1 conditional standalone rewrite; retain original | [P3-T01](#p3-t01) | Rewrite/history fixtures |
| FR-RET-2 scoped dense 40 + lexical 40 | [P3-T02](#p3-t02) | Scope/top-k integration tests |
| FR-RET-3 RRF constant 60 | [P3-T03](#p3-t03) | Hand-calculated RRF tests |
| FR-RET-4 rerank top 30 to 8 | [P3-T03](#p3-t03) | Recorded rerank traces/tests |
| FR-RET-5 score-based abstention calibrated in P5 | [P3-T05](#p3-t05), [P5-T03](#p5-t03) | Fixture mechanics and labeled curve |
| FR-RET-6 C1–C8, continuation-only neighbors, token budget | [P3-T04](#p3-t04) | Context contract/fixtures |
| FR-GEN-1 grounded prompt, claim ID/quote, abstain | [P4-T01](#p4-t01) | Versioned prompt/schema tests |
| FR-GEN-2 exact JSON; one repair then visible failure | [P4-T02](#p4-t02) | Call-count and failure fixtures |
| FR-GEN-3 verbatim quotes ≤25 words | [P4-T01](#p4-t01), [P4-T03](#p4-t03) | Schema and quote tests |
| FR-VER-1 valid JSON and provided-context chunk IDs | [P4-T03](#p4-t03) | Structural verifier tests |
| FR-VER-2 NFKC/whitespace/case fuzzy quote, initial 92 | [P4-T03](#p4-t03), [P5-T04](#p5-t04) | Boundary tests/calibration |
| FR-VER-3 one batched Ultra entailment call, three verdicts/reasons | [P4-T04](#p4-t04) | Verifier schema/call fixtures |
| FR-VER-4 removal/partial/refusal/>30% one regeneration | [P4-T05](#p4-t05) | Policy table and regeneration audit |
| FR-VER-5 best block or all-chunk-blocks citation fallback | [P4-T06](#p4-t06), [P6-T05](#p6-t05) | Citation resolution/highlight tests |
| FR-VER-6 persist verifier output for audit/eval | [P4-T04](#p4-t04), [P4-T07](#p4-t07), [P4-T08](#p4-t08) | Message/verifier/trace records |
| FR-UI-1 library/upload/progress/delete/collections | [P6-T02](#p6-t02) | Library workflows |
| FR-UI-2 SSE statuses, verified answer only, no answer tokens | [P6-T03](#p6-t03), [P4-T07](#p4-t07) | SSE API/UI ordering tests |
| FR-UI-3 summary/details/numbered document-page-quote sources | [P6-T03](#p6-t03) | Answer layout tests |
| FR-UI-4 chips, PDF page/block highlight, multi-citation chooser | [P6-T04](#p6-t04), [P6-T05](#p6-t05), [P6-T07](#p6-t07) | Interaction tests and 20/20 audit |
| FR-UI-5 partial badges, refusal/failure states | [P6-T03](#p6-t03), [P6-T04](#p6-t04) | Verdict/refusal/failure fixtures |
| FR-UI-6 stored table HTML beside highlighted page | [P6-T06](#p6-t06) | Sanitized table side-panel tests |

### Use cases

| Use case | Owning tasks | Required end-to-end result |
| --- | --- | --- |
| UC1 factual answer + source passage | [P4-T07](#p4-t07), [P6-T03](#p6-t03), [P6-T07](#p6-t07) | Verified factual claim and quote/source visible |
| UC2 table value + exact cell region | [P2-T02](#p2-t02), [P4-T06](#p4-t06), [P6-T06](#p6-t06), [P6-T07](#p6-t07) | Correct table block/page plus HTML/quote |
| UC3 answer across several collection documents | [P3-T02](#p3-t02), [P3-T04](#p3-t04), [P5-T01](#p5-t01), [P6-T07](#p6-t07) | Cross-document evidence with scoped citations |
| UC4 click citation to highlighted PDF region | [P6-T04](#p6-t04), [P6-T05](#p6-t05), [P6-T07](#p6-t07) | Correct page and block, 20/20 sample |
| UC5 clear refusal when sources insufficient | [P3-T05](#p3-t05), [P4-T05](#p4-t05), [P6-T03](#p6-t03), [P6-T07](#p6-t07) | No unsupported answer; measured refusal behavior |

### Eight success metrics

| Metric and initial target | Implementation/measurement owners | Gate/report |
| --- | --- | --- |
| Recall@8 ≥0.90; draft P3 ≥0.85 or diagnosis/fix plan | [P3-T07](#p3-t07), [P3-T08](#p3-t08), [P5-T02](#p5-t02) | P3 retrieval report; P5 baseline |
| MRR ≥0.75 after rerank | [P3-T07](#p3-t07), [P3-T08](#p3-t08), [P5-T02](#p5-t02) | Hand validation; P5 baseline |
| Citation precision ≥0.95 | [P4-T08](#p4-t08), [P5-T02](#p5-t02) | Draft measured; P5 gold/spot checks |
| Citation recall ≥0.98 | [P4-T08](#p4-t08), [P5-T02](#p5-t02) | Factual-claim citation coverage |
| Unsupported claim rate ≤3% | [P4-T05](#p4-t05), [P4-T08](#p4-t08), [P5-T02](#p5-t02) | Removal audit and displayed-claim metric |
| Refusal accuracy ≥0.90 | [P3-T05](#p3-t05), [P4-T05](#p4-t05), [P5-T03](#p5-t03), [P5-T02](#p5-t02) | Unanswerable subset/calibration |
| Answer correctness ≥0.85 | [P5-T02](#p5-t02), [P5-T06](#p5-t06) | Ultra judge, 20% human audit, all disagreements |
| Query latency p95 ≤30 s | [P5-T02](#p5-t02), [P7-T06](#p7-t06) | Full verified-answer traces and 8-QPM load |

### API surface — all 12 endpoints

| Endpoint | Owning task(s) | Notes |
| --- | --- | --- |
| `POST /auth/register` | [P7-T01](#p7-t01) | Real auth replaces development identity |
| `POST /auth/login` | [P7-T01](#p7-t01) | Safe session/credential handling |
| `GET /collections` | [P1-T02](#p1-t02), [P7-T01](#p7-t01) | Per-user scope at release |
| `POST /collections` | [P1-T02](#p1-t02), [P7-T01](#p7-t01) | Includes confidential flag behavior |
| `POST /collections/{id}/documents` | [P1-T02](#p1-t02), [P6-T02](#p6-t02) | Multipart upload returns document ID |
| `GET /documents/{id}` | [P1-T06](#p1-t06), [P6-T02](#p6-t02) | Status and page progress |
| `GET /documents/{id}/file` | [P4-T06](#p4-t06), [P6-T05](#p6-t05), [P7-T01](#p7-t01) | Authorized original for pdf.js |
| `GET /documents/{id}/pages/{n}/blocks` | [P4-T06](#p4-t06), [P6-T05](#p6-t05) | Stored blocks and bboxes |
| `DELETE /documents/{id}` | [P6-T02](#p6-t02), [P7-T01](#p7-t01) | Backend deletion plus explicit UI confirmation |
| `POST /chat` | [P4-T07](#p4-t07), [P6-T03](#p6-t03) | SSE statuses then final verified answer |
| `GET /conversations/{id}/messages` | [P3-T01](#p3-t01), [P7-T01](#p7-t01) | Authorized history/original query |
| `GET /health` | [P7-T03](#p7-t03) | Parser, vector store/Qdrant, PostgreSQL, NIM |

### Data model — all 11 tables

| Table | Owning task(s) | Integrity focus |
| --- | --- | --- |
| `users` | [P1-T01](#p1-t01), [P7-T01](#p7-t01) | ID, email, password hash, created timestamp; safe auth |
| `collections` | [P1-T01](#p1-t01), [P1-T02](#p1-t02) | User ownership, name, confidential flag |
| `documents` | [P1-T01](#p1-t01), [P1-T02](#p1-t02), [P1-T06](#p1-t06) | Collection, filename, SHA-256, page count, language, status/timestamp |
| `pages` | [P1-T01](#p1-t01), [P1-T03](#p1-t03), [P1-T04](#p1-t04) | Geometry, raw output, parse status/timing, unique page order |
| `blocks` | [P1-T01](#p1-t01), [P1-T04](#p1-t04) | Class, normalized/pixel/PDF bboxes, text/HTML/order |
| `chunks` | [P2-T06](#p2-t06), [P2-T03](#p2-t03), [P2-T07](#p2-t07) | Text/embed text, tokens, section/pages, continuation, `tsv` |
| `chunk_blocks` | [P2-T06](#p2-t06), [P2-T08](#p2-t08) | Ordered source-block provenance, no orphans |
| `embed_cache` | [P2-T06](#p2-t06) | Text SHA-256 + model, response-derived dimension/vector reference |
| `conversations` | [P3-T01](#p3-t01) | Collection ownership and created timestamp |
| `messages` | [P3-T01](#p3-t01), [P4-T07](#p4-t07) | Original/rewrite, answer/verifier/trace JSON and timestamps |
| `eval_runs` | [P3-T07](#p3-t07), [P5-T02](#p5-t02) | Config hash, git SHA, metrics JSON, created timestamp |

### Non-functional requirements

| NFR | Owning task(s) | Acceptance focus |
| --- | --- | --- |
| Privacy / no confidential hosted indexing | [P0-T07](#p0-t07), [P1-T02](#p1-t02), [P4-T07](#p4-t07), [P7-T01](#p7-t01), [P7-T05](#p7-t05) | Terms evidence, enforced collection block, README warning |
| Secrets from environment; never logged/browser | [P0-T01](#p0-t01), [P2-T05](#p2-t05), [P6-T01](#p6-t01), [P7-T03](#p7-t03), [P7-T07](#p7-t07) | Bundle/log/API audits and fixture tests |
| Structured observability and per-stage traces | [P1-T06](#p1-t06), [P4-T07](#p4-t07), [P7-T03](#p7-t03) | Trace IDs, latency/call/model/chunk/score data, redaction |
| Restart-safe ingestion; parse outage pauses | [P1-T05](#p1-t05), [P7-T04](#p7-t04) | Worker/service restart and no duplicate proof |
| Versioned reproducibility and eval identities | [P0-T08](#p0-t08), [P3-T07](#p3-t07), [P5-T02](#p5-t02), [P5-T07](#p5-t07) | Models/prompts/thresholds config; config hash/git SHA |
| Compose portability; separate GPU parser | [P7-T04](#p7-t04), [P7-T05](#p7-t05) | Clean start/restart and documented parser script |
| Linux parser; Windows via WSL2 GPU | [P0-T02](#p0-t02), [P7-T04](#p7-t04) | Evidenced Blackwell compatibility and topology |

### Risk register coverage — all eight PRD §16 risks

| Risk | Mitigation owners | Required evidence |
| --- | --- | --- |
| 1. Parser incompatible with RTX 5070 stack | [P0-T02](#p0-t02), [P0-T03](#p0-t03), [P1-T08](#p1-t08) | Smoke results; Docling fallback/hosted endpoint checked if needed |
| 2. Credits/RPM throttle ingestion and queries | [P0-T06](#p0-t06), [P2-T05](#p2-t05), [P2-T06](#p2-t06), [P7-T06](#p7-t06) | Measured burst, batching/cache/token bucket, load ledger |
| 3. Early-access Super VL changes/disappears | [P0-T04](#p0-t04), [P0-T07](#p0-t07), [P0-T08](#p0-t08), [P4-T01](#p4-t01) | Pinned config, named fallback, eval rerun on change |
| 4. Table/scan parser errors propagate | [P0-T03](#p0-t03), [P1-T07](#p1-t07), [P1-T08](#p1-t08), [P2-T02](#p2-t02), [P5-T05](#p5-t05) | Overlays, stored HTML, double/single-pass comparison |
| 5. Block highlight coarser than cited sentence | [P6-T04](#p6-t04), [P6-T05](#p6-t05), [P6-T07](#p6-t07) | Verbatim quote beside correct block highlight |
| 6. Verifier false support/removal | [P4-T04](#p4-t04), [P4-T08](#p4-t08), [P5-T06](#p5-t06) | Quote + entailment checks, removal audit, human adjudication |
| 7. Hindi/Marathi embed/rerank quality gap | [P0-T05](#p0-t05), [P2-T07](#p2-t07), [P3-T08](#p3-t08), [P5-T01](#p5-t01), [P5-T06](#p5-t06) | Preliminary probe and final per-language eval/limits |
| 8. Confidential documents leave machine | [P0-T07](#p0-t07), [P1-T02](#p1-t02), [P7-T01](#p7-t01), [P7-T05](#p7-t05), [P7-T07](#p7-t07) | Collection flag enforcement, privacy docs, release audit |

## Phase progress and dependency map

Update counts only from task records. A gate passes only when its checklist and committed proof both pass.

| Phase | Core progress | Optional | Gate status | Unlock dependency | Gate proof summary |
| --- | ---: | ---: | --- | --- | --- |
| [P0](#p0--environment-and-smoke-tests) | 0/8 done | — | `not_started` | Planning approved | Smoke report, three raw outputs/overlays, limits table, model config |
| [P1](#p1--ingestion-and-parsing) | 0/8 done | — | locked | P0 gate | Ten overlays/JSON, concurrency/VRAM table, retry/manual review |
| [P2](#p2--chunking-and-indexing) | 0/8 done | — | locked | P1 gate | Three chunk dumps, histogram, ten tables, quota/provenance/zero-call |
| [P3](#p3--retrieval) | 0/8 done | — | locked | P2 gate | Draft gold, metrics, hybrid/rerank ablations, draft Recall gate |
| [P4](#p4--generation-and-verification) | 0/8 done | — | locked | P3 gate | Thirty answers, all removals, five refusals, draft quality |
| [P5](#p5--evaluation-and-tuning) | 0/7 done | — | locked | P4 gate | Baseline/eval rows, all ablations/calibration, worst 15, target decisions |
| [P6](#p6--web-ui) | 0/7 done | — | locked | P5 gate | Five use-case recordings, click-position test, 20/20 highlights |
| [P7](#p7--hardening-and-release) | 0/7 done | 0/1 | locked | P6 gate | Clean setup, 8-QPM load, final eval, README-only release |
| **Total** | **0/61 done** | **0/1** | — | — | — |

### Cross-phase critical path

```text
P0 provider/GPU evidence + model config
  → P1 reliable parsing + reviewed block provenance
  → P2 bounded chunks + cached dense/simple lexical indexes
  → P3 scoped hybrid/RRF/rerank + draft retrieval evidence
  → P4 grounded JSON + structural/quote/entailment verification + citations
  → P5 final gold/calibration/ablations/human audit/target decisions
  → P6 verified-answer UI + exact PDF/table highlights
  → P7 auth/privacy/observability/Compose/load/final release audit
```

Within an unlocked phase, respect each task's `Depends` line. No dependency is waived because a later task appears easy or an agent reports success without artifacts.

## Proof-of-work gate matrix

All locations below are **planned until real artifacts are committed**.

| Gate | Required artifacts and acceptance checks | Owning consolidation task |
| --- | --- | --- |
| P0 | `proof/P0/smoke_report.md`; digital/scanned/table raw outputs and three overlays; exact model IDs/request shapes/dimension/limits/rerank route/score observations/reasoning controls; measured 60-call ledger; terms URLs/dates; bounded Hindi/Marathi quality probe; `config/models.yaml`; all six roles respond or fallback recorded | [P0-T08](#p0-t08) |
| P1 | Ten varied overlays and parse JSON; manual text/bbox review; timing/VRAM at concurrency 1/2/4/8 and selected reason; observed parser classes; two-retry/failure/restart/outage proof | [P1-T07](#p1-t07), [P1-T08](#p1-t08) |
| P2 | Three-document chunk dump; token histogram; ten table chunks with HTML; quota usage; every chunk under limit and mapped to blocks/bboxes; identical reingestion zero embedding calls | [P2-T08](#p2-t08) |
| P3 | Versioned draft gold with answer/page/block labels; LLM-free retrieval metrics; no-hybrid/no-rerank ablation table; draft Recall@8 ≥0.85 or diagnosis/fix plan | [P3-T08](#p3-t08) |
| P4 | Thirty recorded answers with verifier output; every removed claim/reason; five refusals; measured citation precision/unsupported claim rate; no displayed failed-quote claim; verified-only summary | [P4-T08](#p4-t08) |
| P5 | `proof/P5/baseline.md` with all eight metrics/targets; eval rows/config/git identities; final gold; all four ablations; two threshold calibrations; judge + 20% audit/all disagreements; Hindi/Marathi results; worst 15; every miss decided | [P5-T07](#p5-t07) |
| P6 | UC1–UC5 recordings; Playwright citation-click page/block/position assertion; sanitized table side panel; 20/20 correct sampled highlights | [P6-T07](#p6-t07) |
| P7 | Clean-machine setup log; controlled 8-QPM load; final eval; README-only fresh-clone verified answer; authorization/privacy/secret/proof audit | [P7-T07](#p7-t07) |

## Completion and change-control audit

Run this audit before marking any phase or release complete. Compare code and proof artifacts against this checklist, not an agent summary.

### Per-task audit

- [ ] Task ID matches `P[0-7]-T[0-9]{2}` and is unique; status is one of the five allowed values; owner and dependencies are present.
- [ ] Every dependency is satisfied and every referenced decision anchor exists; no dependency cycle was introduced.
- [ ] Every `Proof (planned)` path uses the task's own `proof/Pn/` directory unless deliberately linking versioned config/gold source.
- [ ] `done` tasks have real committed proof at every required destination, passing commands/results, and reviewer approval; links are not placeholders.
- [ ] Offline tests use recorded fixtures and make zero NIM calls; live smoke, burst, judge, and load procedures have separate authorization and ledgers.
- [ ] Hosted IDs, dimensions, request parameters, quotas, parser classes, and score ranges trace to observed evidence; no remembered value silently became config.

### Requirements and evidence audit

- [ ] All 42 FR rows, five use cases, eight metrics, 12 endpoints, 11 tables, seven NFRs, and eight risks retain an owning done task and passing proof.
- [ ] Exact values remain intact: RGB/150 dpi, 1664 × 2048, exact parse prompt, `max_new_tokens=8744`, temperature 0, `top_k=1`, repetition 1.1, special tokens false, two retries.
- [ ] Chunk values remain intact: 400–800 tokens/~12% overlap, tables >1,200 split by rows/repeated headers, measured embed limit, text+model cache, response-derived dimension, `simple` tsvector.
- [ ] Retrieval values remain intact: dense 40 + lexical 40, RRF 60, rerank 30→8, C1–C8, continuation-only neighbors, configured budget, labeled abstention calibration.
- [ ] Verification values remain intact: quotes ≤25 words, NFKC/whitespace/case, initial fuzzy 92 pending calibration, one batched entailment call, three verdicts, unsupported removal, partial badge, all-removed refusal, >30% one regeneration/recheck.
- [ ] Answer JSON and verifier JSON match PRD §10; one JSON repair maximum; summary only from surviving verified claims; no answer-token streaming or pre-verification answer.
- [ ] Final gold has 60–100 items, required approximate category mix, ≥15% unanswerable, ≥10 Hindi/Marathi, expected answer/page/block; judge audits 20% and every disagreement.
- [ ] All four ablations ran; verifier-off exists only in evaluation; final targets were met or each miss has cause, user impact, decision, and follow-up.
- [ ] P0–P7 proof directories contain gate artifacts, not merely reports describing future work; release includes clean-machine and final-eval evidence.

### Decision/change audit

- [ ] Open decisions are resolved at their owning gate: D-P0-01–06 at P0, D-P1-01–03 at P1, D-P5-01–03 at P5; decision history records evidence and approver.
- [ ] Every model, prompt, threshold, or chunking change after initial gate selection has an eval run, config hash, and git SHA; initial selections cite gate proof/config/version identifiers.
- [ ] Initial targets changed only at P5 with evidence and Atharva approval. Later target changes formally reopen P5 with new evidence; post-P5 remediation alone does not authorize target changes.
- [ ] Qdrant remains default unless P0 dimension evidence approved pgvector; production abstention was not guessed; quote threshold 92 was calibrated; duplicate behavior was selected before API freeze.
- [ ] Confidential collection flag blocks hosted indexing/query from P1 onward until a local path exists; no credentials or provider secrets appear in logs/browser artifacts.

### Release scope audit

- [ ] No multi-tenant SaaS, billing, collaboration, web search, agents, model fine-tuning, or word-level highlighting entered v1 core scope.
- [ ] PDF/PNG/JPG are core input formats. DOCX/PPTX conversion, page-image retrieval, and answer cache remain optional independently evaluated `P7-T08` experiments.
- [ ] `P7-T08` does not block release, bypass verification/auth/privacy, or substitute for any missing core gate artifact.
- [ ] Final release decision cites actual code, eval, clean-machine run, and proof artifacts. Any failure reopens the owning task rather than being narrated away.
