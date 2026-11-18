# CiteRAG Engineering Decisions

Owner: Atharva  
Source: `PRD.md` v1.0, dated 15 Nov 2026  
Document date: 18 Nov 2026  
Status: Approved by owner on 18 Nov 2026

## 1. Purpose and authority

This document turns the PRD into explicit engineering decisions and records choices that the PRD leaves open. `TASKS.md` is the execution view; this document is the decision and rationale view.

Precedence, highest first:

1. Explicit owner decisions recorded after review.
2. `PRD.md` requirements and phase gates.
3. Accepted decisions in this document.
4. Implementation details in `TASKS.md`.

A task, agent summary, or implementation convenience cannot silently override a higher-precedence source. Conflicts stop the affected task for a decision update.

Every implementation task in `TASKS.md` cites its applicable decision IDs and PRD requirements. Every phase gate cites the pending decisions it must close.

### Status vocabulary

- **Accepted (PRD):** directly required by the PRD; changing it requires a recorded PRD decision.
- **Proposed:** recommended resolution of an implementation gap; becomes accepted only after owner review.
- **Pending gate:** cannot be finalized until the named phase supplies evidence.
- **Superseded:** retained for history but no longer operative.

After the owner approves this document, approved **Proposed** entries are treated as accepted working decisions. Any entry still marked **Pending gate** remains unresolved.

**Approval record:** On 18 Nov 2026, the owner approved all entries marked **Accepted (owner)** as working decisions. Entries marked **Pending gate** still require their specified evidence and may not be treated as resolved.

### Change control

Every material change records:

- Decision ID and prior status.
- Reason and supporting evidence.
- Alternatives considered.
- Affected requirements, tasks, tests, and proof artifacts.
- Migration or rollback impact.
- Evaluation rerun requirements.

Success targets may be recalibrated only at P5, with the original target, new target, measured result, and reason retained. Prompt, threshold, model, or chunking changes require an eval run. Never overwrite an earlier decision record to hide a reversal; mark it superseded and add its replacement.

## 2. Decision index

| ID | Decision | Status | Resolution point |
| --- | --- | --- | --- |
| D-001 | P0–P7 gates govern delivery order | Accepted (PRD) | Every phase gate |
| D-002 | Use one modular monorepo with clear service boundaries | Accepted (PRD) | P0 scaffold |
| D-003 | Keep hosted-model calls behind one Python NIM gateway | Accepted (PRD) | P0–P2 |
| D-004 | Pin model behavior in versioned configuration, not source literals | Accepted (PRD) | P0 |
| D-005 | Use PostgreSQL as the system of record | Accepted (PRD) | P1 |
| D-006 | Use a private local file store for original uploads | Accepted (owner) | P1 |
| D-007 | Select Qdrant or pgvector from measured embedding constraints | Pending gate | P0 |
| D-008 | Run the specified parser locally; isolate parse failures by page | Accepted (PRD) | P0–P1 |
| D-009 | Use Docling only if the primary parser fails the P0 gate | Pending gate | P0 |
| D-010 | Preserve both render-pixel and PDF-point coordinates | Accepted (PRD) | P1 |
| D-011 | Reject exact duplicates within a collection | Accepted (owner) | P1 |
| D-012 | Chunk deterministically from typed blocks | Accepted (PRD) | P2 |
| D-013 | Link inferred cross-page continuations without merging provenance | Accepted (PRD) | P2 |
| D-014 | Key embedding cache entries by model and text hash | Accepted (owner) | P2 |
| D-015 | Keep cached vectors independent of document lifetime | Accepted (owner) | P2 |
| D-016 | Use filtered hybrid retrieval, RRF 60, rerank 30-to-8 | Accepted (PRD) | P3 |
| D-017 | Rewrite only conversational or underspecified queries | Accepted (PRD) | P3 |
| D-018 | Implement abstention early; calibrate its release threshold at P5 | Accepted (owner) | P3/P5 |
| D-019 | Assemble labeled, budgeted context with linked neighbors only | Accepted (PRD) | P3 |
| D-020 | Use strict answer JSON and one repair attempt | Accepted (PRD) | P4 |
| D-021 | Treat fuzzy quote matching as locating evidence, not permission to alter quotes | Accepted (owner) | P4 |
| D-022 | Make the first chunk ID the primary quote anchor for multi-chunk claims | Accepted (owner) | P4 |
| D-023 | Remove unsupported claims; badge partial claims; regenerate at most once | Accepted (PRD) | P4 |
| D-024 | Construct the displayed summary only from surviving claims | Accepted (owner) | P4 |
| D-025 | Resolve citations back to source blocks after verification | Accepted (PRD) | P4 |
| D-026 | Send answer text only after verification over a terminal-safe SSE contract | Accepted (owner) | P4/P6 |
| D-027 | Derive viewer highlights from PDF points and the active viewport transform | Accepted (owner) | P6 |
| D-028 | Treat uploads and generated table HTML as untrusted content | Accepted (owner) | P1/P6 |
| D-029 | Default confidential collections to blocked hosted indexing | Accepted (owner) | P1/P7 |
| D-030 | Enforce ownership server-side on every object and retrieval filter | Accepted (owner) | P7 |
| D-031 | Make deletion an idempotent, recoverable cross-store operation | Accepted (owner) | P1/P2/P7 |
| D-032 | Use explicit language hints rather than unreliable script-only detection | Accepted (owner) | P1/P2 |
| D-033 | Correlate logs and traces without logging secrets or sensitive content | Accepted (PRD) | P0–P7 |
| D-034 | Keep tests quota-free by default and evaluate from stored traces | Accepted (PRD) | P0–P7 |
| D-035 | Keep stretch features outside the required v1 critical path | Accepted (PRD) | P7 |

## 3. Delivery and repository

### D-001 — Phase gates govern delivery order

- **Status:** Accepted (PRD sections 14–15).
- **Decision:** Execute P0 through P7 in order. A phase closes only when its acceptance criteria pass and its proof artifacts exist under `proof/Pn/`. Later-phase tasks remain blocked until the prior gate closes.
- **Consequences:** Exploratory spikes may inform an open decision, but they do not count as completing a later-phase task. A gate cannot be waived by an agent summary.
- **Repository prerequisite:** The current directory is not a git repository. Initialize version control as a P0 task; phases requiring committed proof cannot close until commits exist.

### D-002 — One modular monorepo with clear service boundaries

- **Status:** Accepted (PRD sections 5 and 18).
- **Decision:** Treat the directory containing `PRD.md`, `DECISION.md`, and `TASKS.md` as the repository root. Place `apps/`, `packages/`, `config/`, and `proof/` directly beneath it; do not create a redundant nested `citerag/citerag` tree.
- **Boundaries:**
  - `apps/api`: HTTP contracts, auth, query orchestration, verification, and the NIM gateway.
  - `apps/worker`: Celery orchestration for rendering, parsing, chunking, and indexing.
  - `apps/parse_service`: local parser startup and client wrapper.
  - `apps/web`: Next.js UI and PDF viewer.
  - `packages/chunking`: deterministic block-to-chunk logic with no network calls.
  - `packages/eval`: gold data, metrics, ablations, and report generation.
- **Rule:** Shared behavior belongs in an explicit Python package or typed web module, not copied between services. Web code must not import server secrets or Python service internals.

### D-003 — One NIM gateway for hosted-model calls

- **Status:** Accepted (PRD sections 5–6 and 11).
- **Decision:** API, worker, and eval code call a shared Python gateway rather than constructing vendor requests independently. The gateway owns request schemas, timeouts, per-model token buckets, retries with exponential backoff and jitter, circuit breakers, fallbacks, usage accounting, response validation, and cache integration.
- **Failure behavior:** Retry only transient failures and only within configured budgets. Never retry non-idempotent operations blindly. Return typed errors to the caller so ingestion can pause and chat can end with an explicit failure event.
- **Observability:** Record model ID, sanitized request metadata, latency, retry count, fallback use, and call count under the request or job trace ID. Do not log API keys.
- **Alternative rejected:** Direct SDK calls in each stage would scatter quota behavior and make fixture-based testing inconsistent.

### D-004 — Model behavior lives in versioned configuration

- **Status:** Accepted for the mechanism (PRD section 6); exact values are **Pending P0**.
- **Decision:** `config/models.yaml` records exact model IDs, routes, request parameters, context/input limits, reasoning controls, fallbacks, and measured quota settings after real endpoint smoke tests. Retrieval and verification thresholds live in versioned YAML. Prompts live under `config/prompts/`.
- **Prohibition:** Do not hardcode an assumed endpoint ID, embedding dimension, rerank score range, input-type flag, or reasoning parameter from memory.
- **Evaluation:** Hash the effective configuration and store that hash, model IDs, and git SHA with every eval run.

## 4. Storage and consistency

### D-005 — PostgreSQL is the system of record

- **Status:** Accepted (PRD section 8).
- **Decision:** PostgreSQL owns users, collections, documents, pages, blocks, chunks, provenance, conversations, verifier output, traces, and eval metadata. Qdrant, if selected, is a rebuildable retrieval index rather than the sole copy of chunk text or citation metadata.
- **Transactions:** Use database transactions for metadata transitions. Vector writes occur through an idempotent indexing step with a durable indexing status; a crash between stores is repaired by retrying that step, not by pretending the transaction was atomic.
- **Migrations:** Use versioned Alembic migrations and explicit foreign keys, uniqueness constraints, and indexes. Add ownership and confidentiality fields required by D-029 and D-030 rather than keeping them only in application state.

### D-006 — Originals use a private local file store

- **Status:** Accepted (owner).
- **Decision:** Store uploaded originals on a persistent local volume outside the web public directory. Keep a database-managed storage key, original filename, media type, byte count, and SHA-256. Serve files only through the authorized document-file endpoint.
- **Alternative considered:** PostgreSQL large objects simplify backups but make large-file streaming and pdf.js range access less direct. Public static storage is rejected because it bypasses auth.
- **Deployment:** Development and v1 production use the same storage abstraction so a future object-store backend does not change ingestion or viewer contracts.

### D-007 — Vector store selection remains a P0 gate

- **Status:** Pending gate.
- **Decision:** Qdrant is the provisional implementation. Measure the hosted embedding dimension and input limit, verify the current pgvector index constraint for the intended index type, and confirm filtering and operational needs before choosing.
- **Choose pgvector only if:** the measured dimension is supported by the selected index, required collection/document filters are efficient, expected local corpus size fits the deployment, and the simplification does not weaken retrieval evaluation.
- **Otherwise:** retain Qdrant.
- **Record:** Store the decision, measured values, compared constraints, and migration impact in `proof/P0/smoke_report.md` and update this entry. Do not silently switch stores mid-phase.

### D-014 — Embedding cache identity includes the model

- **Status:** Accepted (owner) refinement of PRD FR-IDX-4.
- **Decision:** Look up cache entries by `(text_sha256, model)` and validate `vector_dim` before reuse. The cached text is the exact `embed_text`, including section path and any required endpoint input-type handling. Namespace or invalidate entries when request semantics change.
- **Reason:** A text-only key can return an incompatible vector after a model or encoding change.
- **Acceptance:** Re-ingesting unchanged content with unchanged model semantics spends zero embedding calls; changing models cannot reuse an incompatible vector.

### D-015 — Cached vectors outlive individual documents

- **Status:** Accepted (owner).
- **Decision:** `embed_cache.vector_ref` points to an immutable vector in a model/dimension-specific cache collection or table, separate from per-document retrieval points. Document deletion removes retrieval points but not the cache entry. Cache entries are never dangling references to a deleted document's point.
- **Alternative rejected:** Pointing cache rows at ordinary document vectors makes deletion and re-ingestion order-dependent.
- **Operational rule:** Cache cleanup is an explicit maintenance operation, not a side effect of document deletion. Any cleanup must preserve referential integrity.

### D-031 — Deletion is idempotent and recoverable

- **Status:** Accepted (owner).
- **Decision:** Mark the document deleting, remove or disable its retrieval points, delete dependent metadata and the stored original through retryable steps, then mark deletion complete. Repeated DELETE requests are safe. Ownership is checked before any mutation.
- **Failure behavior:** A partially deleted document cannot remain searchable or appear as a healthy document. A background retry or administrative retry endpoint can finish interrupted cleanup.
- **Cache exception:** Embedding cache entries follow D-015 and are not document-owned.

## 5. Ingestion and provenance

### D-008 — Use the specified local parser and isolate page failures

- **Status:** Accepted (PRD sections 6–7 and 12).
- **Decision:** Serve Nemotron-3.5-Parse locally through vLLM on Linux or WSL2 with GPU passthrough. Use the exact task prompt, `max_new_tokens=8744`, temperature 0, `top_k=1`, `repetition_penalty=1.1`, and `skip_special_tokens=false`. Start with double-pass parsing and the `guarded` merge policy when duplicate table hypotheses pollute the index.
- **Page policy:** Retry a failed page twice, then mark only that page failed. Preserve raw output and timing for successful and failed attempts where available. Jobs resume from the last good page.
- **Outage policy:** A parse-service outage pauses affected jobs with a visible retrying/paused state; it does not convert every queued page into a permanent failure.
- **Capacity:** Benchmark concurrency 1, 2, 4, and 8 in P1. Start at 4 only where safe; select the final value from throughput, latency, VRAM, and failure evidence.

### D-009 — Docling is conditional, not a parallel default

- **Status:** Pending P0.
- **Decision:** Activate Docling only if Nemotron-3.5-Parse cannot run on the target GPU/OS stack or cannot satisfy the P0 smoke gate. Record the failure evidence, changed block schema, bbox capabilities, and any requirement gaps before P1 proceeds.
- **Compatibility rule:** A fallback must emit the same internal page/block contract or use an explicit adapter. It must not silently drop raw output, classes, or coordinates required for citations.

### D-010 — Preserve both coordinate systems

- **Status:** Accepted (PRD FR-ING-2 through FR-ING-5).
- **Decision:** Render at 150 dpi, downscale proportionally only when needed to fit 1664×2048, and persist actual render width, height, dpi, and scale. Keep normalized, render-pixel, and PDF-point bboxes on every block.
- **Conversion:** Account for the actual downscale factor when converting pixels to PDF points with `pixels * 72 / render_dpi`. Never assume A4/Letter dimensions or that no downscale occurred.
- **Validation:** Overlay tests cover portrait, landscape, scanned, table-heavy, and downscaled pages. Coordinates remain block-level; word-level highlighting is out of scope.

### D-011 — Reject exact duplicates within a collection

- **Status:** Accepted (owner) resolution of PRD FR-ING-1's reject-or-link choice.
- **Decision:** Enforce a uniqueness constraint on `(collection_id, sha256)` for active documents and return the existing document with an explicit `duplicate=true` response. Do not create a second parse/index job. The same file may exist in different collections, where it receives separate collection-scoped retrieval points but may share embedding cache entries.
- **Alternative considered:** Linking multiple document rows to one indexed representation saves storage but complicates deletion, status, permissions, and provenance.
- **Restart behavior:** Hash calculation and document reservation are idempotent so a retried multipart upload cannot create duplicate active rows.

### D-028 — Uploads and generated table HTML are untrusted

- **Status:** Accepted (owner) security implementation of the PRD privacy and input requirements.
- **Decision:** Enforce configurable byte caps, inspect file signatures as well as extensions/MIME declarations, accept only PDF/PNG/JPG in v1, generate safe storage names, and never execute uploaded content. Return appropriate nosniff and content-disposition headers; do not expose filesystem paths.
- **Viewer:** Parse PDFs in pdf.js rather than embedding arbitrary uploaded HTML. Sanitize stored table HTML with a strict allowlist before rendering; no scripts, event handlers, remote resources, or arbitrary styles.
- **Error behavior:** Invalid or unsupported uploads fail before a Celery job is created, with a safe user-facing reason and no retained partial file.

### D-029 — Confidential collections default to blocked hosted indexing

- **Status:** Accepted (owner) implementation of PRD sections 12 and 16.
- **Decision:** Add a collection-level `confidential` flag defaulting to `true`. Upload and local storage may proceed, but any stage that sends chunk text, questions, or derived content to a hosted endpoint is blocked until the owner explicitly marks the collection non-confidential and acknowledges the privacy notice.
- **Query rule:** Chat is also blocked for confidential collections because retrieval and generation use hosted models. A local-model path is not implied by this flag and remains future work.
- **Audit:** Record the flag change and timestamp without recording document contents. The README states that hosted free-tier inputs may be recorded subject to terms confirmed in P0.

### D-032 — Language metadata uses explicit hints

- **Status:** Accepted (owner).
- **Decision:** Accept a document `lang_hint` for English, Hindi, Marathi, or unknown. Propagate the best available value to chunk payloads, using `und` when unknown. Do not claim to distinguish Hindi from Marathi using Devanagari-script detection alone.
- **Search:** Use PostgreSQL's `simple` full-text configuration as required by the PRD. Language metadata supports filtering and evaluation, not silent exclusion of unknown-language chunks.
- **Evaluation:** Gold-set language labels are manually verified; Hindi and Marathi metrics are reported separately.

## 6. Chunking and indexing

### D-012 — Chunk deterministically from typed blocks

- **Status:** Accepted (PRD FR-CHK-1 through FR-CHK-9).
- **Decision:** Build chunks from ordered parsed blocks and their semantic classes. Record actual class names from P1 output before finalizing class mappings. Exclude headers, footers, and page numbers only from indexing; retain them in `blocks`.
- **Text:** Target 400–800 embedding-tokenizer tokens with approximately 12% overlap. Prefer block and paragraph boundaries; split an oversized block only when unavoidable.
- **Tables:** Keep one table per chunk up to 1,200 tokens. Larger tables split by rows and repeat headers. Store sanitized display HTML and flattened row-wise text for embedding and lexical search.
- **Charts:** Use one chunk containing extracted chart data and caption. Do not invent values missing from parser output.
- **Provenance:** Every chunk retains ordered block links, pages, and bboxes. Token counts use the actual embedding tokenizer when available; otherwise use one documented proxy with a conservative margin below the measured input limit.
- **Testing:** Golden chunk snapshots, boundary tests, oversized-block/table tests, provenance invariants, and multilingual samples run without hosted calls.

### D-013 — Continuations link chunks without erasing provenance

- **Status:** Accepted (PRD FR-CHK-7).
- **Decision:** Use deterministic heuristics to link likely cross-page paragraph/table continuations with `continues_from`. Preserve each chunk's own source blocks and page ranges. Evaluate the heuristic in P2 before relying on it in retrieval.
- **Context rule:** P3 may add a linked neighbor even when it was not independently retrieved, but may not add arbitrary adjacent chunks. Added neighbors still consume the context token budget and retain their own citation labels and provenance.
- **Failure rule:** A low-confidence continuation remains unlinked; a false merge is worse than retrieving two independently citable chunks.

## 7. Retrieval and context

### D-016 — Filtered hybrid retrieval is fixed; its calibration is not

- **Status:** Accepted for algorithm and counts (PRD FR-RET-2 through FR-RET-6); score behavior is measured in P0/P3.
- **Decision:** Run dense top-40 and lexical top-40 searches with identical collection/document authorization filters. Fuse with RRF constant 60, rerank the first 30 merged candidates, and retain eight.
- **Data contract:** Persist dense rank/score, lexical rank/score, fused rank/score, rerank score, final rank, and model/config identifiers in traces so retrieval can be evaluated without another LLM call.
- **Security:** Optional `doc_ids` must be a subset of documents the user can access within the selected collection. Filters apply before ranking, not after results are returned.
- **Ablations:** P3 compares no-rerank and no-hybrid variants on the same draft gold set.

### D-017 — Query rewriting is conditional

- **Status:** Accepted (PRD section 6 and FR-RET-1).
- **Decision:** Rewrite only when prior turns supply necessary context or a deterministic underspecification check indicates need. Otherwise use the original question directly and avoid a hosted call. Always retain the original question for display and audit.
- **Contract:** The rewritten query is standalone, short, low-temperature, and cannot add facts or broaden the selected document scope. If rewriting fails, use the original query when safe and record the fallback; do not fabricate a rewrite.
- **Evaluation:** Include follow-up questions in the gold set so unnecessary or incorrect rewrites are visible in retrieval metrics.

### D-018 — Abstention ships as a mechanism before its final threshold

- **Status:** Accepted (owner) rollout resolving the P3 mechanism/P5 calibration sequence.
- **Decision:** Implement and test the abstention gate in P3 with a nullable configured threshold. Until P5 calibration, development traces label it `uncalibrated`; no guessed threshold is represented as production-ready. Unit and integration tests use explicit fixture thresholds to exercise both refusal and pass-through branches.
- **P5 release rule:** Calibrate on the final eval set using measured rerank scores and refusal/coverage trade-offs. Store the selected threshold, score semantics, dataset/config hashes, and resulting refusal accuracy.
- **Failure rule:** Missing or incomparable rerank scores cannot be interpreted as confidence. Return an explicit unavailable/failure state unless the configured development policy deliberately leaves the gate disabled.

### D-019 — Context is labeled, bounded, and provenance-safe

- **Status:** Accepted (PRD FR-RET-6).
- **Decision:** Label final chunks C1–C8 in stable rank order. Add only `continues_from`-linked neighbors under a configured token budget, with deterministic truncation that never silently removes the primary evidence for a retained label.
- **Prompt input:** Supply each labeled chunk's text and stable internal mapping, not arbitrary UI citation numbers. Primary reranked chunks use C1–C8; linked neighbors receive C9 onward in primary-rank order and count toward the same context budget. Keep section paths in embedded text only; displayed source text remains the original chunk text.
- **Trace:** Record included, truncated, and neighbor-added chunk IDs plus token counts so citation validity can be checked against the exact model input.

## 8. Generation, verification, and citations

### D-020 — Strict answer JSON with one repair attempt

- **Status:** Accepted (PRD section 10 and FR-GEN-1 through FR-GEN-3).
- **Decision:** Use the PRD answer schema, temperature at or near zero, reasoning off for the answer model, and labeled context only. Every factual sentence is a `claim`; `connective` text may contain no facts. Each generated quote is at most 25 words.
- **Repair:** Schema/JSON failure permits exactly one automatic repair call using the invalid output and validation errors. A second failure returns a failure state, not a best-effort prose answer.
- **Structural gate:** Reject citations whose IDs were absent from the exact supplied context. Validate types, paragraph/sentence structure, abstention consistency, and quote length before entailment.

### D-021 — Fuzzy matching locates evidence; displayed quotes remain verbatim

- **Status:** Accepted (owner) reconciliation of PRD G1, FR-GEN-3, and FR-VER-2.
- **Decision:** Normalize model quote and candidate source with Unicode NFKC, whitespace, and case normalization, then use the configured fuzzy partial-ratio threshold (default 92) to locate a candidate source span. The UI must display an exact span copied from stored source text, not the model's possibly paraphrased quote.
- **Acceptance:** Preserve the original generated quote, normalized match score, matched source span, and block mapping in verifier output. A score below threshold or failure to recover an exact source span of at most 25 words marks the claim unsupported. If an exact span exists but does not identify one unique block, citation resolution follows D-025's all-blocks fallback rather than discarding an otherwise supported claim. For PNG/JPG sources, return pixel bboxes against actual stored render dimensions alongside logical PDF-point coordinates; P6 uses the pixel boxes for image overlays.
- **Rationale:** The fuzzy threshold tolerates formatting/model noise without silently presenting a near-quote as verbatim. A threshold pass alone is not enough when no exact source span can be recovered.

### D-022 — The first chunk ID anchors a multi-chunk claim's quote

- **Status:** Accepted (owner) interpretation of the PRD's single `quote` plus multiple `chunk_ids` schema.
- **Decision:** `chunk_ids[0]` is the primary evidence chunk and must contain the quote. Remaining IDs are supplementary evidence used in the entailment check. Use multiple IDs only when their combined evidence supports the claim; tangential chunks are not valid citations. All IDs must belong to the supplied context, and the verifier evaluates the claim against their combined evidence.
- **Resolution:** Resolve the primary citation by quote to the best block. For supplementary chunks, return their linked source blocks; if primary quote matching cannot select one block, return all blocks of the primary chunk as required by FR-VER-5.
- **Presentation:** The inline claim opens a chooser when multiple citations exist. Every displayed source quote is copied verbatim from its stored chunk. Persist primary versus supplementary roles in the resolved response.
- **Alternative considered:** Replacing the PRD schema with a citation-object array would be cleaner for multiple independent quotes but requires a PRD schema change; it is not adopted silently.

### D-023 — Verification policy is fail-closed for unsupported claims

- **Status:** Accepted (PRD FR-VER-1 through FR-VER-6).
- **Decision:** Run structural checks, quote checks, and one batched entailment call. Supported claims remain; partial claims remain with visible badges and reasons; unsupported claims are removed. If all factual claims are removed, refuse.
- **Regeneration:** If more than 30% of factual claims are removed, regenerate once with a stricter prompt and rerun all checks. There are at most two generation calls: the initial call and one verification-triggered regeneration. Each generation call that returns malformed or schema-invalid JSON may trigger one repair call; a failed repair ends that answer path. A repair call does not consume the verification-triggered regeneration allowance.
- **Connectives:** If a supposed connective contains a new fact, reclassify and verify it or remove it; it cannot smuggle unsupported facts into the answer.
- **Verifier outage:** Do not show an unverified answer. Persist the failed state and trace, emit a terminal error, and permit an explicit user retry.
- **Audit:** Persist all verdicts, reasons, removals, match scores, regenerated output, and final displayed claim IDs.

### D-024 — Displayed summary derives only from surviving claims

- **Status:** Accepted (owner) implementation of PRD section 10's summary rule.
- **Decision:** Treat the model's original summary as untrusted draft content. After verification and any regeneration, construct the displayed summary by concatenating at most the first three surviving claim sentences in original order, omitting connectives and retaining each claim's citations and partial badges. Do not introduce another unverified summary-generation call.
- **Fallback:** If no factual claims survive, return a refusal rather than a transitional or unsupported summary. The detailed explanation retains all surviving claims even when the summary contains only the first three.
- **Audit:** Keep the original answer JSON and record which surviving claim IDs formed the displayed summary.

### D-025 — Citation resolution occurs after verification

- **Status:** Accepted (PRD FR-VER-5).
- **Decision:** Resolve only surviving claims. Match the verified source span against the cited chunk's ordered blocks. Select one block only when the match identifies a unique best block; if the span crosses blocks, candidates tie, or no single block matches, return every block of the chunk as required by FR-VER-5. Return document ID, page, PDF-point bbox, source quote, chunk ID, and primary/supplementary role.
- **Invariant:** No response citation may lack a document, page, block-level region, and verbatim source quote. Table citations additionally expose the stored sanitized table HTML.
- **Failure:** Missing/deleted provenance invalidates the affected citation; do not render a guessed page or highlight.

### D-026 — SSE has explicit terminal semantics and no answer-token streaming

- **Status:** Accepted (owner) API detail implementing PRD FR-UI-2 and the `/chat` contract.
- **Decision:** Emit stage events for rewriting, retrieving, reranking, answering, and verifying, followed by exactly one terminal `answer`, `refusal`, or `error` event. Include event ID, trace ID, stage, and safe status metadata. Answer text appears only in the verified terminal payload.
- **Reliability:** Use heartbeats for long-running calls, bounded server timeouts, and client disconnect handling. A disconnect may cancel work only if persistence and retry semantics remain consistent; otherwise finish and persist for later retrieval.
- **Persistence:** Save the user message early enough to correlate failures, but save/display the assistant answer only after final verification. Do not emit raw stack traces, prompts, secrets, or removed claims to the browser.

## 9. Frontend and API

### D-027 — Highlights use stored PDF points and the live viewport transform

- **Status:** Accepted (owner) implementation detail for PRD FR-UI-4 and the P6 gate.
- **Decision:** pdf.js owns page rendering. Convert stored PDF-point bboxes through the same page viewport transform used for the displayed page, accounting for origin, rotation, scale, and device-independent CSS coordinates. Recompute overlays on page render, zoom, resize, and rotation.
- **Navigation:** A citation selects document, page, and block IDs, waits for that page to render, then positions the highlight and scrolls it into view. Multiple citations open a chooser before navigation.
- **Verification:** Playwright compares overlay geometry with pdf.js block expectations at multiple zoom levels and on downscaled source documents. P6 requires 20/20 sampled citations to land correctly.

### D-030 — Authorization is enforced on the server

- **Status:** Accepted (owner) implementation detail for PRD auth and per-user collection requirements.
- **Decision:** Use Argon2id password hashing and HTTP-only, Secure, SameSite-appropriate session cookies backed by revocable server-side sessions. Add an `auth_sessions` table for opaque session-token hashes, user ID, expiry, revocation, and creation metadata. Add explicit ownership relationships and query every collection, document, conversation, file, block, and chat operation through the authenticated user scope.
- **Development sequence:** P0–P6 may use a loopback-only development identity to match the PRD's P7 auth phase. Never expose those unauthenticated stages on a non-loopback interface. P7 release requires registration/login, logout/session revocation, ownership tests, and secure cookie configuration.
- **Retrieval:** Authorization filters are part of collection/document selection before dense, lexical, rerank, file, and citation-resolution operations.
- **Alternative rejected:** Browser-held bearer tokens increase XSS exposure and complicate revocation for this single-user local application.

## 10. Reliability, observability, and evaluation

### D-033 — Correlate operations without leaking sensitive data

- **Status:** Accepted (PRD section 12), with proposed implementation detail.
- **Decision:** Emit structured JSON logs with trace ID, job ID, document/conversation ID, stage, outcome, latency, retry/fallback count, and model/config ID where applicable. Store per-query stage timings, call counts, model IDs, and retrieval scores in `trace_json`.
- **Redaction:** Never log API keys, password hashes, session tokens, authorization headers, or raw multipart data. Content logging is off by default for confidential collections; required raw parser outputs and eval traces remain protected local artifacts with documented sensitivity.
- **Health:** `/health` reports PostgreSQL, selected vector store, Redis/worker, parse service, and NIM reachability without making excessive paid calls. Distinguish liveness from readiness and degraded dependencies.
- **Metrics:** Track ingestion stage durations, page failures, queue wait, hosted quota use, per-query latency, verification removals, refusals, and fallbacks.

### D-034 — Tests are quota-free by default; eval is evidence-driven

- **Status:** Accepted (PRD sections 4, 11, 13, and 15).
- **Decision:** Unit and CI tests use local fixtures and recorded hosted responses. Live NIM smoke/rate tests run only as explicit P0 or diagnostic commands with visible budgets. No normal test command consumes hosted quota.
- **Required unit coverage:** Chunking, bbox conversion, RRF, JSON validation/repair, quote/source-span matching, citation resolution, continuation linking, cache identity, authorization filters, and verifier removal/regeneration policy.
- **Integration coverage:** Upload-to-index resume/idempotency, cross-store failure recovery, retrieval filters, SSE terminal behavior, and recorded end-to-end query fixtures.
- **Evaluation:** Build the 60–100-question gold set with required category/language proportions. Compute retrieval metrics from stored traces; use the specified judge with a 20% human audit and review every disagreement. Run baseline ablations and retain every `eval_runs` row.
- **Gate honesty:** A missed target is reported with cause and decision, never removed from the report. P5 is the only phase that may recalibrate targets, and the original values remain visible.

### D-035 — Stretch features do not block v1

- **Status:** Accepted (PRD sections 2 and 14).
- **Decision:** DOCX/PPTX conversion, page-image retrieval, multimodal embedding/reranking, and answer caching are optional P7 stretch tasks. They require separate decisions, tests, privacy review, and eval evidence before activation.
- **Rule:** No stretch task may delay clean-machine setup, required auth/privacy hardening, the 8-questions-per-minute load test, or final evaluation. Disabled stretch configuration must have no effect on the v1 path.

## 11. Cross-stage failure policy

| Failure | Required behavior | User-visible result |
| --- | --- | --- |
| Unsupported/oversized upload | Reject before job creation; remove partial file | Safe validation error |
| Duplicate in collection | Return existing document; no new job | Duplicate notice linked to existing item |
| Transient page parse error | Retry the page twice with bounded backoff | Page progress shows retrying |
| Page still failing | Mark page failed; continue other pages | Partial/failed-page state with counts |
| Parse service unavailable | Pause/resume affected jobs | Degraded ingestion status, not permanent failure |
| Hosted 429/5xx | Bounded backoff/jitter; circuit breaker; configured fallback | Stage delayed or explicit failure if exhausted |
| Vector/index failure after DB write | Retry idempotent indexing step | Document remains not fully indexed |
| Invalid answer JSON | One repair attempt, then stop | Explicit answer failure |
| Quote/structure failure | Mark affected claim unsupported; apply verification policy | Claim omitted; refusal if none survive |
| Verifier unavailable/invalid | Do not display answer; persist trace | Explicit verification failure |
| All claims unsupported | Return refusal | Clear insufficient-sources response |
| SSE disconnect | Preserve consistent message/job state | Reconnect or reload persisted outcome |
| Citation provenance missing | Reject affected citation; never guess location | Claim removed or answer failure by policy |
| Dependency unhealthy | Report degraded readiness with trace correlation | Accurate health/status state |

## 12. Non-negotiable release invariants

1. No answer reaches the UI before structural, quote, and entailment verification completes.
2. Every displayed factual claim retains at least one valid citation; unsupported claims are never displayed.
3. Every displayed citation resolves to a document, page, block-level bbox, and verbatim stored source quote.
4. Every chunk maps to ordered source blocks and remains within the measured embedding input limit.
5. Re-ingesting unchanged content with unchanged model semantics makes zero embedding calls.
6. Every retrieval operation enforces collection/document scope and user ownership before ranking.
7. Confidential collections cannot send content to hosted endpoints without an explicit owner override.
8. Exact model IDs, dimensions, limits, score semantics, and calibrated thresholds come from recorded evidence, not assumptions.
9. Hosted-model tests use fixtures by default and cannot unexpectedly spend quota.
10. Phase proof artifacts and acceptance results, not agent summaries, determine phase completion.
11. Every prompt, threshold, chunking, or model change has a reproducible eval record.
12. Required v1 gates complete before optional stretch features are considered done.

## 13. Pending gate register

| Decision/value | Evidence required | Due | Blocked work if unresolved |
| --- | --- | --- | --- |
| Exact hosted model IDs and request shapes | One real minimal call per model or documented fallback | P0 | Hosted integration beyond smoke tests |
| Embedding dimension, input limit, tokenizer/input-type behavior | Real response and model documentation | P0 | D-007, chunk limit, vector schema |
| Rerank route, candidate limit, score scale | Real rerank response and documentation | P0 | Rerank integration and abstention calibration |
| Reasoning controls | Real Super VL and Ultra request tests | P0 | Answer/verifier request configuration |
| Free-tier quota, credits, endpoint terms | Measured burst and current terms review | P0 | Rate configuration, privacy release notes |
| Primary parser viability | Three sample outputs, overlays, GPU stack evidence | P0 | D-009 and P1 implementation |
| Qdrant versus pgvector | D-007 comparison using measured constraints | P0 | Final indexing implementation |
| Actual parser class names | Real P1 postprocessed outputs | P1 | Final chunk class mapping |
| Parse concurrency | Throughput, VRAM, latency at 1/2/4/8 | P1 | Production worker settings |
| Chunk tokenizer proxy and safety margin | Tokenizer availability and measured embed limit | P0/P2 | Oversize prevention |
| Continuation heuristic quality | P2 labeled examples and error review | P2 | Neighbor expansion reliance |
| Abstention threshold | Final gold-set calibration with score semantics | P5 | Release-grade automatic abstention |
| Quote-match threshold confirmation | P5 calibration and audit | P5 | Final verification configuration |
| Success-target attainment or recalibration | Full P5 metrics and error analysis | P5 | Release baseline sign-off |
