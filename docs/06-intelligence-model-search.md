# Intelligence: Models, Search, And Crawling

## 1. Intelligence Decision

The lightweight server orchestrates intelligence. It does not run heavy local
models by default.

Use:

- OpenAI-compatible model gateway for model calls;
- TrendRadar for trends, RSS, hot lists, and public-opinion inputs;
- FunASR as optional ASR for audio transcription and voice-command input;
- MinerU as optional document parsing for PDF, image, and Office ingestion;
- SearXNG as optional self-hosted metasearch;
- Sonic as optional local internal search for our own documents, notes, logs,
  and task records;
- Firecrawl or equivalent API for page extraction when needed;
- OCR or multimodal APIs for image/document understanding;
- local Whisper only as a transitional lightweight ASR path.

## 2. Model Gateway

The model gateway hides provider details behind one compatible contract.

Model slots:

- fast model for quick replies;
- summary model for reports;
- reasoning model for final judgment;
- vision model for image/document understanding;
- embedding/rerank provider when needed by memory search.

Secrets must stay server-side.

## 3. TrendRadar

TrendRadar provides:

- hot news;
- RSS;
- trend tracking;
- public-opinion events;
- recurring intelligence inputs.

It remains an isolated external runtime. Do not copy its source or internals
into this repository.

Hermes integrates TrendRadar through an adapter boundary:

- source discovery under `vendor/runtimes/trendradar`;
- GPLv3 license and commercial-boundary reporting;
- CLI command planning for the upstream `trendradar` module;
- MCP server command planning for the upstream `mcp_server.server` module;
- future MCP-backed live intelligence calls through `TRENDRADAR_MCP_URL`.

Current Hermes CLI surface:

```bash
python -m src.hermes intel status
python -m src.hermes intel doctor-command
python -m src.hermes intel schedule-command
python -m src.hermes intel mcp-command --transport http --host 127.0.0.1 --port 3333
```

`TRENDRADAR_MCP_URL` enables future live MCP-backed intelligence calls. Without
it, Hermes reports `source_ready` and still exposes the real upstream commands
needed to start or diagnose TrendRadar.

## 4. SearXNG

SearXNG is optional.

Use it when:

- plain web search is needed;
- hosted search provider keys should be avoided;
- self-hosted metasearch is acceptable.

Do not use SearXNG as a trend engine. It supplements TrendRadar.

Hermes integrates SearXNG as an external Docker/Linux service, not as a Windows
worktree checkout. The SearXNG JSON API contract is:

- `GET /search?q=<query>&format=json`
- `POST /search` with `q=<query>&format=json`
- SearXNG `settings.yml` must enable the `json` output format

Current Hermes CLI surface:

```bash
python -m src.hermes search status
python -m src.hermes search docker-command
python -m src.hermes search query --query "bairui agent"
```

`SEARXNG_BASE_URL` enables live metasearch calls. Without it, Hermes reports
`missing_config` and still exposes the Docker command and API contract needed
to deploy SearXNG correctly.

## 5. Sonic

Sonic is optional and does not replace SearXNG.

Use Sonic when:

- Hermes needs to search Bairui-owned text such as notes, report titles, logs,
  job IDs, task records, and lightweight document indexes;
- we want a small local search backend without putting this data into a public
  metasearch engine;
- we need fast exact or fuzzy lookup before heavier memory retrieval.

Do not use Sonic for public web search. SearXNG searches the outside web;
Sonic searches our own indexed objects.

Hermes integrates Sonic as an external TCP service using the upstream channel
protocol:

- `START search|ingest|control <password>`
- `PING`
- `PUSH <collection> <bucket> <object> "<text>"`
- `QUERY <collection> <bucket> "<terms>" LIMIT(<n>)`

Current Hermes CLI surface:

```bash
python -m src.hermes index status
python -m src.hermes index docker-command
python -m src.hermes index ping
python -m src.hermes index push --collection bairui --bucket docs --object-id doc-1 --text "Hermes runtime readiness"
python -m src.hermes index query --collection bairui --bucket docs --query "readiness"
```

`SONIC_HOST` and `SONIC_PASSWORD` enable live index calls. Without them, Hermes
reports `missing_config` and still exposes the Docker command and protocol
contract needed to deploy Sonic correctly.

## 6. FunASR Voice ASR

FunASR is the first voice-input runtime.

Use it for:

- meeting recording transcription;
- short voice commands;
- customer service call analysis;
- audio-to-text ingestion before memory extraction or report generation.

Hermes integrates FunASR through its OpenAI-compatible ASR API:

- `GET /health`
- `POST /v1/audio/transcriptions`
- multipart field `file`
- multipart field `model`

Current Hermes CLI surface:

```bash
python -m src.hermes voice asr status
python -m src.hermes voice asr server-command --device cuda
python -m src.hermes voice asr transcribe --audio-path ./sample.wav
```

`FUNASR_BASE_URL` enables live transcription calls. Without it, Hermes reports
`missing_config` and still exposes the upstream server command and API contract
needed to deploy FunASR correctly.

## 7. MinerU Document Parsing

MinerU is the first heavy document parsing runtime.

Use it when:

- PDF, image, DOCX, PPTX, or spreadsheet files need to become Markdown/JSON;
- tables, formulas, layout, and embedded images matter;
- parsed output should feed Sonic local index, EverOS memory, PostgreSQL source
  records, and Obsidian reports.

Hermes integrates MinerU as a local CLI/service boundary:

- `mineru -p <input_path> -o <output_path>`
- output Markdown/JSON is written under `MINERU_OUTPUT_DIR`
- customer documents stay inside the controlled runtime directory

Current Hermes CLI surface:

```bash
python -m src.hermes document parse status
python -m src.hermes document parse install-command
python -m src.hermes document parse parse-command --input-path ./sample.pdf
python -m src.hermes document parse ingest-plan --input-path ./sample.pdf --title "Sample"
python -m src.hermes document parse run-ingest --ingest-id <ingest_id>
python -m src.hermes document parse register-artifacts --ingest-id <ingest_id>
python -m src.hermes document parse index-artifacts --ingest-id <ingest_id>
python -m src.hermes document parse memory-candidates --ingest-id <ingest_id>
python -m src.hermes document parse review-memory-candidate --candidate-id <candidate_id> --decision approve
python -m src.hermes document parse source-refs --ingest-id <ingest_id>
python -m src.hermes document parse ingest-report --ingest-id <ingest_id>
python -m src.hermes document-ingests
python -m src.hermes document-ingest-runs
python -m src.hermes document-ingest-reports
python -m src.hermes document-artifacts
python -m src.hermes document-index-runs
python -m src.hermes document-memory-candidates
python -m src.hermes document-memory-reviews
python -m src.hermes source-refs
```

`ingest-plan` creates a local `document_ingests.jsonl` record with the input
file, output directory, MinerU command, and downstream pipeline states:

- parse: planned;
- artifact registration: pending;
- Sonic index: pending;
- EverOS memory candidate: pending;
- PostgreSQL source reference: pending;
- Obsidian report: pending.

`run-ingest` executes the stored MinerU command through a supervised worker and
writes `document_ingest_runs.jsonl` with command, cwd, exit code, stdout,
stderr, error, and timestamps. Missing executables, non-zero exits, and
timeouts are recorded as failed/timeout runs instead of being hidden.

`register-artifacts` scans the ingest output directory and writes
`document_artifacts.jsonl` records for real files produced by MinerU. Each
artifact record stores the ingest id, absolute path, relative path, artifact
type, MIME type, size, sha256 hash, and timestamp. Markdown, JSON, images,
tables, HTML, and text files are classified for downstream processing.

`index-artifacts` reads registered Markdown, text, JSON, and HTML artifacts and
pushes their text content into Sonic using the existing `index push` adapter
contract. Image/table/formula artifacts are skipped until a dedicated extractor
exists. Each run writes `document_index_runs.jsonl` with provider, collection,
bucket, indexed/skipped/failed counts, per-artifact status, and any error. If
`SONIC_HOST` or `SONIC_PASSWORD` is missing, the run is recorded as failed
instead of reporting fake indexing success.

Hermes still does not claim full knowledge ingestion is complete after Sonic
indexing.

`memory-candidates` reads registered text-like artifacts and creates
`document_memory_candidates.jsonl` records with `pending_review` status. These
records are memory candidates only: they are not pushed into EverOS and not
treated as owner-approved long-term memory.

`review-memory-candidate` is the governed handoff. Approvals attempt EverOS
`/add`, rejections do not call EverOS, and both decisions write
`document_memory_reviews.jsonl` plus an Obsidian graph note under
`00-Inbox/everos-candidates/` with frontmatter, tags, and internal links to
`[[Document Memory Candidates]]`, `[[Bairui]]`, `[[Hermes]]`, `[[EverOS]]`, and
the source `[[Document Ingest <short-id>]]`.

`source-refs` creates structured provenance records for the same pipeline. It
writes `source_refs.jsonl` locally and matches the PostgreSQL `source_refs`
table contract used by production migrations. The records connect MinerU
artifacts, Sonic index runs, Hermes memory candidates, review status, EverOS
promotion status, and related Obsidian note paths.

`ingest-report` writes a graph-friendly Obsidian report under
`05_Reports/document-ingests/` and records the output in
`document_ingest_reports.jsonl`. The report has YAML frontmatter, tags, a
`Document Ingest Reports.md` MOC, and internal links to
`[[Document Ingest Reports]]`, `[[Document Memory Candidates]]`, `[[Bairui]]`,
`[[Hermes]]`, `[[MinerU]]`, `[[Sonic]]`, `[[EverOS]]`, and `[[Obsidian]]`.
It summarizes artifacts, Sonic index runs, memory candidates, review status,
source references, and next actions for the ingest.

The next pipeline phase is surfacing this workflow in the product UI/API as a
document knowledge ingestion workbench.

## 8. Unified Runtime Readiness

Hermes now exposes a machine-readable readiness summary for vendor runtimes:

```bash
python -m src.hermes runtime-readiness
curl http://127.0.0.1:8787/runtime/readiness
```

The readiness contract separates:

- blockers: required runtime pieces that prevent a usable deployment;
- warnings: optional runtimes that are not yet configured;
- source_ready: upstream source is present but the live service endpoint is not
  configured yet;
- configured: adapter has enough configuration to attempt live calls.

This is the bridge from adapter visibility to one-click orchestration. Platform
and deployment scripts should consume this endpoint instead of guessing from
free-form logs.

## 9. Research Flow

```text
owner question
  -> Hermes route planner
  -> TrendRadar or SearXNG
  -> crawl/extract if needed
  -> source_refs in PostgreSQL
  -> model synthesis
  -> Obsidian report
  -> short owner summary
```

## 10. Source Rules

Research outputs must:

- store source references;
- distinguish evidence from inference;
- include retrieval time;
- avoid unsupported claims;
- write durable conclusions to Obsidian only after quality checks.
