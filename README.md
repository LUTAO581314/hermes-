# MOXI Industrial Agent OS

This repository is the source-owned engineering framework for MOXI Industrial
Agent OS.

The previous prototype source has been removed. The repository now keeps the
commercial product plan, deployment environment baseline, and clean source
skeleton from which Hermes will be rebuilt.

## Current Repository State

This repository intentionally contains:

- current product and architecture documents under `docs/`;
- historical phase summaries under `reports/`;
- environment templates and deployment skeleton files;
- `src/` as the rebuilt Hermes runtime source location;
- `tests/` as the rebuilt test suite location.

This repository intentionally does not contain:

- old runtime implementation files;
- old tests tied to removed implementation details;
- external project patches;
- copied frontend prototypes;
- runtime data, logs, secrets, sessions, QR state, or generated media.

## Product Direction

MOXI Industrial Agent OS provides one controlled backend, one primary user
experience, governed long-term memory, company workflow automation, trend and
research intelligence, simulation, and owner-approved execution.

The system is built around these permanent boundaries:

- Hermes is the planned single backend authority.
- MOXI / Brain UI is the primary frontend surface.
- PostgreSQL is the production system database.
- Obsidian is the owner-readable long-term memory and decision record.
- EverOS is the automatic memory extraction and retrieval engine.
- TrendRadar is the first external trend and public-opinion runtime.
- SearXNG is an optional self-hosted metasearch supplement.
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

The old explanatory documents have been removed. Phase summaries remain under
`reports/`. The current product plan is now organized by functional domain:

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
- Every phase must include verification and a Chinese owner-facing report in
  `reports/`.
- New runtime code must be rebuilt under `src/`.
- New tests must be rebuilt under `tests/`.
- External runtime source lives under `vendor/runtimes/` and must keep its
  license and adapter boundary.
