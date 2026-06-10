# bairui

This repository is the source-owned engineering framework for the bairui
industrial agent product.

Customer-facing product surfaces must expose only the `bairui` brand. Historical
project names, upstream runtime names, and third-party repository names are
internal engineering details and must not appear in the customer frontend,
activation flow, setup copy, or public product contract.

## Current Repository State

This repository contains:

- current product and architecture documents under `docs/`;
- environment templates and deployment skeleton files;
- `src/` as the rebuilt runtime source location;
- `tests/` as the rebuilt test suite location.

This repository intentionally does not contain:

- old runtime implementation files;
- old tests tied to removed implementation details;
- external project patches;
- copied frontend prototypes;
- historical phase report noise;
- runtime data, logs, secrets, sessions, QR state, or generated media.

## Product Direction

bairui provides one controlled backend, one primary user experience, governed
long-term memory, company workflow automation, document intelligence, voice
input, search, reports, and owner-approved execution.

The commercialization requirement is a quality bar, not a command to build
everything from a blank file. The product should prioritize mature, working
source code as substrate whenever the license and architecture fit.

The preferred path is:

- use mature open-source runtime code directly when it is useful;
- keep original licenses, notices, source names, and attribution in internal
  engineering boundaries;
- put third-party runtime code under `vendor/runtimes/` or another explicit
  boundary;
- build bairui product behavior, configuration, deployment, license,
  readiness, and frontend contracts around those runtimes;
- avoid AI-only blank-slate rewrites for complex agent internals unless a
  small owned component is clearly safer than integrating an existing one.

The frontend should use the owner-approved open-source UI base only for
interaction patterns, component density, layout rhythm, and visual inspiration.
All public copy, product name, logo text, route labels, activation steps, empty
states, and reports must be changed to `bairui`.

Internal frontend source reference:

- Repository: `https://github.com/xiaoyuanda666-ship-it/BaiLongma`
- License: MIT
- Scope: frontend interaction model, component behavior, activation experience,
  voice panel patterns, media panels, realtime UI events, and workbench layout.
- Boundary: do not expose the upstream project name, package name, logo, or
  route labels to customers; backend integration is supplemental only.

## Documentation Map

- [Product Blueprint](docs/00-product-blueprint.md)
- [System Architecture](docs/01-system-architecture.md)
- [Server Rebuild And Deployment](docs/02-server-rebuild-and-deployment.md)
- [PostgreSQL Data Architecture](docs/03-postgresql-data-architecture.md)
- [Backend Runtime](docs/04-hermes-backend-runtime.md)
- [Memory And Notes](docs/05-memory-obsidian-everos.md)
- [Intelligence: Models, Search, And Crawling](docs/06-intelligence-model-search.md)
- [Simulation](docs/07-simulation-mirofish.md)
- [Connectors And Channels](docs/08-connectors-and-channels.md)
- [Frontend: bairui UI](docs/09-frontend-moxi-brain-ui.md)
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
- [bairui Frontend Source UI Integration](docs/20-bairui-frontend-source-ui-integration.md)

## CLI Entry Point

```bash
python -m src.hermes --help
python -m src.hermes status
python -m src.hermes capabilities
python -m src.hermes frontend-contract
python -m src.hermes events
python -m src.hermes channels status
python -m src.hermes channels targets
python -m src.hermes channels plan-send --target-id owner_review --text "Review this update"
python -m src.hermes memory status
python -m src.hermes memory search --query "owner preferences"
python -m src.hermes voice asr status
python -m src.hermes document parse status
python -m src.hermes document parse ingest-plan --input-path ./sample.pdf --title "Sample"
python -m src.hermes document parse session-list --limit 50
python -m src.hermes document parse session-summary --ingest-id <ingest_id>
python -m src.hermes document parse workbench-next --ingest-id <ingest_id>
python -m src.hermes document parse workbench-run-until-blocked --ingest-id <ingest_id>
python -m src.hermes runtime-readiness
python -m src.hermes serve
```

## Frontend Contract

- `GET /frontend/contract`
- `python -m src.hermes frontend-contract`

The contract lists stable bairui product surfaces, including activation,
dashboard, command, documents, memory review, reports, and runtime settings.
It also includes the complete activation steps, renderable action forms, status
values, and premium sci-fi UI design tokens.

## Deployment

Local usable deployment remains:

```bash
bash scripts/deploy-usable.sh
```

Commercial Linux service assets live under `infra/hermes`:

```bash
sh infra/hermes/scripts/deploy-hermes.sh
```

Copy `infra/hermes/env.example` to a protected server path and set real values
before production service install.
