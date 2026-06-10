# Product Blueprint

## 1. Product Definition

MOXI Industrial Agent OS is a commercial agent operating system for personal
command, company operations, research intelligence, governed memory, simulation,
and controlled execution.

It is not a wrapper around one chatbot. It is also not a pile of loosely glued
open-source projects. The long-term product must be source-owned, auditable,
deployable, and replaceable at every external boundary.

The system should support:

- owner command and review;
- company task, customer, sales, report, approval, and risk workflows;
- personal companion and reminder channels;
- durable memory and decision records;
- source-backed search, trend, and public-opinion analysis;
- image, document, voice, and later video intelligence through reviewed APIs;
- multi-agent decision simulation;
- explicit owner confirmation before sensitive or irreversible actions;
- commercial operations, deployment, monitoring, billing readiness, and support.

## 2. Product Principles

### Mature Source First

Commercialization is a product-quality target. It does not require a
blank-slate AI rewrite of every subsystem.

Hermes should prefer mature, working source code as the product substrate for
complex agent capabilities when the license, architecture, and operational
boundary are acceptable. This is especially important for memory, agent
runtime, workflow, search, connectors, and simulation, where hidden edge cases
are expensive.

Our product work is to own the source tree and product contract:

- brand and customer-facing fields default to `bairui`;
- deployment, readiness, logging, license, and verification are ours;
- adapters define the boundary between Hermes and external runtimes;
- upstream names, licenses, notices, and attribution remain intact;
- GPL/AGPL components can be used when we accept the related public-source
  obligations for that component or keep them isolated as services.

Do not treat "source-owned" as "invent everything from zero." Treat it as:
we can read, build, modify, deploy, test, replace, and explain the source we
ship.

### Source Ownership

Core behavior belongs to our codebase. External projects can accelerate the
system, but they must not own the product brain, memory authority, permission
model, or customer-facing backend contract.

Examples:

- Hermes owns backend orchestration.
- MOXI / Brain UI owns the user experience.
- PostgreSQL owns structured production state.
- Obsidian owns readable long-term memory.
- EverOS owns automatic memory extraction and retrieval as an engine, not as the
  final human truth.
- TrendRadar, SearXNG, Firecrawl, and MiroFish are external runtimes behind
  adapters.

### Industrialization

The product must move beyond demos:

- deterministic deployment;
- database migrations;
- typed domain contracts;
- audit logs;
- health checks;
- backups;
- permission planes;
- incident runbooks;
- CI verification;
- release notes;
- customer-safe configuration;
- clear license and attribution boundaries.

### Human Authority

The owner remains the final authority for:

- money movement;
- HR and compensation;
- legal commitments;
- external promises;
- account settings;
- irreversible deletion;
- production deployment changes;
- persistent memory promotion.

## 3. Product Planes

| Plane | Purpose | Primary System |
| --- | --- | --- |
| Command Plane | Owner interaction and approvals | MOXI / Brain UI, Feishu, CLI |
| Backend Plane | Routing, jobs, tools, policy, memory flow | Hermes |
| Data Plane | Structured state and audit | PostgreSQL |
| Memory Plane | Human-readable long-term truth | Obsidian |
| Automatic Memory Plane | Extraction, retrieval, agent/user memory | EverOS |
| Intelligence Plane | Search, trend, crawl, model reasoning | TrendRadar, SearXNG, model gateway |
| Simulation Plane | Multi-agent decision rehearsal | MiroFish |
| Connector Plane | Platform-specific message ingress/egress | Feishu, WeChat, QQ adapters |
| Operations Plane | Deploy, monitor, backup, security | Linux, systemd, Docker, Nginx |

## 4. Commercial Target

The commercial target is an agent OS that can be packaged for:

- private owner deployment;
- company operations assistant;
- knowledge and memory assistant;
- research and intelligence dashboard;
- governed multi-agent decision lab;
- future SaaS or managed private-cloud edition.

Commercial readiness requires:

- clean source boundaries;
- repeatable server rebuild;
- PostgreSQL-backed state;
- customer-safe configuration;
- tenant-ready identity model;
- auditability;
- backup and recovery;
- dependency license review;
- stable API contracts;
- deployment and operations manual.
