# Memory: Obsidian And EverOS

## 1. Memory Decision

Use a two-layer memory system:

- Obsidian is the owner-readable long-term memory source of truth.
- EverOS is the automatic memory extraction and retrieval engine.

PostgreSQL stores memory metadata and review state, not the final human memory
truth.

## 2. Obsidian Role

Obsidian stores:

- owner preferences;
- durable instructions;
- project facts;
- company operating reports;
- decisions;
- source-backed research;
- MiroFish simulation reports;
- postmortems;
- curated memory notes.

Obsidian must stay readable, portable, and editable by the owner.

## 3. EverOS Role

EverOS stores and indexes:

- episodes;
- atomic facts;
- user memory;
- agent memory;
- skill memory;
- semantic search artifacts;
- hybrid recall metadata.

EverOS can accelerate recall and personalization, but its outputs are candidates
until reviewed.

Hermes integrates EverOS through a runtime adapter, not by rewriting its memory
engine. The adapter speaks the upstream EverOS HTTP contract:

- `POST /api/v1/memory/add`
- `POST /api/v1/memory/flush`
- `POST /api/v1/memory/search`
- `POST /api/v1/memory/get`

Current Hermes CLI surface:

```bash
python -m src.hermes memory status
python -m src.hermes memory ingest --text "Owner prefers concise reports" --user-id owner --session-id owner-setup
python -m src.hermes memory flush --session-id owner-setup
python -m src.hermes memory search --query "report preference" --user-id owner
python -m src.hermes document parse memory-candidates --ingest-id <ingest_id>
python -m src.hermes document-memory-candidates
```

`EVEROS_BASE_URL` enables live calls. Without it, Hermes reports
`missing_config` for live memory operations while still detecting the local
Apache-2.0 EverOS source under `vendor/runtimes/everos`.

Document-derived memory currently stops at a governed candidate stage.
`document parse memory-candidates` reads registered document text artifacts and
writes `document_memory_candidates.jsonl` records with `pending_review` status.
This stage does not call EverOS `/add`, does not write Obsidian notes, and does
not promote anything to durable memory. Promotion remains a separate owner or
platform review action.

## 4. Memory Flow

```text
raw event
  -> Hermes redaction and summarization
  -> EverOS add / flush
  -> Hermes search and candidate extraction
  -> PostgreSQL memory_candidates
  -> Obsidian inbox note
  -> owner review
  -> promoted Obsidian memory
```

## 5. Obsidian Layout

```text
obsidian-vault/
  00-Inbox/
    needs-review/
    everos-candidates/
  10-Owner/
  20-Agents/
  30-Projects/
  35-Company/
  40-Research/
  50-Markets/
  60-Decisions/
  70-Reports/
    daily/
    weekly/
    simulations/
  80-Runbooks/
  90-Logs/
```

## 6. Promotion Rules

Promote to Obsidian only when the content is:

- stable;
- useful;
- source-backed or owner-confirmed;
- non-duplicative;
- safe to retain;
- connected to a project, person, decision, report, or preference.

Do not promote:

- raw chat noise;
- secrets;
- QR/session state;
- platform tokens;
- unverified speculation;
- temporary model outputs;
- sensitive personal data without a clear reason.

## 7. PostgreSQL Tables

Memory-related PostgreSQL tables:

- `memory_candidates`
- `source_refs`
- `audit_logs`
- `simulation_runs`
- `report_metadata`

These tables track review and provenance. They do not replace the Obsidian note.
