# CiteRAG: Product Requirements Document

Owner: Atharva. Version 1.0. 15 Nov 2026. Status: ready for build. CiteRAG is a working title.

## 1. Summary

CiteRAG answers questions over uploaded documents. Every claim in an answer carries a citation to the document, page, and highlighted region it came from, and every citation is machine-checked before the user sees it. Parsing runs locally on an RTX 5070 (12 GB). All other models run on NVIDIA NIM free hosted endpoints.

## 2. Goals and non-goals

**Goals**

- G1. Accurate references: each claim maps to a document, page, block bounding box, and a verbatim quote.
- G2. Detailed explanations: a short summary followed by a structured explanation, grounded only in retrieved text.
- G3. Honest refusal: if the sources do not answer the question, say so.
- G4. Handle scanned and digital PDFs, tables, and charts, with English, Hindi, and Marathi documents in the test set.
- G5. Run on the free NIM tier plus one consumer GPU.

**Non-goals for v1**

- Multi-tenant SaaS, billing, collaboration.
- Web search, agents, model fine-tuning.
- Input formats beyond PDF, PNG, and JPG. DOCX and PPTX are a P7 stretch via PDF conversion.
- Word-level highlighting. Highlight granularity is the parsed block.

## 3. Users and use cases

Primary user: the owner, a single technical user. Secondary: analysts who read long reports and need to verify claims fast.

- UC1. Ask a factual question and see the source passage.
- UC2. Ask for a value from a table and get the exact cell region cited.
- UC3. Ask a question that spans several documents in a collection.
- UC4. Click a citation and land on the highlighted region in the PDF.
- UC5. Ask something the documents do not cover and get a clear refusal.

## 4. Success metrics

Targets are initial. They are recalibrated after the P5 baseline, never silently lowered.

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

## 5. Architecture

**Ingestion path** Upload, then file store, then Celery job: render pages, parse with Nemotron-3.5-Parse, postprocess into blocks, chunk, embed via NIM, write to Qdrant and Postgres.

**Query path** Question, rewrite, hybrid retrieval, rerank, context assembly, answer generation, verification, citation resolution, response.

| Component | Technology | Role |
| --- | --- | --- |
| Web | Next.js 15 App Router, TypeScript, pdf.js | Chat, library, PDF viewer with highlights |
| API | FastAPI | REST, SSE status events, auth |
| Workers | Celery and Redis | Ingestion jobs, retries |
| Parse service | vLLM serving Nemotron-3.5-Parse on the local GPU | Page images to structured blocks |
| Relational store | PostgreSQL | Metadata, blocks, chunks, full-text index, conversations |
| Vector store | Qdrant | Dense vectors with payload |
| NIM gateway | Python module in the API package | Single place for all hosted model calls, rate limiting, retries, caching |
| Packaging | Docker Compose | Everything except the GPU parse service, which may run in WSL2 directly |

Qdrant is chosen over pgvector because the embed-8B output dimension is unknown until P0, and pgvector indexes cap dimensions. If P0 shows the dimension fits, pgvector is an allowed simplification, decided at the P0 gate.

## 6. Model stack

| Stage | Model | Runs on |
| --- | --- | --- |
| Parse | Nemotron-3.5-Parse, 0.631B parameters | Local, RTX 5070 12 GB |
| Embed | nemotron-3.5-embed-8b | NIM hosted |
| Rerank | nemotron-3.5-rerank-8b | NIM hosted |
| Query rewrite | nemotron-3.5-lightning-30b-a3b | NIM hosted |
| Answer | nemotron-3.5-super-vl-120b-a12b | NIM hosted |
| Verify | nemotron-3-ultra-550b-a55b | NIM hosted |

**Settings**

- Parse: double-pass mode, pages rendered at 150 dpi, merge policy `guarded` if duplicate table hypotheses pollute the index. Single-pass is the fast fallback.
- Rewrite: low temperature, short output, runs only when the conversation has prior turns or the query is under-specified.
- Answer: reasoning off, JSON output per section 10, temperature at or near 0.
- Verify: one batched call per answer, all claims together. Reasoning on with a token budget if the endpoint supports it.
- Rerank: 30 candidates in, 8 out.

**Fallbacks**

- Parse fails on this GPU or OS stack: Docling.
- Super VL changes or is withdrawn (it is labeled early access): llama-3.3-nemotron-super-49b-v1.5.
- Verify too slow or rate limited: Lightning, with a lower claim batch size.

Exact model ID strings, request parameters (for example any input type flag on embeddings), and the rerank route are read from each model's page on build.nvidia.com during P0 and recorded in `config/models.yaml`. Nothing is hardcoded from memory.

## 7. Functional requirements

### 7.1 Ingestion

- FR-ING-1. Accept PDF, PNG, JPG up to a configurable size cap. Compute SHA-256; reject or link duplicates within a collection.
- FR-ING-2. Render each PDF page to RGB with PyMuPDF at 150 dpi. If the render exceeds 1664 x 2048 pixels, downscale to fit, keeping aspect ratio. A4 and Letter at 150 dpi already fit. Store the actual render size per page.
- FR-ING-3. Parse each page with the exact task prompt `</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>` and `max_new_tokens` of 8744. Over vLLM use temperature 0, `top_k` 1, `repetition_penalty` 1.1, and `skip_special_tokens` false so control tokens are preserved.
- FR-ING-4. Keep the raw model output for every page. Run `postprocess_document` with the render size to get markdown and blocks carrying class, normalized bbox, `bbox_pixels`, and text.
- FR-ING-5. Convert bbox pixels to PDF points as `pixels * 72 / render_dpi`, adjusted for any downscale factor. Store both forms.
- FR-ING-6. Per-page status and retry. A failed page is retried twice, then marked failed without failing the document. Jobs are idempotent and resumable from the last good page.
- FR-ING-7. Expose ingestion progress per document: queued, rendering, parsing, chunking, embedding, indexed, failed, with page counts.
- FR-ING-8. Parse service concurrency starts at 4 requests and is tuned in P1 from measured throughput and VRAM.

### 7.2 Chunking

- FR-CHK-1. Chunk from parsed blocks, not raw text. Use the semantic classes the parser returns. The exact class names are recorded in P1 from real output.
- FR-CHK-2. Exclude page headers, footers, and page numbers from the index but keep them in the blocks table.
- FR-CHK-3. Target 400 to 800 tokens per text chunk with about 12% overlap, splitting on block and paragraph boundaries. Never cut inside a block unless the block alone exceeds the maximum.
- FR-CHK-4. A table is one chunk. If it exceeds 1,200 tokens, split by rows and repeat the header row in each part. Store the table HTML for display and a flattened row-wise text form for embedding and lexical search.
- FR-CHK-5. A chart block becomes one chunk from its extracted data and caption.
- FR-CHK-6. Prepend the section path (for example `Report > 3 Risks > 3.2 Credit`) to the embedded text, not to the displayed text.
- FR-CHK-7. Heuristic continuation: if a table or a paragraph continues across a page break, link the chunks with `continues_from`. The parser does not infer cross-page continuations, so this is our logic and is evaluated in P2.
- FR-CHK-8. Every chunk stores its source blocks, page numbers, and bboxes, so any chunk can be drawn on the PDF.
- FR-CHK-9. Token counts use the embedding model's tokenizer if available, otherwise a documented proxy. Chunk maximum stays below the embed model's input limit, read in P0.

### 7.3 Indexing

- FR-IDX-1. Embed chunk text in batches through the NIM gateway. Vector size is read from the first API response, never assumed.
- FR-IDX-2. Qdrant payload: `chunk_id`, `doc_id`, `collection_id`, `page_start`, `page_end`, `section_path`, `chunk_type`, `lang`.
- FR-IDX-3. Postgres full-text index (`tsvector`) over chunk text for lexical search. Use the `simple` configuration so Hindi and Marathi tokens are not dropped.
- FR-IDX-4. Embedding results are cached by text hash so re-ingestion costs no quota.

### 7.4 Retrieval

- FR-RET-1. Rewrite the question into a standalone query using the last few turns. Keep the original for display.
- FR-RET-2. Dense search top 40 and lexical search top 40, both restricted to the selected collection or documents.
- FR-RET-3. Merge with Reciprocal Rank Fusion, constant 60.
- FR-RET-4. Rerank the top 30 merged candidates, keep the top 8.
- FR-RET-5. Abstention gate: if the top rerank score is below a threshold, skip generation and return a refusal. The threshold is calibrated on the eval set in P5, not guessed.
- FR-RET-6. Context assembly: label chunks C1 to C8, add neighbor chunks only when linked by `continues_from`, cap context at a configured token budget.

### 7.5 Generation

- FR-GEN-1. The prompt instructs the model to answer only from labeled context, to cite a chunk ID and a verbatim quote for every factual sentence, and to abstain when the context is insufficient.
- FR-GEN-2. Output is JSON matching the schema in section 10. Invalid JSON gets one automatic repair attempt, then a failure state shown to the user.
- FR-GEN-3. Quotes are at most 25 words and must be exact text from the cited chunk.

### 7.6 Verification

- FR-VER-1. Structural check: JSON valid, every cited chunk ID was in the provided context.
- FR-VER-2. Quote check: normalize both sides (Unicode NFKC, whitespace, case) and require a fuzzy match at or above a configured threshold (default 92 partial ratio) against the cited chunk text. Failing quotes mark the claim unsupported.
- FR-VER-3. Entailment check: one batched Ultra call returns `supported`, `partial`, or `unsupported` per claim with a one-line reason.
- FR-VER-4. Policy: unsupported claims are removed from the displayed answer. Partial claims stay with a visible badge. If every factual claim is removed, return a refusal. If more than 30% were removed, regenerate once with a stricter prompt, then apply the same checks.
- FR-VER-5. Citation resolution: for each surviving claim, find the block inside the cited chunk that best matches the quote and return its page and bbox. If no single block matches, return all blocks of the chunk.
- FR-VER-6. Persist the verifier output with the answer for audit and evaluation.

### 7.7 Frontend

- FR-UI-1. Library: upload, per-document ingestion progress, delete, collections.
- FR-UI-2. Chat: question box, status line driven by SSE events (rewriting, retrieving, reranking, answering, verifying), then the verified answer. The answer is shown only after verification, so token streaming is not used for the answer text.
- FR-UI-3. Answer layout: summary, detailed explanation, numbered sources list with document, page, and quote.
- FR-UI-4. Inline citation chips. Clicking one opens the PDF viewer at the page with the block bbox highlighted. Multiple citations on one sentence open a chooser.
- FR-UI-5. Badges for partial claims, and a clear state for refusals and failures.
- FR-UI-6. Table citations render the stored table HTML in a side panel next to the highlighted page.

## 8. Data model

PostgreSQL, key columns only.

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

`trace_json` records stage latencies, call counts, model IDs, and retrieved chunk IDs with scores for every query.

## 9. API

- `POST /auth/register`, `POST /auth/login`
- `GET/POST /collections`
- `POST /collections/{id}/documents` multipart upload, returns document ID
- `GET /documents/{id}` status and page progress
- `GET /documents/{id}/file` original file for the viewer
- `GET /documents/{id}/pages/{n}/blocks` blocks with bboxes
- `DELETE /documents/{id}`
- `POST /chat` body: collection\_id, conversation\_id, question, optional doc\_ids. Returns an SSE stream of status events, then a final `answer` event.
- `GET /conversations/{id}/messages`
- `GET /health` including parse service, Qdrant, Postgres, and NIM reachability

## 10. Output schemas

**Answer JSON**

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

Every `claim` needs at least one chunk ID and a quote. `connective` sentences may not contain facts. The summary is composed only from claims that survive verification.

**Verifier JSON**

```json
{
  "results": [
    { "claim_index": 0, "verdict": "supported", "reason": "string" }
  ]
}
```

## 11. Quota and rate limits

- Reported free tier: 1,000 credits at signup and 40 requests per minute per key. This comes from a third-party summary and must be confirmed in P0. If credits are consumed per call, they cap total usage and ingestion embedding is the main spender.
- Calls per question: rewrite, embed, rerank, answer, verify, so 5. At 40 RPM that is about 8 questions per minute with nothing else running.
- The NIM gateway enforces a token bucket per model, configured from the measured limit, with exponential backoff and jitter on 429 and 5xx, a circuit breaker per model, and automatic fallback per section 6.
- Ingestion embeds in the largest batch the endpoint allows and caches by text hash.
- Tests use recorded fixtures so the suite does not spend quota.

## 12. Non-functional requirements

- **Privacy.** Chunk text and questions are sent to hosted NVIDIA endpoints. The free trial terms may permit NVIDIA to record inputs. Do not index confidential documents on this tier. Confirm the current terms in P0 and document them in the README.
- **Secrets.** API keys come from environment variables, are never logged, and never reach the browser.
- **Observability.** Structured JSON logs with a trace ID per request and per ingestion job. Per-stage latency and call counts in `trace_json`.
- **Reliability.** Ingestion survives worker restarts. A parse service outage pauses jobs instead of failing them.
- **Reproducibility.** All thresholds, model IDs, and prompts live in versioned config. Each eval run records the config hash and git SHA.
- **Portability.** `docker compose up` starts everything except the GPU parse service, which has its own documented start script.
- **Platform.** The parser supports Linux only. On Windows, use WSL2 with GPU passthrough.

## 13. Evaluation plan

**Gold set.** 60 to 100 questions written from the owner's own documents, each with the expected answer and the expected source page and block.

- About 35% factoid, 25% table lookup, 15% multi-passage, 10% cross-document, at least 15% unanswerable.
- At least 10 questions on Hindi or Marathi documents.

**Metrics.** Recall@k and MRR at chunk and page level, citation precision and recall, unsupported claim rate, refusal accuracy, answer correctness, latency per stage.

**Method**

- Retrieval metrics are computed without the LLM, from stored traces.
- Answer correctness uses an Ultra judge against gold answers, with a manual audit of 20% of items and every disagreement.
- Ablations run once at baseline: no rerank, no hybrid, single versus double parse pass, verifier off, to show what each stage earns.
- Every change to chunking, thresholds, or prompts reruns the suite and stores a row in `eval_runs`.

## 14. Delivery phases

Each phase has a gate. A phase is not complete, and the next does not start, until its proof-of-work artifacts are committed under `proof/Pn/` and acceptance criteria pass.

### P0. Environment and smoke tests

Scope: GPU stack, parse service, all hosted models.

- Install CUDA and a PyTorch and vLLM build that supports the RTX 5070 under WSL2 or Linux. Serve Nemotron-3.5-Parse.
- Parse 3 sample pages (digital, scanned, table-heavy) end to end.
- Call each hosted model once with a minimal request. Record model ID strings, request shapes, embedding dimension, embed input limit, rerank route and score range, reasoning controls.
- Measure real rate limit and credit consumption with a 60-call burst.
- Confirm free-tier terms and the current status of each free endpoint.
- Decide Qdrant versus pgvector from the dimension.

Proof: `proof/P0/smoke_report.md`, raw parse outputs, one overlay PNG per sample page, a table of model IDs and measured limits, `config/models.yaml`. Gate: all six models respond, or fallbacks are chosen and recorded.

### P1. Ingestion and parsing

- Upload, store, render, parse, postprocess, persist pages and blocks. Per-page retries and status.
- Bbox overlay tool that draws stored blocks on the rendered page.
- Record the semantic class names seen in real output.

Proof: overlays for 10 varied pages, parse JSON for each, a timing and VRAM table at concurrency 1, 2, 4, 8, and the chosen concurrency with the reason. Gate: parsed text matches the source on the 10 pages on manual review, bboxes land on the right regions, failed pages are retried and reported.

### P2. Chunking and indexing

- Block-based chunker, table and chart handling, section paths, continuation linking.
- Embedding through the gateway with cache, Qdrant and Postgres writes.

Proof: chunk dump for 3 documents, histogram of token counts, a list of 10 table chunks with their HTML, quota usage report. Gate: no chunk exceeds the embed limit, every chunk maps back to blocks and bboxes, re-ingest of the same file spends zero embedding calls.

### P3. Retrieval

- Rewrite, hybrid search, RRF, rerank, abstention gate, context assembly.
- Retrieval-only eval harness.

Proof: first gold set draft, retrieval metrics report, ablation table for hybrid and rerank. Gate: Recall@8 at or above 0.85 on the draft set, or a written diagnosis and fix plan.

### P4. Generation and verification

- Answer prompt, JSON parsing and repair, three-stage verifier, citation resolution, refusal paths.

Proof: 30 recorded answers with verifier output, a list of every claim the verifier removed with the reason, 5 refusal examples. Gate: citation precision and unsupported claim rate measured on the draft set, and no answer is shown that failed the quote check.

### P5. Evaluation and tuning

- Final gold set, full metric run, ablations, threshold calibration for abstention and quote matching.
- Hindi and Marathi subset results.

Proof: `proof/P5/baseline.md` with all metrics against section 4 targets, `eval_runs` rows, error analysis of the worst 15 questions. Gate: targets met, or each miss documented with cause and decision. Targets are only changed here, with the reason written down.

### P6. Web UI

- Library, chat, SSE status, citation chips, PDF viewer highlight, table side panel, badges.

Proof: screen recording of the five use cases, a Playwright test that clicks a citation and asserts the highlight position. Gate: highlight lands on the correct block for 20 of 20 sampled citations.

### P7. Hardening and release

- Auth, per-user collections, quota dashboard, structured logging, Compose setup, README with setup and privacy notes.
- Stretch: DOCX and PPTX through PDF conversion, page-image retrieval with the multimodal embed and rerank, answer cache.

Proof: clean-machine setup log, load test at 8 questions per minute, final eval run. Gate: fresh clone reaches a working answer by following the README only.

## 15. Engineering process

- `TASKS.md` at repo root. Task IDs `P{phase}-T{nn}`, each with status, owner, and a link to its proof artifact.
- Commits follow `type(P1-T03): message`, where type is feat, fix, test, docs, or chore. One task per commit where possible.
- Agent deviations are caught by comparing the code and proof artifacts against `TASKS.md`, not against the agent's summary.
- CI runs unit tests on every push: chunker, bbox conversion, quote matcher, RRF, JSON repair. Hosted-model tests use recorded fixtures.
- Pull requests that change prompts, thresholds, or chunking attach an eval run.

## 16. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Parser does not run cleanly on the RTX 5070 stack | Blocks ingestion | P0 smoke test first, Docling fallback, hosted parse endpoint checked if available |
| Free credits or 40 RPM cap throttle ingestion and queries | Slow or blocked use | Measure in P0, batching, caching, token bucket, smaller test corpus |
| Early-access Super VL changes or disappears | Answer quality shift | Pinned config, fallback model, eval rerun on any change |
| Parser errors on tables or scans propagate to wrong answers | Wrong citations | Overlay review in P1, table chunks stored with HTML, double-pass mode |
| Block-level highlight is coarser than the cited sentence | Reduced precision for the reader | Show the verbatim quote next to the highlight |
| Verifier model errs | False support or false removal | Audit sample in P5, two independent checks before display |
| Embed or rerank quality weaker on Hindi and Marathi than English | Poor recall on those docs | Dedicated eval subset, report separately, tune or document limits |
| Confidential documents leave the machine | Privacy breach | README warning, collection-level flag blocks indexing of marked documents until a local model path exists |

## 17. Assumptions to verify in P0

- Free endpoints for all five hosted models remain available and not gated behind credits that run out.
- Embedding dimension, maximum input tokens, and any query versus passage input flag.
- Rerank request route, candidate limit, and score scale.
- Whether reasoning can be disabled or budgeted per request on Super VL and Ultra.
- Embed and rerank multilingual quality on Hindi and Marathi.
- Blackwell compatibility of the vLLM and CUDA stack under WSL2.

## 18. Repository layout

```
citerag/
  TASKS.md
  README.md
  config/            models.yaml, retrieval.yaml, prompts/
  apps/
    api/             FastAPI app, routers, nim_gateway, verifier
    worker/          Celery tasks: render, parse, chunk, embed
    parse_service/   vLLM start script and client wrapper
    web/             Next.js 15 app
  packages/
    chunking/        block-based chunker
    eval/            gold set, metrics, ablation runner
  proof/             P0 to P7 artifacts
  docker-compose.yml
```
