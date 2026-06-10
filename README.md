# MOXI Industrial Agent OS

This repository is the source-owned engineering framework for MOXI Industrial
Agent OS.

The previous prototype source and historical phase reports have been removed.
The repository now restarts from a clean, mature-source-first Hermes
productization baseline.

## Current Repository State

This repository intentionally contains:

- current product and architecture documents under `docs/`;
- environment templates and deployment skeleton files;
- `src/` as the rebuilt Hermes runtime source location;
- `tests/` as the rebuilt test suite location.

This repository intentionally does not contain:

- old runtime implementation files;
- old tests tied to removed implementation details;
- external project patches;
- copied frontend prototypes;
- historical phase report noise;
- runtime data, logs, secrets, sessions, QR state, or generated media.

## Product Direction

MOXI Industrial Agent OS provides one controlled backend, one primary user
experience, governed long-term memory, company workflow automation, trend and
research intelligence, simulation, and owner-approved execution.

## Productization Decision

The commercialization requirement is a quality bar, not a command to build
everything from a blank file. The runtime should prioritize mature, working
source code as product substrate whenever the license and architecture fit.

For Hermes, "source-owned" means we control the source tree, deployment,
configuration, brand fields, adapters, tests, and operational contract. It does
not mean every agent, memory, search, or workflow component must be invented
from scratch.

The preferred path is:

- use mature open-source runtime code directly when it is useful;
- keep original licenses, notices, source names, and attribution;
- put third-party runtime code under `vendor/runtimes/` or another explicit
  boundary;
- build bairui product behavior, configuration, deployment, license,
  readiness, and platform contracts around those runtimes;
- avoid AI-only blank-slate rewrites for complex agent internals unless a
  small owned component is clearly safer than integrating an existing one.

The target is still industrial product quality: repeatable deployment,
observable operation, tests, clear boundaries, and future commercial-grade
handoff. Public/open-source use is acceptable when a selected upstream license
requires it.

The system is built around these permanent boundaries:

- Hermes is the planned single backend authority.
- MOXI / Brain UI is the primary frontend surface.
- PostgreSQL is the production system database.
- Obsidian is the owner-readable long-term memory and decision record.
- EverOS is the automatic memory extraction and retrieval engine.
- FunASR is the optional voice ASR runtime for transcription, voice commands,
  meeting notes, and call analysis.
- MinerU is the optional document parsing runtime for PDF, image, and Office
  ingestion into Markdown/JSON.
- TrendRadar is the first external trend and public-opinion runtime.
- SearXNG is an optional self-hosted metasearch supplement.
- Sonic is the optional local internal search index for our own documents,
  notes, logs, and task records.
- MiroFish is the scenario simulation and decision rehearsal lab.
- Feishu is the company operation surface.
- WeChat and QQ are personal or social channels with strict risk boundaries.

Production will support only two deployment modes:

- Local production environment: a local workstation, mini server, NAS, or LAN
  machine. It is a real production deployment for the owner, but it does not
  require a public domain or DNS record.
- Domain server production environment: a server with a domain name, DNS
  resolution, HTTPS, and Nginx routing. This mode is required when the product
  must receive stable Feishu, WeChat, QQ, or public web callbacks.

## Documentation Map

The old explanatory documents and phase summaries have been removed. The
current product plan is organized by functional domain:

- [Product Blueprint](docs/00-product-blueprint.md)
- [System Architecture](docs/01-system-architecture.md)
- [Server Rebuild And Deployment](docs/02-server-rebuild-and-deployment.md)
- [PostgreSQL Data Architecture](docs/03-postgresql-data-architecture.md)
- [Hermes Backend Runtime](docs/04-hermes-backend-runtime.md)
- [Memory: Obsidian And EverOS](docs/05-memory-obsidian-everos.md)
- [Intelligence: Models, Search, And Crawling](docs/06-intelligence-model-search.md)
- [Simulation: MiroFish](docs/07-simulation-mirofish.md)
- [Connectors And Channels](docs/08-connectors-and-channels.md)
- [Frontend: MOXI / Brain UI](docs/09-frontend-moxi-brain-ui.md)
- [Security, Compliance, And Operations](docs/10-security-compliance-ops.md)
- [Commercial Productization Roadmap](docs/11-commercial-roadmap.md)
- [One-Click Deployment To Usable Stage](docs/12-one-click-deployment.md)
- [Source Rebuild Technical Path](docs/13-source-rebuild-technical-path.md)
- [Commercial Interaction Model](docs/14-commercial-interaction-model.md)
- [GitHub Repository Cleanup Policy](docs/15-github-repository-cleanup.md)
- [Commercial Delivery Development Plan](docs/16-commercial-delivery-development-plan.md)
- [Three-Pillar Commercial Project Plan](docs/17-three-pillar-commercial-project-plan.md)
- [Vendor Runtime Integration](docs/18-vendor-runtime-integration.md)
- [Brand And Trademark Fields](docs/19-brand-and-trademark-fields.md)

## P0 Hermes Deployment

CLI entrypoint:

```bash
python -m src.hermes --help
python -m src.hermes status
python -m src.hermes capabilities
python -m src.hermes memory status
python -m src.hermes memory search --query "owner preferences"
python -m src.hermes voice asr status
python -m src.hermes voice asr server-command
python -m src.hermes document parse status
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
python -m src.hermes intel status
python -m src.hermes intel mcp-command
python -m src.hermes simulation status
python -m src.hermes simulation dev-command
python -m src.hermes search status
python -m src.hermes search docker-command
python -m src.hermes index status
python -m src.hermes index docker-command
python -m src.hermes runtime-readiness
python -m src.hermes serve
```

Local usable deployment remains:

```bash
bash scripts/deploy-usable.sh
```

Commercial Linux service assets live under `infra/hermes`:

```bash
sh infra/hermes/scripts/deploy-hermes.sh
```

Copy `infra/hermes/env.example` to a protected server path such as
`/etc/bairui/hermes.env` and set real values before production service install.

## Engineering Rule

The repository must converge toward production ownership:

- New durable behavior belongs in our source tree first.
- External projects are isolated behind adapter contracts.
- Platform credentials, sessions, QR state, generated media, and raw private logs
  must stay outside Git.
- New runtime code must be rebuilt under `src/`.
- New tests must be rebuilt under `tests/`.
- External runtime source lives under `vendor/runtimes/` and must keep its
  license and adapter boundary.
