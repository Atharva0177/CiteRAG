# CiteRAG Decision Register

**Owner:** Atharva

**Requirements baseline:** [CiteRAG PRD v1.0, 15 Nov 2026](PRD.md)

**Register status:** Active planning baseline

**Decision snapshot:** 11 accepted PRD-fixed records; 12 open evidence-gated records; no resolved or superseded records at initialization.

## 1. Purpose and authority

This register separates choices fixed by the Product Requirements Document (PRD) from choices that must be made from build-time evidence. It records the reason, consequences, fallback, owning task, and proof path for each choice so implementation does not depend on remembered provider contracts or silently guessed values.

[PRD.md](PRD.md) is the requirements authority. This register is the decision and change-control record; `TASKS.md` is the execution checklist. If these documents disagree, the PRD controls unless Atharva formally revises the requirements and supersedes the affected records. A task summary is not evidence of a decision or of completed work.

This is a greenfield register of current decisions, not a restoration of deleted history. All proof, configuration, README, and evaluation links below are **planned, not existing evidence**, unless a future resolved-history entry explicitly identifies the artifact as observed and verified. No phase gate is passed by this document's creation. The P7 stretch items remain optional and non-blocking.

## 2. Status, evidence, and change-control conventions

### Statuses

| Status | Meaning |
| --- | --- |
| `accepted` | Active PRD-fixed policy. It needs implementation proof, but not a selection exercise. |
| `open` | An unresolved evidence-dependent choice. Its label names the resolving gate, and its record names the task and required evidence. |
| `resolved` | A formerly open choice settled by the required evidence at its gate. The original question and evidence remain in the record. |
| `superseded` | No longer active; a successor record and change rationale are linked. The old record remains as history. |

Open labels use exactly **Open — P0 gate**, **Open — P1 gate**, or **Open — P5 gate**. Every record has a stable explicit anchor. Task references are plain IDs rather than guessed `TASKS.md` heading links; task anchors can be added after the actual task headings exist.

### Evidence and proof rules

- A PRD citation establishes requirement authority, not implementation proof.
- A link marked **planned** is a destination for future proof, not a claim that the file, directory, configuration, or result exists.
- `open` becomes `resolved` only when the named task and gate are complete, acceptance checks pass, and real proof has been committed under the correct `proof/Pn/` directory.
- The P0–P7 gates are sequential. The next phase does not start until the prior phase's proof and acceptance criteria pass. Proof is committed per [PRD §14](PRD.md#14-delivery-phases); this document's initial creation does not commit anything.
- Hosted-model tests ordinarily use recorded fixtures. Live smoke, burst, judge, and load procedures are separate and explicit so routine tests do not spend NIM quota.
- Exact hosted model IDs, request shapes, embedding dimensions and input limits, measured quotas, rerank score ranges, parser class inventories, and calibrated thresholds must come from their named resolving tasks. No value in those categories is authoritative merely because it appears in an example elsewhere.

### Change control

1. Keep decision IDs stable. Resolve an open record in place and append a dated history entry; supersede rather than delete an accepted or resolved record when its active choice changes.
2. Distinguish initial gate selections from subsequent changes. Initial P0/P1 model, fallback, parser-class, and class-to-chunk mapping selections resolve on their named gate evidence with applicable config/version identifiers; they do not require a full evaluation baseline that is unavailable before P3/P5. After the initial selection, any model, prompt, threshold, or chunking change must attach an evaluation run and record its **config hash and git SHA**. PRs changing prompts, thresholds, or chunking must attach that run, per [PRD §15](PRD.md#15-engineering-process).
3. Put model IDs, thresholds, and prompts in versioned configuration. Record model/fallback changes in the relevant decision and planned [`config/models.yaml`](config/models.yaml); never hardcode a remembered provider contract.
4. A fixed-value departure or API/schema break requires Atharva's approval, a superseding record, compatibility/migration analysis, and updated proof. Additive implementation details are allowed only where D-F09 explicitly permits them and required semantics remain intact.
5. Retrieval's draft P3 miss path allows a written diagnosis and fix plan; it does not lower the final target. Only P5 may accept a metric miss or recalibrate a target, with cause, user impact, evidence, and follow-up recorded in D-P5-03.
6. A fallback never bypasses verification, privacy, provenance, or proof gates. `P7-T08` stretch work cannot delay the core P7 release gate.

## 3. PRD model roles and fallbacks

The following model-role table is copied exactly from [PRD §6](PRD.md#6-model-stack).

| Stage | Model | Runs on |
| --- | --- | --- |
| Parse | Nemotron-3.5-Parse, 0.631B parameters | Local, RTX 5070 12 GB |
| Embed | nemotron-3.5-embed-8b | NIM hosted |
| Rerank | nemotron-3.5-rerank-8b | NIM hosted |
| Query rewrite | nemotron-3.5-lightning-30b-a3b | NIM hosted |
| Answer | nemotron-3.5-super-vl-120b-a12b | NIM hosted |
| Verify | nemotron-3-ultra-550b-a55b | NIM hosted |

The fallback wording below is also copied exactly from PRD §6.

| Role | PRD fallback wording |
| --- | --- |
| Parse | Parse fails on this GPU or OS stack: Docling. |
| Answer | Super VL changes or is withdrawn (it is labeled early access): llama-3.3-nemotron-super-49b-v1.5. |
| Verify | Verify too slow or rate limited: Lightning, with a lower claim batch size. |

“Lightning” refers to the PRD-named query-rewrite model above; no provider ID is inferred. PRD §6 names no role-specific substitute for embed, rerank, or rewrite. If a required hosted role is unavailable, P0 must select and record a fallback before its gate can pass; this register does not preselect an unnamed substitute. Exact provider IDs and request contracts remain open under D-P0-02, D-P0-04, and D-P0-05.

## 4. Accepted PRD-fixed decisions

<a id="d-f01"></a>
### D-F01 — Product scope and local/hosted execution boundary

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §§1–2](PRD.md#1-summary), [§5](PRD.md#5-architecture), [§6](PRD.md#6-model-stack), [§16 risk: parser/GPU](PRD.md#16-risks).

**Affected tasks:** `P0-T02`, `P0-T03`, `P0-T04`, `P0-T08`, `P1-T02`, `P1-T04`, `P1-T05`, `P2-T05`, `P7-T04`, `P7-T05`, `P7-T08` (optional).

**Decision:** Parse pages locally with Nemotron-3.5-Parse on the RTX 5070 12 GB; run embed, rerank, query rewrite, answer, and verify on hosted NVIDIA NIM endpoints. Use Docling if the parser fails on this GPU or OS stack, and check a hosted parse endpoint if one is available without assuming that it exists. The parser supports Linux only; Windows uses WSL2 with GPU passthrough.

CiteRAG v1 accepts PDF, PNG, and JPG up to a configurable size cap, computes SHA-256, and answers questions over those documents with document/page/block-bbox citations and verbatim quotes. Collection-scoped duplicate reject-versus-link behavior remains open under D-P1-03. It handles scanned and digital PDFs, tables, charts, and English/Hindi/Marathi evaluation documents. Multi-tenant SaaS, billing, collaboration, web search, agents, model fine-tuning, additional input formats, and word-level highlighting are non-goals. Highlight granularity is the parsed block, with the quote shown beside it. DOCX/PPTX conversion, page-image retrieval with multimodal embed/rerank, and answer caching belong only to optional, independently evaluated `P7-T08`; DOCX/PPTX conversion uses PDF conversion if attempted. Core P7 authentication and per-user collections do not turn v1 into multi-tenant SaaS.

**Rationale:** Local parsing keeps page processing on the consumer GPU while the named hosted roles satisfy the free-tier-plus-one-GPU goal. Block-level provenance supports verifiable citations without promising word-level precision. A narrow input and product scope protects the citation-quality and evaluation goals.

**Consequences:** The parse service needs a separate Linux/WSL2 start path and GPU diagnostics. Hosted calls cross the machine boundary and are governed by D-F10. All citations resolve to blocks, and the UI must display the verbatim quote to offset coarse highlights. Stretch items cannot enter core acceptance or block release.

**Fallback / reversal trigger:** GPU/OS incompatibility activates the P0 smoke investigation and Docling fallback; D-P0-01 records the selected stack. WSL2 failure may select native Linux. A local-model path would be required before confidential collections could be indexed locally; it is not assumed. Expanding scope or highlight granularity requires PRD approval and a superseding record.

**Evidence / proof / config:** Requirements evidence is the PRD above. Planned, not existing: [`proof/P0/smoke_report.md`](proof/P0/smoke_report.md), [P0 raw outputs and overlays](proof/P0/), [P1 parser proof](proof/P1/), and [P7 release notes](proof/P7/).

<a id="d-f02"></a>
### D-F02 — Application, worker, storage, and packaging stack

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §5](PRD.md#5-architecture), [§9](PRD.md#9-api), [§12](PRD.md#12-non-functional-requirements), [§14 P7](PRD.md#p7-hardening-and-release).

**Affected tasks:** `P0-T01`, `P0-T02`, `P1-T01`, `P1-T05`, `P2-T07`, `P4-T07`, `P6-T01`, `P7-T03`, `P7-T04`, `P7-T07`.

**Decision:** Use Next.js 15 App Router with TypeScript and pdf.js for chat, library, and PDF highlights; FastAPI for REST, SSE status events, and auth; Celery with Redis for ingestion jobs and retries; and PostgreSQL for metadata, blocks, chunks, full-text indexing, and conversations. Use Docker Compose for everything except the GPU parse service, which may run directly in WSL2 and has its own documented start procedure. A Python NIM-gateway module in the API package is the single location for hosted calls, rate limiting, retries, and caching. Qdrant is the default vector store but its final selection is evidence-gated under D-P0-03, not silently fixed here.

**Rationale:** These components directly support the PRD's typed web client, asynchronous ingestion, SSE workflow, relational provenance, lexical retrieval, and reproducible local deployment. Keeping the GPU service outside Compose respects its Linux/WSL2 requirements.

**Consequences:** Worker state must be resumable, browser code must never receive API secrets, and all hosted traffic must pass through the gateway. `docker compose up` does not claim to start the GPU parser. The clean-machine README must explain both the Compose and parser startup paths. Vector-store health and migrations follow the P0 selection.

**Fallback / reversal trigger:** Component substitutions or moving the parser into the Compose contract require a superseding decision and fresh portability proof. If Qdrant is replaced by the allowed pgvector simplification, D-P0-03 must be resolved and all required payload/filter/health behavior preserved. Startup failure blocks P7 rather than being hidden in documentation.

**Evidence / proof / config:** Requirements evidence is PRD §§5, 9, and 12. Planned, not existing: [P0 bootstrap/smoke report](proof/P0/smoke_report.md), [P1 ingestion proof](proof/P1/), [P4 chat proof](proof/P4/), [P7 clean-machine setup and release proof](proof/P7/), and [Compose file](docker-compose.yml).

<a id="d-f03"></a>
### D-F03 — Named model roles, generation settings, and hosted fallbacks

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §6](PRD.md#6-model-stack), [§7.4–7.6](PRD.md#74-retrieval), [§11](PRD.md#11-quota-and-rate-limits), [§16 risk: early-access answer model](PRD.md#16-risks), [§17](PRD.md#17-assumptions-to-verify-in-p0).

**Affected tasks:** `P0-T04`, `P0-T08`, `P1-T04`, `P2-T05`, `P2-T06`, `P3-T01`, `P3-T03`, `P4-T01`, `P4-T04`, `P5-T05`, `P5-T06`, `P7-T05`.

**Decision:** Keep the six role assignments exactly as shown in §3: Nemotron-3.5-Parse for parse, nemotron-3.5-embed-8b for embed, nemotron-3.5-rerank-8b for rerank, nemotron-3.5-lightning-30b-a3b for rewrite, nemotron-3.5-super-vl-120b-a12b for answer, and nemotron-3-ultra-550b-a55b for verify.

Apply the PRD settings without inventing numeric values where it is qualitative:

- **Parse:** double-pass; `guarded` merge if duplicate table hypotheses pollute the index; single-pass is the fast fallback. Rendering and sampling are fixed in D-F04, and measured mode/concurrency selection is D-P1-02.
- **Rewrite:** low temperature, short output; run only when the conversation has prior turns or the query is under-specified. Preserve the original question for display.
- **Answer:** reasoning off, JSON output per PRD §10, temperature at or near 0.
- **Verify:** one batched call per answer with all claims together; reasoning on with a token budget if the endpoint supports it. Supported controls are discovered in P0, not presumed.
- **Rerank:** 30 candidates in, 8 out.
- **Embed:** batch through the gateway, derive vector size from the first response, and cache by text hash. Input and batch contracts remain open.

Activate only the PRD-named answer fallback, llama-3.3-nemotron-super-49b-v1.5, if Super VL changes or is withdrawn; use Lightning with a lower claim batch size if verify is too slow or rate limited. Parser fallback is Docling under D-F01. Exact provider IDs, endpoint availability, request parameters, reasoning controls, and fallback activation remain open under D-P0-02.

**Rationale:** Role separation follows the PRD's quality/cost architecture. Deterministic answer settings and batched verification support reproducibility, while explicit fallbacks address early-access and throttling risks without dropping the verification stage.

**Consequences:** All six roles must respond in P0 or have recorded fallbacks. Initial P0 model/fallback selections use P0 smoke evidence and versioned config; subsequent model substitutions require an evaluation run. Verification fallback may reduce claim batch size but never skips quote/entailment checks or permits an unverified answer.

**Fallback / reversal trigger:** The three named fallback triggers above are active policy. Endpoint disappearance, unexpected request/reasoning behavior, or excessive latency/rate limiting is resolved at P0 with measured evidence; any unnamed fallback must be selected and recorded at that gate. After the initial P0 selection, every model change reruns evaluation and records config hash/git SHA.

**Evidence / proof / config:** Requirements evidence is PRD §6. Planned, not existing: [P0 smoke report and model/limit table](proof/P0/smoke_report.md), [P0 recorded calls](proof/P0/), [`config/models.yaml`](config/models.yaml), [P4 answer/verifier proof](proof/P4/), and [P5 baseline and ablations](proof/P5/baseline.md).

<a id="d-f04"></a>
### D-F04 — Page rendering, exact parse contract, and coordinate provenance

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §7.1](PRD.md#71-ingestion), [§8](PRD.md#8-data-model), [§14 P0–P1](PRD.md#p0-environment-and-smoke-tests), [§16 risk: parser errors](PRD.md#16-risks).

**Affected tasks:** `P0-T03`, `P1-T03`, `P1-T04`, `P1-T05`, `P1-T07`, `P1-T08`, `P5-T05`, `P6-T05`.

**Decision:** Render every PDF page to RGB with PyMuPDF at **150 dpi**. If the render exceeds **1664 × 2048 pixels**, downscale to fit while preserving aspect ratio; A4 and Letter at 150 dpi already fit. Store actual render width, height, dpi, and scale-to-PDF metadata per page.

Use this exact task prompt:

```text
</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>
```

Use `max_new_tokens` = 8744. Over vLLM use temperature 0, `top_k` = 1, `repetition_penalty` = 1.1, and `skip_special_tokens` = false so control tokens are preserved. Retain raw model output for every page. Run `postprocess_document` with the actual render size to obtain markdown and blocks carrying class, normalized bbox, `bbox_pixels`, and text. Convert bbox pixels to PDF points as `pixels * 72 / render_dpi`, adjusted for any downscale factor, and store both pixel and PDF forms.

Start in double-pass mode. Use `guarded` merge if duplicate table hypotheses pollute the index; single-pass is the fast fallback. Retry a failed page twice, then mark that page failed without failing the whole document. Jobs are idempotent and resumable from the last good page. Parse concurrency starts at 4 and is tuned from P1 measurements under D-P1-02.

**Rationale:** Exact rendering and sampling preserve parser behavior and control tokens. Raw output plus all coordinate forms makes parsing auditable and citations drawable on the source PDF. Page-level isolation prevents one bad page from discarding the rest of a document.

**Consequences:** No implementation may silently alter the prompt, sampling, dpi, or downscale arithmetic. Downscale metadata is required for accurate PDF conversion. Reviewers must inspect raw output and overlays, including tables and scans. Failed pages remain visible in status/progress rather than disappearing into a successful document state.

**Fallback / reversal trigger:** GPU/OS failure uses D-F01; duplicate table hypotheses activate `guarded`; throughput/quality/VRAM evidence may select single-pass at P1. Any change to fixed parse or coordinate values requires regression overlays, a superseding record, and applicable evaluation. Parser errors discovered on the ten-page review block the P1 gate until fixed or handled by the approved fallback.

**Evidence / proof / config:** Requirements evidence is PRD §7.1. Planned, not existing: [P0 smoke report](proof/P0/smoke_report.md), [P0 raw digital/scanned/table outputs and three overlays](proof/P0/), [P1 ten overlays, parse JSON, and benchmark table](proof/P1/), and [`config/models.yaml`](config/models.yaml).

<a id="d-f05"></a>
### D-F05 — Block-based chunking and source provenance

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §7.2](PRD.md#72-chunking), [§7.3](PRD.md#73-indexing), [§8](PRD.md#8-data-model), [§14 P2](PRD.md#p2-chunking-and-indexing).

**Affected tasks:** `P1-T07`, `P2-T01`, `P2-T02`, `P2-T03`, `P2-T04`, `P2-T08`, `P3-T04`, `P5-T02`, `P5-T07`.

**Decision:** Chunk parsed blocks, not raw text, using observed semantic classes under D-P1-01. Exclude page headers, footers, and page numbers from the index but retain them in `blocks`. Every chunk stores its source blocks, page numbers, and bboxes so it can be drawn on the PDF.

- Target **400–800 tokens** per text chunk with **about 12% overlap**. Split on block and paragraph boundaries; never cut inside a block unless that block alone exceeds the maximum.
- A table is one chunk. Above **1,200 tokens**, split by rows and repeat the header row in each part. Store table HTML for display and flattened row-wise text for embedding and lexical search.
- A chart block becomes one chunk from its extracted data and caption.
- Prepend the section path, such as `Report > 3 Risks > 3.2 Credit`, to embedded text only, never displayed text.
- Implement cross-page table/paragraph continuation with `continues_from`; the parser does not infer it. Evaluate this heuristic in P2.
- Count tokens with the embedding model's tokenizer when available, otherwise a documented proxy. Keep every chunk maximum below the input limit measured in D-P0-04.

**Rationale:** Parser blocks retain table/chart semantics and precise citation geometry. Bounded, overlapping text chunks support retrieval while row-wise table splitting and repeated headers preserve context. Section paths improve retrieval without contaminating display text, and explicit continuation links permit safe neighbor expansion.

**Consequences:** The chunker cannot be a raw fixed-window text splitter. `chunk_blocks` provenance, table HTML, flattened text, section paths, and continuation links are required. No chunk may exceed the measured embed limit, and re-ingestion/proof must demonstrate complete block/bbox mappings. Unknown parser classes cannot be invented or silently discarded.

**Fallback / reversal trigger:** Oversized blocks are the only permitted reason to cut inside a block; oversized tables use row splitting. Ambiguous classes remain a P1 mapping issue. Chunking or continuation defects require fixes and P2 provenance/token audits. Any chunking change reruns evaluation with config hash/git SHA; changing fixed ranges or weakening provenance requires a superseding record.

**Evidence / proof / config:** Requirements evidence is PRD §7.2. Planned, not existing: [P1 observed class/overlays](proof/P1/), [P2 three-document chunk dump, token histogram, ten table chunks, and provenance audit](proof/P2/), [P5 baseline](proof/P5/baseline.md), and [versioned configuration](config/).

<a id="d-f06"></a>
### D-F06 — Hybrid retrieval, rerank, abstention, and context assembly

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §7.3–7.4](PRD.md#73-indexing), [§11](PRD.md#11-quota-and-rate-limits), [§14 P3](PRD.md#p3-retrieval), [§16 risk: multilingual quality](PRD.md#16-risks).

**Affected tasks:** `P2-T05`, `P2-T06`, `P2-T07`, `P3-T01`, `P3-T02`, `P3-T03`, `P3-T04`, `P3-T05`, `P3-T06`, `P3-T07`, `P3-T08`, `P5-T02`, `P5-T03`, `P5-T05`, `P5-T07`, `P7-T06`.

**Decision:** Conditionally rewrite the question into a standalone query using the last few turns, retaining the original for display. Run dense search **top 40** and lexical search **top 40**, both restricted to the selected collection or documents. PostgreSQL lexical search uses a `tsvector` with the **`simple` configuration** so Hindi and Marathi tokens are not dropped. Merge with Reciprocal Rank Fusion, constant **60**; rerank the top **30** merged candidates and keep the top **8**.

If the top rerank score is below the calibrated threshold, skip generation and return a refusal. That threshold is open under D-P5-01 and cannot be guessed. Assemble context labels **C1–C8**, add neighbor chunks only when linked by `continues_from`, and cap context at a configurable token budget. Persist candidates, scores, model IDs, and retrieval traces for LLM-free evaluation.

**Rationale:** Dense plus lexical retrieval covers semantic and exact-match evidence, RRF avoids score-scale assumptions, and reranking focuses the answer context. Collection/document filters enforce scope. A calibrated abstention gate supports honest refusal, and continuation-only neighbors avoid unrelated context expansion.

**Consequences:** The `30 → 8` rerank contract is fixed even though its route, capacity, and score scale are open. A production abstention mechanism may be tested with synthetic fixtures before P5, but no uncalibrated threshold becomes authoritative. Multilingual retrieval results are reported separately. No-rerank and no-hybrid configurations are evaluation ablations, not permission to remove production stages.

**Fallback / reversal trigger:** Draft Recall@8 below **0.85** at P3 requires the PRD-permitted diagnosis and fix plan; it does not reduce the final **≥0.90** target. If rerank cannot support the required contract, P0 must select and record a compatible route or fallback under D-P0-05 rather than guess or disable it; P3 validates actual `30 → 8` pipeline behavior. Subsequent model/score changes require recalibration and evaluation.

**Evidence / proof / config:** Requirements evidence is PRD §§7.3–7.4. Planned, not existing: [P2 indexing/quota proof](proof/P2/), [P3 draft gold set, retrieval report, traces, and ablations](proof/P3/), [P5 baseline/calibration](proof/P5/baseline.md), and [`config/retrieval.yaml`](config/retrieval.yaml).

<a id="d-f07"></a>
### D-F07 — Exact answer and verifier JSON contracts

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §7.5](PRD.md#75-generation), [§10](PRD.md#10-output-schemas), [§14 P4](PRD.md#p4-generation-and-verification).

**Affected tasks:** `P4-T01`, `P4-T02`, `P4-T03`, `P4-T04`, `P4-T05`, `P4-T06`, `P4-T07`, `P4-T08`, `P6-T03`, `P6-T04`.

**Decision:** The answer prompt requires answers only from labeled context, a chunk ID and verbatim quote for every factual sentence, and abstention when context is insufficient. Quotes are at most **25 words** and exact text from the cited chunk. Invalid output JSON receives exactly **one automatic repair attempt**, then a visible failure state. The answer contract is:

```json
{
  "abstain": false,
  "abstain_reason": null,
  "summary": "string",
  "paragraphs": [
    [
      {
        "text": "one sentence",
        "type": "claim",
        "chunk_ids": ["C3"],
        "quote": "verbatim text from C3, 25 words or fewer"
      },
      { "text": "transition sentence", "type": "connective", "chunk_ids": [], "quote": null }
    ]
  ]
}
```

Every `claim` needs at least one chunk ID and a quote. `connective` sentences may not contain facts. The summary is composed only from claims that survive verification. The verifier returns one result per claim with `supported`, `partial`, or `unsupported` and a one-line reason; its JSON shape is:

```json
{
  "results": [
    { "claim_index": 0, "verdict": "supported", "reason": "string" }
  ]
}
```

**Rationale:** A narrow, explicit schema makes claim-level verification, refusal, and citation resolution deterministic. Separating factual claims from non-factual connectives prevents uncited factual text from hiding in transitions, and deriving the summary only from survivors prevents unsupported claims from reappearing.

**Consequences:** Validators, repair logic, SSE final events, and the UI must preserve claim/connective semantics and abstention fields. Multiple citations on one sentence remain possible through `chunk_ids`. The verifier's example shows `supported`, but the allowed verdict set includes all three PRD states. No required field or rule may be dropped.

**Fallback / reversal trigger:** JSON failure after the single repair is shown as failure; it is not rendered as a best-effort answer. Contract changes require schema/client migration, regression proof, Atharva's approval, and a superseding record. Prompt changes require an eval run with config hash/git SHA.

**Evidence / proof / config:** Requirements evidence is PRD §10. Planned, not existing: [P4 thirty recorded answers, verifier outputs, removals, and five refusals](proof/P4/), [P6 UI proof](proof/P6/), and [versioned prompts](config/prompts/).

<a id="d-f08"></a>
### D-F08 — Mandatory three-stage verification and citation resolution

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §7.6](PRD.md#76-verification), [§7.7](PRD.md#77-frontend), [§10](PRD.md#10-output-schemas), [§14 P4–P5](PRD.md#p4-generation-and-verification), [§16 risk: verifier errors](PRD.md#16-risks).

**Affected tasks:** `P4-T01`, `P4-T02`, `P4-T03`, `P4-T04`, `P4-T05`, `P4-T06`, `P4-T07`, `P4-T08`, `P5-T02`, `P5-T04`, `P5-T05`, `P5-T06`, `P6-T02`, `P6-T03`, `P6-T04`, `P6-T05`, `P6-T06`, `P6-T07`.

**Decision:** Every answer passes all three verification stages before display:

1. **Structural:** JSON is valid and every cited chunk ID was in the provided context.
2. **Quote:** Normalize both sides with Unicode NFKC, whitespace, and case normalization; require fuzzy match at or above the configured threshold, initially **92 partial ratio**, against the cited chunk text. Failing quotes mark the claim unsupported.
3. **Entailment:** One batched Ultra call returns `supported`, `partial`, or `unsupported` per claim with a one-line reason.

Remove unsupported claims from the displayed answer. Keep partial claims with a visible badge. If every factual claim is removed, return a refusal. If more than **30%** are removed, regenerate once with a stricter prompt, then apply the same checks again. Compose the summary only from surviving claims. Persist verifier output with the answer for audit and evaluation.

For each surviving claim, resolve the block inside the cited chunk that best matches the quote and return its page and bbox. If no single block matches, return all blocks of the chunk. Show the answer only after verification; answer-token streaming is not used. Display quotes next to block highlights and table HTML where applicable.

The frontend presents a summary, detailed explanation, and numbered sources with document, page, and quote. Inline citation chips open the pdf.js viewer at the cited page/block bbox; multiple citations on one sentence open a chooser. Partial claims have badges, and refusals/failures have clear states. Table citations render sanitized stored table HTML in a side panel beside the highlighted page. The library provides upload, per-document progress, delete, and collections.

**Rationale:** Structural, quote, and entailment checks address different failure modes before the user sees a claim. Removal/refusal policies favor honest uncertainty over fluent unsupported output. Best-block resolution gives precise highlights while the all-blocks fallback preserves honest geometry when no unique block matches.

**Consequences:** No failed-quote answer can be displayed, and verifier-off mode is confined to the P5 ablation. Verification output and removed-claim reasons are audit data. Latency fallback may use Lightning with smaller claim batches under D-F03, but cannot bypass checks. Quote calibration remains open under D-P5-02.

**Fallback / reversal trigger:** Failed quotes and unsupported claims follow the removal policy; all removed means refusal; >30% removed permits only one regeneration. If verify is too slow/rate limited use the named model fallback. False support/removal found in the P5 audit triggers error analysis and calibration or prompt/model change with evaluation, never silent policy weakening.

**Evidence / proof / config:** Requirements evidence is PRD §7.6. Planned, not existing: [P4 recorded answers and verifier/removal audit](proof/P4/), [P5 baseline, quote calibration, verifier-off ablation, and human audit](proof/P5/baseline.md), and [versioned prompts/config](config/).

<a id="d-f09"></a>
### D-F09 — Required data model and REST/SSE surface

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §8](PRD.md#8-data-model), [§9](PRD.md#9-api), [§7.1](PRD.md#71-ingestion), [§7.7](PRD.md#77-frontend), [§14 P7](PRD.md#p7-hardening-and-release).

**Affected tasks:** `P1-T01`, `P1-T02`, `P1-T05`, `P1-T06`, `P2-T06`, `P2-T07`, `P3-T01`, `P4-T07`, `P6-T01`, `P6-T02`, `P6-T03`, `P6-T04`, `P6-T05`, `P6-T06`, `P7-T01`, `P7-T03`, `P7-T04`.

**Decision:** Preserve the PRD's key columns and relationships. Additive implementation details are allowed, but no required field or route may be dropped.

| Table | Key columns |
| --- | --- |
| users | id, email, password\_hash, created\_at |
| collections | id, user\_id, name |
| documents | id, collection\_id, filename, sha256, page\_count, lang\_hint, status, created\_at |
| pages | id, document\_id, page\_no, render\_dpi, render\_w, render\_h, scale\_to\_pdf, parse\_status, raw\_output, parse\_ms |
| blocks | id, page\_id, order\_idx, class, bbox\_norm, bbox\_px, bbox\_pdf, text, html |
| chunks | id, document\_id, chunk\_type, text, embed\_text, token\_count, section\_path, page\_start, page\_end, continues\_from, tsv |
| chunk\_blocks | chunk\_id, block\_id, order\_idx |
| embed\_cache | text\_sha256, model, vector\_dim, vector\_ref |
| conversations | id, collection\_id, created\_at |
| messages | id, conversation\_id, role, content, rewritten\_query, answer\_json, verifier\_json, trace\_json, created\_at |
| eval\_runs | id, config\_hash, git\_sha, metrics\_json, created\_at |

`trace_json` records stage latencies, call counts, model IDs, and retrieved chunk IDs with scores for every query. When Qdrant is retained, its payload contains `chunk_id`, `doc_id`, `collection_id`, `page_start`, `page_end`, `section_path`, `chunk_type`, and `lang`; an allowed pgvector simplification must preserve equivalent retrieval/filter provenance.

Preserve this API surface:

- `POST /auth/register`, `POST /auth/login`
- `GET/POST /collections`
- `POST /collections/{id}/documents` multipart upload, returning a document ID; collection-scoped duplicate semantics remain D-P1-03 until the contract freeze.
- `GET /documents/{id}` status and page progress
- `GET /documents/{id}/file` original file for the viewer
- `GET /documents/{id}/pages/{n}/blocks` blocks with bboxes
- `DELETE /documents/{id}`
- `POST /chat` with `collection_id`, `conversation_id`, `question`, and optional `doc_ids`; return SSE status events and then a final `answer` event.
- `GET /conversations/{id}/messages`
- `GET /health`, including parse service, Qdrant, Postgres, and NIM reachability; if pgvector is selected, D-P0-03 must record the equivalent selected-store health behavior.

Document states are `queued`, `rendering`, `parsing`, `chunking`, `embedding`, `indexed`, and `failed`, with page counts. Chat statuses are `rewriting`, `retrieving`, `reranking`, `answering`, and `verifying`. Complete auth and per-user object authorization at P7 before release; earlier development identity must not be represented as multi-user auth.

**Rationale:** These fields are the minimum provenance, audit, evaluation, and viewer contract. The named routes support all five use cases without exposing hosted secrets. Additive fields permit implementation needs without sacrificing requirements.

**Consequences:** Migrations, authorization checks, SSE clients, and tests must cover every required table and method. Duplicate behavior cannot be left ambiguous in the upload contract. Health/status endpoints expose operational state without exposing secrets. Switching vector stores does not erase required metadata or observability.

**Fallback / reversal trigger:** Additive changes must remain backward-compatible with required semantics. Removing/renaming fields or routes, changing duplicate behavior after freeze, or weakening authorization requires a superseding record, migration/compatibility proof, and owner approval. P7 fails if object-level authorization or required health checks are absent.

**Evidence / proof / config:** Requirements evidence is PRD §§8–9. Planned, not existing: [P1 schema/upload/status proof](proof/P1/), [P2 indexing proof](proof/P2/), [P4 chat proof](proof/P4/), [P6 UI proof](proof/P6/), and [P7 auth/health/release proof](proof/P7/).

<a id="d-f10"></a>
### D-F10 — Privacy, secrets, observability, reliability, and portability

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §11](PRD.md#11-quota-and-rate-limits), [§12](PRD.md#12-non-functional-requirements), [§16 risk: confidential documents](PRD.md#16-risks), [§14 P7](PRD.md#p7-hardening-and-release).

**Affected tasks:** `P0-T01`, `P0-T02`, `P0-T07`, `P1-T02`, `P1-T05`, `P1-T06`, `P2-T05`, `P4-T07`, `P7-T01`, `P7-T03`, `P7-T04`, `P7-T05`, `P7-T07`.

**Decision:** Apply all PRD non-functional requirements as release constraints:

- **Privacy:** Chunk text and questions go to hosted NVIDIA endpoints. Free-trial terms may permit NVIDIA to record inputs. Do not index confidential documents on this tier. Confirm current terms in P0 and document them in the README. A collection-level flag blocks indexing of marked documents until a local model path exists.
- **Secrets:** API keys come from environment variables, are never logged, and never reach the browser.
- **Observability:** Emit structured JSON logs with a trace ID per request and ingestion job. Record per-stage latency and call counts in `trace_json`, together with the model/retrieval details required by D-F09. Redact secrets and sensitive values.
- **Reliability:** Ingestion survives worker restarts. A parse-service outage pauses jobs instead of failing them; page retry/failure behavior remains D-F04. Idempotent jobs resume from the last good page.
- **Reproducibility:** All thresholds, model IDs, and prompts live in versioned config. Each eval run records config hash and git SHA.
- **Portability/platform:** `docker compose up` starts everything except the GPU parse service, which has its own documented start script. The parser supports Linux only; Windows uses WSL2 with GPU passthrough.
- **Hosted-call control:** Every hosted call goes through the NIM gateway with measured per-model limits, retries/backoff, circuit breaking, caching, and approved fallbacks under D-P0-06. Routine tests use recorded fixtures rather than spending quota.

**Rationale:** Hosted inference creates privacy and availability boundaries that must be explicit. Traceable, versioned execution makes results diagnosable and reproducible, while restart-safe jobs and separate parser startup match the local GPU architecture.

**Consequences:** A confidential collection cannot be made searchable by simply accepting the upload; hosted indexing is blocked. Secret exposure, missing authorization, or absent privacy notes blocks release. Worker and outage tests must prove recovery, and every query/ingestion trace is correlatable. A future local path is optional and must be proven before confidential indexing changes.

**Fallback / reversal trigger:** Parse outage pauses work; 429/5xx responses follow gateway controls. Confidential marking stops hosted indexing until a local path exists—there is no “send anyway” fallback. Unfavorable or unclear terms keep the restriction in force and are documented. Any privacy/secrets relaxation requires PRD approval and a superseding record; operational config changes retain audit/eval requirements.

**Evidence / proof / config:** Requirements evidence is PRD §§11–12 and 16. Planned, not existing: [P0 terms and endpoint review](proof/P0/smoke_report.md), [P1 confidential-block, outage, retry, and restart proof](proof/P1/), [P7 structured-log/health/security/privacy/clean-machine proof](proof/P7/), [README privacy/setup notes](README.md), and [versioned config](config/).

<a id="d-f11"></a>
### D-F11 — Evaluation, initial targets, and proof-gated delivery

**Status:** accepted

**Owner:** Atharva

**PRD references:** [PRD §4](PRD.md#4-success-metrics), [§13](PRD.md#13-evaluation-plan), [§14](PRD.md#14-delivery-phases), [§15](PRD.md#15-engineering-process), [§16](PRD.md#16-risks).

**Affected tasks:** All core tasks `P0-T01`–`P0-T08`, `P1-T01`–`P1-T08`, `P2-T01`–`P2-T08`, `P3-T01`–`P3-T08`, `P4-T01`–`P4-T08`, `P5-T01`–`P5-T07`, `P6-T01`–`P6-T07`, and `P7-T01`–`P7-T07`; `P7-T08` only when its optional work is activated.

**Decision:** Preserve the initial metrics and targets exactly. They may be recalibrated only after the P5 baseline and never silently lowered.

| Metric | Definition | Initial target |
| --- | --- | --- |
| Recall@8 | Gold source chunk or page in the final 8 | >= 0.90 |
| MRR | Rank of first gold source after rerank | >= 0.75 |
| Citation precision | Cited chunk truly supports the claim, judged by gold labels and spot checks | >= 0.95 |
| Citation recall | Factual claims that carry a citation | >= 0.98 |
| Unsupported claim rate | Claims shown to the user that the verifier or a human marks unsupported | <= 3% |
| Refusal accuracy | Unanswerable questions correctly refused | >= 0.90 |
| Answer correctness | Judge score against gold answers, 20% human audit | >= 0.85 |
| Query latency | Question to verified answer | p95 <= 30 s |

Build a final gold set of **60–100 questions** from Atharva's own documents, each with an expected answer, expected source page, and expected source block: about **35% factoid**, **25% table lookup**, **15% multi-passage**, **10% cross-document**, at least **15% unanswerable**, and at least **10 questions on Hindi or Marathi documents**. Document composition gaps in the P3 draft rather than claiming final coverage early.

Compute Recall@k and MRR at chunk and page level from stored traces without an LLM. Measure citation precision/recall, unsupported claim rate, refusal accuracy, answer correctness, and per-stage latency. Use an Ultra judge against gold answers for answer correctness, manually audit **20%** of items and **every disagreement**, and report Hindi/Marathi results separately. Run baseline ablations once: no rerank, no hybrid, single versus double parse pass, and verifier off; verifier off is evaluation-only. Every chunking, threshold, or prompt change reruns the suite and stores an `eval_runs` row with config hash/git SHA.

Apply the PRD engineering controls: root `TASKS.md` task IDs use `P{phase}-T{nn}` with status, owner, and proof links; commits use `type(P1-T03): message` with type `feat`, `fix`, `test`, `docs`, or `chore`, one task per commit where possible. Compare code and proof artifacts against `TASKS.md`, not an agent's summary. CI runs unit tests on every push for the chunker, bbox conversion, quote matcher, RRF, and JSON repair; hosted-model tests use recorded fixtures. Pull requests changing prompts, thresholds, or chunking attach an eval run.

Enforce these proof gates in order:

| Phase | Required planned proof and acceptance gate |
| --- | --- |
| P0 | `proof/P0/smoke_report.md`, raw parse outputs, three sample overlays (digital/scanned/table-heavy), model-ID/measured-limit table, and `config/models.yaml`; all six models respond or fallbacks are chosen and recorded. |
| P1 | Ten varied overlays and parse JSON, timing/VRAM at concurrency 1/2/4/8, chosen concurrency and reason; manual source-text and bbox approval on ten pages, with retries/failures reported. |
| P2 | Three-document chunk dump, token histogram, ten table chunks with HTML, quota report; no chunk over embed limit, every chunk maps to blocks/bboxes, and identical reingestion spends zero embedding calls. |
| P3 | First gold-set draft, retrieval metrics, no-hybrid/no-rerank ablations; draft Recall@8 **≥0.85** or a written diagnosis and fix plan. Final target remains ≥0.90. |
| P4 | Thirty recorded answers with verifier output, every removed claim/reason, five refusals; citation precision and unsupported rate measured, no answer displayed after quote-check failure, summary only from verified survivors. |
| P5 | `proof/P5/baseline.md`, all metrics against §4, `eval_runs` rows, required ablations, Hindi/Marathi results, and worst-15 error analysis; targets met or every miss documented with cause and decision under D-P5-03. |
| P6 | Recording of UC1–UC5 and Playwright citation-position test; correct block highlight for **20 of 20** sampled citations. |
| P7 | Clean-machine setup log, controlled **8 questions/minute** load test, final eval; fresh clone reaches a working verified answer using README alone, with authorization/privacy/secret checks passing. Optional P7-T08 is not required. |

**Rationale:** Claim-level evaluation and human audits test the product's central trust promise, while phase proof catches integration errors before downstream work builds on them. Separate language results and ablations expose weaknesses that aggregate metrics could hide.

**Consequences:** A task cannot be `done` from a summary alone. Missing proof or a failed acceptance check leaves its gate incomplete. Retrieval's draft threshold and final threshold are deliberately different. P5 miss decisions must include user impact and follow-up, and release repeats final evaluation rather than relying only on an old baseline.

**Fallback / reversal trigger:** P3 allows diagnosis/fix instead of meeting draft recall; P5 allows individually explained misses or evidence-backed recalibration under D-P5-03. Other gates have no silent waiver. Failed release/load/highlight/privacy checks block completion. Any target change outside P5 or without evidence is invalid and must be reversed.

**Evidence / proof / config:** Requirements evidence is PRD §§4 and 13–15. Planned, not existing: [`proof/P0/`](proof/P0/), [`proof/P1/`](proof/P1/), [`proof/P2/`](proof/P2/), [`proof/P3/`](proof/P3/), [`proof/P4/`](proof/P4/), [`proof/P5/baseline.md`](proof/P5/baseline.md), [`proof/P6/`](proof/P6/), [`proof/P7/`](proof/P7/), and [versioned config](config/).

## 5. Evidence-gated decisions

### P0 gate records

<a id="d-p0-01"></a>
### D-P0-01 — GPU software stack and WSL2/native-Linux selection

**Status:** open (**Open — P0 gate**)

**Owner:** Atharva

**PRD references:** [PRD §5](PRD.md#5-architecture), [§12 platform](PRD.md#12-non-functional-requirements), [§14 P0](PRD.md#p0-environment-and-smoke-tests), [§16 parser risk](PRD.md#16-risks), [§17 Blackwell compatibility](PRD.md#17-assumptions-to-verify-in-p0).

**Affected tasks:** `P0-T01`, `P0-T02`, `P0-T03`, `P0-T08`, `P1-T04`, `P1-T05`, `P1-T08`, `P7-T04`.

**Open question:** Which exact CUDA, PyTorch, and vLLM versions/builds support Nemotron-3.5-Parse on the RTX 5070 12 GB, and should the reproducible parse service run under WSL2 with GPU passthrough or native Linux? No version or platform winner is selected in advance.

**Rationale:** Blackwell compatibility and the Linux-only parser are explicit P0 risks. A minimal end-to-end parse is stronger evidence than installation success or a version compatibility claim.

**Consequences:** The resolution pins the bootstrap/start procedure and supplies the environment baseline for P1 throughput/VRAM tests. Until resolved, parser-dependent implementation cannot pass P0. Selecting native Linux or WSL2 does not change the outside-Compose boundary.

**Fallback / reversal trigger:** Try the alternate supported Linux/WSL2 path if the first stack fails. If parsing fails on the GPU/OS stack, activate Docling under D-F01 and check a hosted parse endpoint if available; record that choice at P0. Driver/model/runtime changes require new smoke and parser proof before replacing the resolution.

**Required to resolve:** Record exact installed versions/builds, OS/WSL environment, GPU recognition, startup steps, and successful digital, scanned, and table-heavy sample parses with raw outputs and one overlay per sample. Explain any selected fallback.

**Resolution task / gate:** `P0-T02` owns compatibility; `P0-T03` supplies the three-page proof; `P0-T08` records the final choice in config and the smoke report. Resolved only at the **P0 gate**.

**Evidence / proof / config:** No observed implementation evidence yet. Planned: [`proof/P0/smoke_report.md`](proof/P0/smoke_report.md), [raw outputs and three overlays](proof/P0/), [`config/models.yaml`](config/models.yaml), and later [P1 benchmarks](proof/P1/).

<a id="d-p0-02"></a>
### D-P0-02 — Exact provider contracts, endpoint availability, and fallback activation

**Status:** open (**Open — P0 gate**)

**Owner:** Atharva

**PRD references:** [PRD §6](PRD.md#6-model-stack), [§11](PRD.md#11-quota-and-rate-limits), [§14 P0](PRD.md#p0-environment-and-smoke-tests), [§17](PRD.md#17-assumptions-to-verify-in-p0).

**Affected tasks:** `P0-T04`, `P0-T07`, `P0-T08`, `P2-T05`, `P3-T01`, `P3-T03`, `P4-T01`, `P4-T04`, `P7-T05`.

**Open question:** What are the current exact provider model ID strings, endpoint/free availability, minimal request shapes, request parameters, and reasoning controls for the hosted roles? Can reasoning be disabled on Super VL and enabled/budgeted on Ultra per request as required? Which, if any, fallbacks must activate? Embed-specific flags/limits and rerank route/score details are resolved in D-P0-04 and D-P0-05.

**Rationale:** PRD §6 explicitly requires these values to be read from each model's build.nvidia.com page during P0, not hardcoded from memory. Super VL is early access, and endpoint behavior can differ from role-level names.

**Consequences:** `config/models.yaml` and the gateway cannot be treated as complete until real calls and current documentation agree. Answer/verify prompts depend on actual reasoning controls. All six roles must respond or have a chosen, recorded fallback before P0 passes.

**Fallback / reversal trigger:** Super VL change/withdrawal activates llama-3.3-nemotron-super-49b-v1.5; slow/rate-limited verify activates Lightning with a lower claim batch size; parser failure uses Docling. For an unnamed unavailable role, select and document a fallback at P0 rather than inventing one here. Any later model or request-contract change requires re-smoke, evaluation, config hash/git SHA, and history.

**Required to resolve:** One minimal recorded call for each of the five hosted roles; current model-page URLs and access dates; exact IDs and observed request/response shapes; endpoint/gating status; supported reasoning parameters; and an explicit active/fallback choice for every role. Do not treat a fixture as a live availability result.

**Resolution task / gate:** `P0-T04` performs role calls, `P0-T07` verifies current endpoint terms/status sources, and `P0-T08` resolves and records model/fallback choices at the **P0 gate**.

**Evidence / proof / config:** No observed provider evidence yet. Planned: [P0 smoke report/model table](proof/P0/smoke_report.md), [recorded calls and raw responses](proof/P0/), [`config/models.yaml`](config/models.yaml), and [P5 model-change evaluation baseline](proof/P5/baseline.md).

<a id="d-p0-03"></a>
### D-P0-03 — Measured vector dimension and Qdrant/pgvector selection

**Status:** open (**Open — P0 gate**)

**Owner:** Atharva

**PRD references:** [PRD §5 Qdrant rationale](PRD.md#5-architecture), [§7.3](PRD.md#73-indexing), [§8](PRD.md#8-data-model), [§14 P0](PRD.md#p0-environment-and-smoke-tests), [§17](PRD.md#17-assumptions-to-verify-in-p0).

**Affected tasks:** `P0-T05`, `P0-T08`, `P2-T06`, `P2-T07`, `P2-T08`, `P7-T03`, `P7-T04`.

**Open question:** What vector dimension does the first real embedding response return, and does it fit the applicable pgvector index limits? Qdrant remains the default. Select the allowed pgvector simplification only if measured evidence supports it; no dimension is assumed.

**Rationale:** PRD §5 chooses Qdrant because embed-8B's output dimension is unknown until P0 and pgvector indexes cap dimensions. Reading the first response prevents schema and index corruption from guessed sizes.

**Consequences:** The choice determines vector schema/index setup, migrations, payload/filter implementation, health checks, and Compose documentation. `embed_cache` records model, vector dimension, and vector reference regardless of selection. Required Qdrant payload semantics or their pgvector equivalent remain mandatory.

**Fallback / reversal trigger:** Unknown or incompatible dimension keeps Qdrant. If pgvector evidence is insufficient, do not simplify. A later store change requires migration, dimension/provenance/filter tests, retrieval evaluation, and a superseding record; an embedding model/dimension change requires cache invalidation and reindexing analysis.

**Required to resolve:** Preserve the first real embedding response, measured dimension, relevant current pgvector index constraint if considered, and a written Qdrant-versus-pgvector choice with rationale. P2 must subsequently prove dimension consistency, required filters/payload, and provenance.

**Resolution task / gate:** `P0-T05` measures the embedding contract; `P0-T08` selects and records the store at the **P0 gate**. `P2-T07` implements it and `P2-T08` supplies integration proof, not a retroactive unverified selection.

**Evidence / proof / config:** No measured dimension exists in this register. Planned: [P0 model/limit table and smoke report](proof/P0/smoke_report.md), [`config/models.yaml`](config/models.yaml), and [P2 indexing/provenance proof](proof/P2/).

<a id="d-p0-04"></a>
### D-P0-04 — Embed limit, tokenizer, input flags, and safe chunk maximum

**Status:** open (**Open — P0 gate**)

**Owner:** Atharva

**PRD references:** [PRD §6](PRD.md#6-model-stack), [§7.2 FR-CHK-9](PRD.md#72-chunking), [§7.3](PRD.md#73-indexing), [§11](PRD.md#11-quota-and-rate-limits), [§17](PRD.md#17-assumptions-to-verify-in-p0).

**Affected tasks:** `P0-T04`, `P0-T05`, `P0-T08`, `P2-T01`, `P2-T02`, `P2-T03`, `P2-T04`, `P2-T05`, `P2-T06`, `P2-T08`.

**Open question:** What is the embedding model's maximum input-token limit, is its tokenizer available, what documented proxy is needed if not, and does the endpoint require a query-versus-passage input flag or other request parameter? What safe chunk maximum follows from the measured limit and counting method? No limit, flag name/value, proxy, or safety margin is guessed here.

**Rationale:** Token counts and request semantics determine whether a chunk is accepted and whether queries/passages are embedded correctly. The PRD fixes ordinary text/table targets but requires every maximum to remain below the real endpoint limit.

**Consequences:** P2 must implement the selected tokenizer/proxy and enforce the resolved maximum, including oversized-block/table splitting. The gateway must apply documented input flags without inventing request fields. If the measured limit conflicts with normal chunk targets, the conflict needs explicit change control rather than over-limit indexing.

**Fallback / reversal trigger:** If the embedding tokenizer is unavailable, use a documented proxy and conservative, evidence-backed enforcement without claiming exact provider counts. If the limit or flag cannot be established, leave P0 incomplete rather than guess. Model/tokenizer/limit changes require recalculation, chunk/index regression tests, and an eval run.

**Required to resolve:** Current model documentation URLs/access dates, minimal real request/response evidence, measured maximum input tokens, observed query/passage requirements, tokenizer availability or documented proxy, and the resulting safe maximum recorded in versioned config. P2's no-over-limit gate supplies downstream verification.

**Resolution task / gate:** `P0-T05` measures the contract, with `P0-T04` gateway evidence and `P0-T08` recording the choice at the **P0 gate**. `P2-T04` implements counting/enforcement and `P2-T08` proves it.

**Evidence / proof / config:** No measured input limit or tokenizer result is asserted. Planned: [P0 smoke report/model-limit table](proof/P0/smoke_report.md), [raw recorded responses](proof/P0/), [`config/models.yaml`](config/models.yaml), and [P2 token histogram/no-over-limit proof](proof/P2/).

<a id="d-p0-05"></a>
### D-P0-05 — Rerank route, candidate capacity, and score scale

**Status:** open (**Open — P0 gate**)

**Owner:** Atharva

**PRD references:** [PRD §6](PRD.md#6-model-stack), [§7.4](PRD.md#74-retrieval), [§14 P0](PRD.md#p0-environment-and-smoke-tests), [§17](PRD.md#17-assumptions-to-verify-in-p0).

**Affected tasks:** `P0-T04`, `P0-T05`, `P0-T08`, `P3-T03`, `P3-T05`, `P3-T07`, `P3-T08`, `P5-T03`, `P5-T06`.

**Open question:** What is the current rerank request route and request/response shape, how many candidates can the endpoint accept, and what are its score scale and observed range? Can it support the fixed top-30 input/top-8 output pipeline directly or through a documented compatible gateway strategy? No route, capacity beyond the PRD requirement, or numeric score range is assumed.

**Rationale:** Rerank scores drive both candidate ordering and abstention, but score scales are endpoint-specific. P0 must establish the contract before P3 persists scores or P5 calibrates a threshold.

**Consequences:** The gateway, retrieval tests, trace schema, and calibration report depend on this resolution. The fixed `30 → 8` product semantics remain in force. A score range observed in P0 is documentation, not an abstention threshold. `P0-T05` must run a bounded preliminary embed-and-rerank quality check on Hindi and Marathi samples, recording the sample/expected-source selection, method, per-language results, and limitations. Successful requests alone are not quality evidence. This P0 risk check does not replace the fuller dedicated P5 evaluation under D-F11; observed weaknesses and follow-up must be documented rather than hidden.

**Fallback / reversal trigger:** If the named endpoint/route is unavailable or cannot support the required candidate contract, choose and record a compatible fallback at P0 rather than silently reducing candidates or disabling rerank. No-rerank remains an ablation only. Route/model/score-scale changes require P3 regression and P5 threshold recalibration.

**Required to resolve:** Current documentation URL/access date, recorded minimal request/response, exact route and parameters, candidate-capacity evidence relative to 30 inputs, score ordering/scale/range observations, and explicit compatibility/fallback rationale. Include the bounded preliminary Hindi/Marathi embed/rerank quality report with sample and expected-source selection, method, per-language results, and limitations; request success alone does not satisfy this requirement. P3 later proves actual top-30/top-8 behavior and persisted scores, while P5 performs the fuller multilingual evaluation.

**Resolution task / gate:** `P0-T05` owns measurements, `P0-T04` supplies gateway integration, and `P0-T08` records the resolution at the **P0 gate**. `P3-T03` validates pipeline behavior; `P5-T03` separately calibrates abstention.

**Evidence / proof / config:** No route or score range is asserted. Planned: [P0 smoke report/model-limit table](proof/P0/smoke_report.md), [P0 recorded responses](proof/P0/), [`config/models.yaml`](config/models.yaml), [P3 traces/retrieval report](proof/P3/), and [P5 calibration](proof/P5/baseline.md).

<a id="d-p0-06"></a>
### D-P0-06 — Measured quota/credits, batching, gateway controls, and terms

**Status:** open (**Open — P0 gate**)

**Owner:** Atharva

**PRD references:** [PRD §11](PRD.md#11-quota-and-rate-limits), [§12 privacy](PRD.md#12-non-functional-requirements), [§14 P0](PRD.md#p0-environment-and-smoke-tests), [§16 quota/privacy risks](PRD.md#16-risks), [§17](PRD.md#17-assumptions-to-verify-in-p0).

**Affected tasks:** `P0-T04`, `P0-T06`, `P0-T07`, `P0-T08`, `P2-T05`, `P2-T06`, `P2-T08`, `P7-T02`, `P7-T03`, `P7-T05`, `P7-T06`.

**Open question:** What are the actual per-model request limits, credit-consumption behavior, largest safe embedding batch, and appropriate token-bucket/circuit-breaker settings? What do the current free-tier and privacy terms say, and are all five hosted endpoints available without exhausted/gated credits? The reported **1,000 credits at signup** and **40 requests per minute per key** come from a third-party summary and remain unconfirmed until P0.

**Rationale:** The PRD estimates five calls per question—rewrite, embed, rerank, answer, verify—so a 40 RPM ceiling would be about 8 questions/minute with nothing else running. If credits are consumed per call, they cap total usage and ingestion embedding is the main spender. Actual limits and credit rules determine ingestion cost and load behavior. Terms determine privacy documentation but never override the confidential-indexing block.

**Consequences:** The gateway uses a per-model token bucket configured from measured limits, exponential backoff with jitter on 429 and 5xx, a circuit breaker per model, and automatic approved fallbacks. Embedding uses the largest batch the endpoint allows and caches by text hash. Reingestion should spend no embedding quota; ordinary tests use fixtures. P7 exposes quota/usage in a dashboard without revealing secrets. The P7 load test must use measured controls rather than assuming 40 RPM.

**Fallback / reversal trigger:** On throttling, use batching, caching, measured token buckets, backoff/jitter, and the PRD's smaller-test-corpus mitigation; activate named model fallbacks where applicable. Do not bypass provider limits or privacy controls. If credits/terms make a role unusable, record a P0 fallback or blockage. Changed terms/limits require new measurements, config/history updates, README updates, and load/eval evidence.

**Required to resolve:** A bounded **60-call burst** with a request/credit ledger, measured RPM and credit usage, endpoint batch limits and chosen batch settings, current endpoint/free-tier/privacy terms with source URLs and access dates, and gateway settings justified by those observations. P2 supplies a quota report and zero-call reingestion; P7 supplies the controlled 8-questions/minute load report.

**Resolution task / gate:** `P0-T06` owns the burst/ledger and offline backoff fixtures, `P0-T07` owns current terms and availability sources, `P0-T04` supplies call integration, and `P0-T08` records gateway decisions at the **P0 gate**.

**Evidence / proof / config:** No quota measurement or terms confirmation is asserted. Planned: [P0 smoke report, measured-limit table, burst ledger, and terms sources](proof/P0/smoke_report.md), [P0 raw call evidence](proof/P0/), [`config/models.yaml`](config/models.yaml), [P2 quota proof](proof/P2/), [P7 load/release proof](proof/P7/), and [README privacy notes](README.md).

### P1 gate records

<a id="d-p1-01"></a>
### D-P1-01 — Observed parser classes and chunk/exclusion mapping

**Status:** open (**Open — P1 gate**)

**Owner:** Atharva

**PRD references:** [PRD §7.1 FR-ING-4](PRD.md#71-ingestion), [§7.2 FR-CHK-1/2](PRD.md#72-chunking), [§14 P1](PRD.md#p1-ingestion-and-parsing), [§16 parser risk](PRD.md#16-risks).

**Affected tasks:** `P0-T03`, `P1-T04`, `P1-T07`, `P2-T01`, `P2-T02`, `P2-T03`, `P2-T08`.

**Open question:** Which semantic class names actually occur in real Nemotron-3.5-Parse output, and how does each observed class map to text, table, or chart chunk handling and to header/footer/page-number exclusion? No parser class inventory is invented from assumed labels.

**Rationale:** Chunking is class-aware, but the PRD deliberately defers exact class names to P1. Overlay and text review are needed to distinguish indexable content from retained-but-excluded page furniture.

**Consequences:** The resolved mapping drives deterministic P2 chunking and exclusion tests. Headers, footers, and page numbers remain in `blocks` even when excluded from the index. Every observed class needs an explicit disposition; table/chart handling continues to follow D-F05.

**Fallback / reversal trigger:** Ambiguous classes require raw-output/overlay review and a conservative documented mapping, not silent deletion. If Docling or another parser fallback is activated, obtain and review its real class inventory and remap before P2. New classes or mapping changes require chunk regression and evaluation with config hash/git SHA.

**Required to resolve:** Raw parse JSON for ten varied pages, corresponding overlays, manual text/bbox approval, an observed class inventory, and a class-to-chunk/exclusion mapping that covers the reviewed evidence and retains excluded blocks.

**Resolution task / gate:** `P1-T07` owns the overlay review and inventory, using `P1-T04` postprocessing; resolve at the **P1 gate** before class-dependent P2 implementation is accepted.

**Evidence / proof / config:** No observed parser class names are asserted. Planned: [P1 ten raw parse JSON files, overlays, review, and class inventory](proof/P1/), [P0 preliminary samples](proof/P0/), and [P2 mapping/chunk proof](proof/P2/).

<a id="d-p1-02"></a>
### D-P1-02 — Production parse concurrency and operating mode

**Status:** open (**Open — P1 gate**)

**Owner:** Atharva

**PRD references:** [PRD §6 parse settings](PRD.md#6-model-stack), [§7.1 FR-ING-8](PRD.md#71-ingestion), [§13 ablations](PRD.md#13-evaluation-plan), [§14 P1](PRD.md#p1-ingestion-and-parsing), [§16 parser risk](PRD.md#16-risks).

**Affected tasks:** `P0-T02`, `P0-T03`, `P1-T04`, `P1-T05`, `P1-T07`, `P1-T08`, `P5-T05`, `P7-T04`, `P7-T06`.

**Open question:** What production parse concurrency and parse operating mode should be selected from quality, throughput, and VRAM evidence? Benchmark concurrency **1, 2, 4, and 8**, starting from **4**; do not preselect a winner. Double-pass is the baseline, `guarded` addresses duplicate table hypotheses, and single-pass is the fast fallback.

**Rationale:** The 12 GB GPU imposes a real memory/parallelism constraint, while double-pass quality may affect tables/scans and downstream citations. The PRD requires both benchmark numbers and a reasoned selection.

**Consequences:** The chosen settings enter versioned parser configuration and operational docs. Quality evidence must accompany timing/VRAM, so a faster mode cannot be selected solely on throughput. P5 still runs the single-versus-double ablation once at baseline.

**Fallback / reversal trigger:** Duplicate table pollution activates `guarded`; acceptable quality/throughput evidence may select single-pass. GPU/OS failure uses Docling under D-F01. Parse outages pause jobs rather than justify unsafe concurrency. Runtime/GPU/model changes require a new benchmark and updated history before replacing the selected setting.

**Required to resolve:** A timing and VRAM table at concurrency 1/2/4/8, quality observations on the ten varied pages, duplicate-table behavior, and the selected concurrency/mode with an explicit reason. Failed-page retry/report and overlay acceptance remain separate P1 requirements.

**Resolution task / gate:** `P1-T08` owns the benchmark and selection, supported by `P1-T07` quality proof, at the **P1 gate**. `P5-T05` supplies the later parse-mode ablation, not a substitute for P1 evidence.

**Evidence / proof / config:** No production concurrency or mode is claimed as measured. Planned: [P1 timing/VRAM table, overlays, and selected-setting rationale](proof/P1/), [`config/models.yaml`](config/models.yaml), and [P5 single/double-parse ablation](proof/P5/baseline.md).

<a id="d-p1-03"></a>
### D-P1-03 — Collection-scoped duplicate reject-versus-link behavior

**Status:** open (**Open — P1 gate**)

**Owner:** Atharva

**PRD references:** [PRD §7.1 FR-ING-1](PRD.md#71-ingestion), [§8 documents/cache](PRD.md#8-data-model), [§9 upload route](PRD.md#9-api), [§11 caching/quota](PRD.md#11-quota-and-rate-limits).

**Affected tasks:** `P1-T01`, `P1-T02`, `P1-T05`, `P1-T06`, `P2-T06`, `P6-T02`, `P7-T01`.

**Open question:** Within one collection, after computing SHA-256 for an uploaded PDF/PNG/JPG, should a duplicate be **rejected** or **linked to the existing document**? Define the chosen upload response and library/status semantics before freezing the `POST /collections/{id}/documents` API contract. Do not invent a status code or response payload in advance. Duplicate scope is collection-scoped; this record does not create a global cross-collection policy.

**Rationale:** The PRD explicitly permits either behavior but requires predictable duplicate handling. The choice affects document identity, user feedback, storage, idempotency, and embedding-cache benefits while preserving collection isolation.

**Consequences:** Rejection would avoid a second collection-document instance and must communicate the existing duplicate clearly; linking would reuse existing parsed/indexed content and must define how the collection association and upload response are represented. Either implementation must avoid ambiguous repeated ingestion and preserve SHA-256 evidence, authorization, progress reporting, and cache correctness.

**Fallback / reversal trigger:** Before the API freeze, P1-T02 may select either PRD-permitted behavior based on the recorded contract tests. After freeze, switching behavior is a client-visible contract change requiring a superseding record, migration/compatibility analysis, and updated UI/API tests; it cannot be silently toggled.

**Required to resolve:** A written reject-or-link choice, example request/response contract, and tests covering identical content uploaded twice within a collection and collection-boundary behavior, with document identity, status/progress, storage, and reingestion/cache implications demonstrated. The choice must be recorded before the upload response contract is frozen.

**Resolution task / gate:** **`P1-T02` selects and records the behavior before API contract freeze**; this record's status becomes `resolved` only after its required proof and the **P1 gate** pass. `P6-T02` consumes the frozen behavior; `P7-T01` verifies authorization cannot bypass collection scope.

**Evidence / proof / config:** No duplicate behavior is selected yet. Planned: [P1 upload/contract test proof and recorded choice](proof/P1/), [P2 zero-call identical-reingestion evidence](proof/P2/), and later [P6 library behavior proof](proof/P6/).

### P5 gate records

<a id="d-p5-01"></a>
### D-P5-01 — Labeled abstention-threshold calibration

**Status:** open (**Open — P5 gate**)

**Owner:** Atharva

**PRD references:** [PRD §4 refusal/latency targets](PRD.md#4-success-metrics), [§7.4 FR-RET-5](PRD.md#74-retrieval), [§13](PRD.md#13-evaluation-plan), [§14 P5](PRD.md#p5-evaluation-and-tuning).

**Affected tasks:** `P3-T05`, `P3-T06`, `P3-T07`, `P3-T08`, `P4-T07`, `P5-T01`, `P5-T02`, `P5-T03`, `P5-T07`, `P6-T03`.

**Open question:** Which top-rerank-score threshold should skip generation and return a refusal? Select it from labeled final-gold-set results and the P0-established score semantics. No production threshold is chosen in this register or inferred from synthetic P3 tests.

**Rationale:** Abstention trades unsupported-answer avoidance against useful answer coverage. A threshold is meaningful only relative to the selected reranker, score scale, labeled answerable/unanswerable examples, and measured system metrics.

**Consequences:** P3-T05 builds and fixture-tests the abstention mechanism without guessing a production value. P5 records the selected threshold in versioned config and reports selection behavior. The threshold affects refusal accuracy, answer coverage, unsupported claims, and latency; later reranker/score changes require recalibration.

**Fallback / reversal trigger:** If no candidate threshold meets the targets, document the trade-off and miss under D-P5-03 with cause, user impact, and follow-up; do not silently lower a target or ship an arbitrary value. Rerank model, route, score-scale, retrieval, or gold-set changes require a fresh calibration and eval run before replacing the threshold.

**Required to resolve:** Labeled calibration data, the P0 score-scale contract, a threshold selection-curve report, and resulting retrieval/refusal/answer metrics with config hash/git SHA. Include unanswerable and Hindi/Marathi behavior and link the final baseline comparison.

**Resolution task / gate:** `P5-T03` owns labeled calibration and the selection-curve report; `P5-T02` supplies metrics and `P5-T07` records target outcomes. Resolve at the **P5 gate**.

**Evidence / proof / config:** No calibrated threshold is asserted. Planned: [P3 mechanism/draft traces](proof/P3/), [P5 selection-curve report and error analysis](proof/P5/), [`proof/P5/baseline.md`](proof/P5/baseline.md), and [`config/retrieval.yaml`](config/retrieval.yaml).

<a id="d-p5-02"></a>
### D-P5-02 — Fuzzy quote-threshold calibration around default 92

**Status:** open (**Open — P5 gate**)

**Owner:** Atharva

**PRD references:** [PRD §7.5 FR-GEN-3](PRD.md#75-generation), [§7.6 FR-VER-2](PRD.md#76-verification), [§13](PRD.md#13-evaluation-plan), [§14 P4–P5](PRD.md#p4-generation-and-verification), [§16 verifier risk](PRD.md#16-risks).

**Affected tasks:** `P4-T03`, `P4-T05`, `P4-T08`, `P5-T01`, `P5-T02`, `P5-T04`, `P5-T06`, `P5-T07`, `P6-T04`.

**Open question:** Should the initial fuzzy quote threshold of **92 partial ratio** be retained or changed based on P5 calibration? Normalization remains Unicode NFKC, whitespace, and case on both sides; the quote remains at most 25 words and tied to the cited chunk. No replacement number is guessed.

**Rationale:** A quote threshold that is too strict can remove supported claims; one that is too lenient can admit inaccurate citations. Calibration must measure both behaviors, including multilingual text, while preserving the rule that failed quotes are unsupported.

**Consequences:** P4 starts with configured default 92 and regression-tests normalization/matching. P5 must explicitly retain or change it with evidence. Changing it does not relax structural/context-ID checks or permit a failed-quote answer to display; it prompts a new verifier audit and evaluation row.

**Fallback / reversal trigger:** In the absence of evidence for a change, retain 92 as the initial default pending explicit P5 resolution. If calibration cannot meet citation/unsupported-claim goals, record the miss and follow-up under D-P5-03 rather than silently relaxing matching. Parser/chunking/normalization changes require recalibration and full applicable evaluation.

**Required to resolve:** Quote-match calibration around default 92 with false-accept/false-reject analysis, regression tests, multilingual evidence, verifier removal/audit results, and resulting citation precision/recall and unsupported-claim metrics with config hash/git SHA.

**Resolution task / gate:** `P5-T04` owns calibration and regression evidence; `P4-T03` supplies the implementation and `P4-T08` the draft answer/removal audit. Resolve at the **P5 gate**, with target review in `P5-T07`.

**Evidence / proof / config:** No calibrated replacement for 92 is asserted. Planned: [P4 quote/removal proof](proof/P4/), [P5 calibration and regression results](proof/P5/), [`proof/P5/baseline.md`](proof/P5/baseline.md), and [versioned verification config](config/).

<a id="d-p5-03"></a>
### D-P5-03 — Metric misses and evidence-backed target recalibration

**Status:** open (**Open — P5 gate**)

**Owner:** Atharva

**PRD references:** [PRD §4](PRD.md#4-success-metrics), [§13](PRD.md#13-evaluation-plan), [§14 P5](PRD.md#p5-evaluation-and-tuning), [§15](PRD.md#15-engineering-process), [§16 multilingual/verifier risks](PRD.md#16-risks).

**Affected tasks:** `P3-T08`, `P4-T08`, `P5-T01`, `P5-T02`, `P5-T03`, `P5-T04`, `P5-T05`, `P5-T06`, `P5-T07`, `P7-T06`, `P7-T07`.

**Open question:** Does the final baseline meet every PRD §4 target? For any miss, what is the measured cause, user impact, and follow-up, and should the miss be documented or the initial target recalibrated at P5 with evidence? No miss, waiver, or new target is pre-authorized.

**Rationale:** The PRD calls the targets initial and allows recalibration only after the P5 baseline, never silently. A single register entry must make every deviation visible and preserve the original measured baseline for later release decisions.

**Consequences:** `P5-T07` records a per-target outcome: met, or missed with cause and explicit decision. Accepted limitations must be represented in release documentation and owned follow-up. Recalibration does not erase the original target, baseline, config hash, or git SHA. P7 repeats final evaluation and cannot rely on an undocumented P5 waiver.

**Fallback / reversal trigger:** A metric miss triggers worst-case error analysis, ablation/judge/audit evidence where relevant, and a fix or documented P5 decision. P3's draft-recall diagnosis is not target recalibration. Post-P5 evidence may document improved compliance or trigger remediation, but cannot accept a new miss or recalibrate a target outside P5. Any target change requires a formally reopened P5 gate, fresh evidence, Atharva's approval, and superseding history; never rewrite the old baseline as though it passed.

**Required to resolve:** [`proof/P5/baseline.md`](proof/P5/baseline.md) with all eight metrics against §4, `eval_runs` rows with config hash/git SHA, worst-15 error analysis, required ablations, Ultra judging with 20% human audit and every disagreement, separate Hindi/Marathi results, and a cause/user-impact/follow-up statement for every miss or recalibration.

**Resolution task / gate:** `P5-T07` owns target comparison and decisions, using `P5-T02` metrics and `P5-T06` judge/audit results. Resolve at the **P5 gate**; `P7-T07` verifies final release evidence.

**Evidence / proof / config:** No baseline outcome or target change is asserted. Planned: [`proof/P5/baseline.md`](proof/P5/baseline.md), [P5 eval/error/ablation artifacts](proof/P5/), [P7 final evaluation and release audit](proof/P7/), and [versioned config](config/).

## 6. Fallback and change-control matrix

This matrix is an operational index, not permission to bypass the detailed records or gates. All config/model/prompt/threshold/chunking changes also follow §2 and the resolved-history rules.

| Area / trigger | Required response | Evidence and change control | Record(s) |
| --- | --- | --- | --- |
| Parser fails on RTX 5070/OS stack | Investigate WSL2 versus native Linux; use Docling if it fails on this stack; check hosted parse only if available. | P0 raw samples/overlays and smoke report; record fallback/config. Re-review P1 overlays/classes. | [D-F01](#d-f01), [D-P0-01](#d-p0-01), [D-P1-01](#d-p1-01) |
| Duplicate table hypotheses pollute index | Use `guarded` merge; single-pass remains the fast fallback. | P1 quality/VRAM/throughput evidence; P5 single/double ablation. | [D-F04](#d-f04), [D-P1-02](#d-p1-02) |
| Parse page fails | Retry twice, mark only that page failed, preserve document/job resumability. Parse outage pauses jobs. | P1 retry/failure/outage/restart proof and visible page status. | [D-F04](#d-f04), [D-F10](#d-f10) |
| Super VL changes or is withdrawn | Use llama-3.3-nemotron-super-49b-v1.5. | Initial P0 activation uses availability smoke/config evidence; subsequent changes require an eval run with config hash/git SHA. | [D-F03](#d-f03), [D-P0-02](#d-p0-02) |
| Verify too slow or rate limited | Use Lightning with a lower claim batch size; retain every verification/policy check. | P0/P4 recorded behavior, latency/audit output, eval on model change. | [D-F03](#d-f03), [D-F08](#d-f08) |
| Hosted 429/5xx or model circuit opens | Apply measured per-model token bucket, exponential backoff with jitter, circuit breaker, and approved fallback. | P0 60-call ledger/settings; offline fixtures for ordinary tests; P7 controlled load report. | [D-P0-06](#d-p0-06) |
| Embedding dimension unknown/incompatible with pgvector | Keep Qdrant default. Use pgvector only when measured dimension fits and P0 explicitly selects the simplification. | First response/dimension and store rationale; P2 payload/filter/provenance proof; migration/eval on later change. | [D-P0-03](#d-p0-03), [D-F09](#d-f09) |
| Embedding tokenizer unavailable | Use a documented proxy and an evidence-backed safe maximum below the measured input limit. | P0 tokenizer/limit evidence; P2 histogram and no-over-limit gate. Never invent an input flag. | [D-P0-04](#d-p0-04), [D-F05](#d-f05) |
| Rerank route/capacity/score unknown | Keep P0 open until real route, capacity, ordering, and scale are recorded; select a compatible fallback if needed. | P0 request/response and model docs; P3 `30 → 8` proof; P5 recalibration after score/model change. | [D-P0-05](#d-p0-05), [D-F06](#d-f06) |
| Draft P3 Recall@8 below 0.85 | Write diagnosis and fix plan; do not lower the final ≥0.90 target. | P3 retrieval report/ablations and linked follow-up. | [D-F06](#d-f06), [D-F11](#d-f11) |
| Answer JSON invalid | Make exactly one automatic repair attempt, then show failure. | P4 schema/repair tests and recorded failures; no best-effort unverified display. | [D-F07](#d-f07) |
| Quote fails or claim is unsupported | Mark/remove the claim under policy; never display a failed-quote claim. | P4 matcher/verifier/removal audit; P5 quote calibration and eval. | [D-F08](#d-f08), [D-P5-02](#d-p5-02) |
| More than 30% of claims removed | Regenerate once with a stricter prompt, then rerun the same checks. | P4 both-pass verifier outputs and removal reasons; prompt/eval change control. | [D-F08](#d-f08) |
| Every factual claim removed / context below abstention threshold | Return an honest refusal; do not synthesize an answer. | P4 refusal examples; P5 labeled abstention calibration and refusal metrics. | [D-F06](#d-f06), [D-F08](#d-f08), [D-P5-01](#d-p5-01) |
| No single block matches a surviving quote | Return all blocks of the cited chunk; show the verbatim quote beside block-level highlight. | P4 citation-resolution audit and P6 highlight checks; do not claim word-level precision. | [D-F08](#d-f08), [D-F01](#d-f01) |
| Parser errors on scans/tables or block highlight is coarse | Use double-pass/overlay review, preserve table HTML, and display quote with highlight. | P1 ten-page manual review; P2 table proof; P6 20/20 highlight gate. | [D-F04](#d-f04), [D-F05](#d-f05), [D-F11](#d-f11) |
| Verifier errs | Retain structural/quote/entailment controls and audit false support/removal; verifier off only for evaluation ablation. | P4 removal log; P5 human audit, verifier-off ablation, and error analysis. | [D-F08](#d-f08), [D-F11](#d-f11) |
| Hindi/Marathi retrieval or answer quality is weaker | Report the dedicated subset separately; tune or document limitations, never hide them in aggregate metrics. | Final gold set has at least ten Hindi/Marathi questions; P5 subset results and miss decisions. | [D-F11](#d-f11), [D-P5-03](#d-p5-03) |
| Confidential collection marked or privacy terms unclear | Block hosted indexing until a local model path exists; keep secrets server-side and out of logs/browser. | P0 terms sources; P1/P7 block/authorization/secret tests; README warning. | [D-F10](#d-f10), [D-P0-06](#d-p0-06) |
| Duplicate upload within collection | Apply the P1-T02-selected reject-or-link behavior only after contract evidence; do not switch silently after freeze. | P1 contract/tests and migration/compatibility review for later changes. | [D-P1-03](#d-p1-03) |
| Any P5 metric misses its target | Document cause, user impact, decision, and follow-up; recalibrate only at P5 with evidence. | Full baseline, eval config hash/git SHA, worst-15 analysis; history entry and final release re-evaluation. | [D-P5-03](#d-p5-03), [D-F11](#d-f11) |
| Optional P7 stretch is incomplete or rejected | Keep it out of core release; evaluate DOCX/PPTX conversion, page-image retrieval, and answer cache independently. | Optional `P7-T08` proof only when attempted; no core-gate waiver is needed because stretch is non-blocking. | [D-F01](#d-f01), [D-F11](#d-f11) |

## 7. Resolved and superseded history conventions

No resolved or superseded implementation history exists at initialization. The accepted D-F records are the PRD baseline, and all D-P0/D-P1/D-P5 records are open. Entries are added only when a decision is actually resolved or superseded; planned proof must not be relabeled as observed evidence.

### Resolving an open record

1. Complete the named resolving task and gate, then preserve the original **Open question**, PRD references, and rationale.
2. Change `open` to `resolved`, add the measured decision and resolution date, and link the actual committed proof and versioned config. Replace no longer applicable “planned” wording for the evidence used, while leaving future proof destinations clearly planned.
3. Record the resolving task/gate, acceptance result, source URLs/access dates where applicable, and any active fallback. Initial P0/P1 model, fallback, parser-class, and class-to-chunk mapping selections record their gate evidence and applicable config/version identifiers; they do not require a future full evaluation baseline. For subsequent model, prompt, threshold, or chunking changes, include the eval run, **config hash**, and **git SHA**.
4. Append a history row using the convention below. Do not fabricate retrospective dates, results, provider values, or proof paths.

| Date | Record | Resolution / supersession and rationale | Resolving task / gate | Observed proof and config | Eval run / config hash / git SHA |
| --- | --- | --- | --- | --- | --- |

### Superseding a decision

- Keep the old ID, title, original decision/question, evidence, and history. Set its status to `superseded` and link its successor.
- Give the successor a new stable decision ID, link back to the predecessor, and explain the new evidence, trigger, user/compatibility impact, migration, and fallback. Do not overwrite history to make an old choice look correct.
- For a PRD-fixed change, obtain Atharva's approval and update the requirements authority through the normal change process. For an evidence-gated change, repeat the required measurement/gate or document why a later phase is the proper authority.
- Attach the mandatory eval run/config hash/git SHA for model, prompt, threshold, or chunking changes. Rerun affected parser overlays, provenance checks, API/UI tests, load tests, or release checks even when no eval is otherwise required.
- If a target is recalibrated at P5 or a formally reopened P5 gate, preserve both the original and new targets and the P5 cause/user-impact/follow-up analysis in D-P5-03. Never silently lower targets or convert an evaluation-only ablation into a production bypass.
