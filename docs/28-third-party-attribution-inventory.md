# Third-Party Attribution Inventory

This inventory is an internal engineering and delivery checklist for bairui
commercial trials. It is not legal advice. Complete legal review before paid
distribution, hosted service resale, or customer-specific contract commitments.

Customer-facing product surfaces must still expose only the `bairui` brand.
Names below are source attribution and license-review records, not public UI
labels.

## Inventory Table

| Component | Product Role | Integration Boundary | License | Default Trial Use | Required Action |
| --- | --- | --- | --- | --- | --- |
| psycopg binary package | PostgreSQL driver | Python dependency in `requirements.txt` | LGPL with binary packaging terms | allowed | Preserve package license notices and pin version. |
| EverOS | Long-term memory adapter | Optional source/service under `vendor/runtimes/everos` | Apache-2.0 | allowed after source/license present | Preserve LICENSE/NOTICE and keep owner review before memory promotion. |
| FunASR | Voice ASR runtime | Optional external HTTP/OpenAI-compatible service | MIT | allowed when self-hosted and configured | Preserve notices; do not upload customer audio to unknown public endpoints. |
| MinerU | Document parsing runtime | Optional CLI/service parser | MinerU Open Source License | review required | Review project-specific terms before paid document parsing delivery. |
| TrendRadar | Intelligence/trend runtime | Optional isolated source/MCP runtime | GPLv3 | review required | Source-delivery and modification obligations must be reviewed before distribution. |
| MiroFish | Simulation runtime | Optional isolated source/API runtime | AGPLv3 | review required | Hosted-service source obligations must be reviewed before customer use. |
| SearXNG | Metasearch service | Optional external Docker/Linux service | AGPLv3 | review required | Hosted-use and settings/source delivery obligations must be reviewed. |
| Sonic | Local internal index | Optional external TCP/Docker service | MPL-2.0 | allowed with notices | Preserve notices and modified-file obligations if changed. |
| pixi-live2d-display-advanced | Browser Avatar renderer | Optional frontend/browser runtime contract | MIT | allowed with notices | Preserve notices and require customer authorization for avatar assets. |
| BaiLongma UI source reference | Frontend interaction substrate | Internal design/source reference only | MIT | allowed as source substrate | Remove public upstream identity; preserve MIT attribution internally. |

## Trial Defaults

Allowed by default for a controlled commercial trial:

- bairui-owned runtime code in this repository;
- PostgreSQL through `psycopg`;
- Sonic as an internal service when self-hosted;
- FunASR when self-hosted with customer-approved audio handling;
- pixi-live2d-display-advanced for browser Avatar rendering;
- BaiLongma-derived interaction patterns after all public copy is rewritten to
  `bairui`;
- EverOS only when the source/license files are present and memory promotion is
  still owner-reviewed.

Review required before enabling for a paying customer:

- MinerU document parsing if customer files are processed;
- GPLv3/AGPLv3 runtimes such as TrendRadar, MiroFish, and SearXNG;
- any cloud API that may receive customer data;
- voice cloning, customer voice assets, or avatar assets without explicit
  authorization;
- any modified third-party source shipped to the customer.

## Customer Data Boundary

Do not send customer data to third-party public services by default.

- Audio files require customer approval and a self-hosted ASR target for trial
  delivery.
- Documents require customer approval and a configured parser runtime.
- Web search/metasearch should be treated as external network access and shown
  as disabled or approval-required until configured.
- Avatar assets require customer ownership or written authorization.
- Long-term memory writes require owner review and must not be automatic.

## Internal Attribution Boundary

Internal documents, dependency manifests, vendor folders, and license notices may
include upstream names and repository URLs. Customer UI, activation flow, setup
copy, screenshots, route labels, public product contract, and reports must not.

Run:

```powershell
.\scripts\check-public-brand.ps1
```

before every commercial trial handoff.

## Go/No-Go Rule

Go only when:

- this inventory matches the runtimes actually enabled in the trial;
- every enabled third-party component has a known license;
- required notices are preserved;
- review-required components are either disabled or explicitly approved;
- the diagnostic bundle does not include secrets, raw customer documents,
  customer audio, database dumps, or private runtime tokens.

No-go when any enabled component has unknown license status, unclear hosted-use
obligations, missing notices, or unapproved customer data transfer.
