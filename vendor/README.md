# Vendor Runtime Sources

This directory contains external runtime source integrations used by MOXI Hermes.

These projects are integrated as Git submodules or external runtime references.
They are not the Hermes product core. Hermes must call them through adapters,
process boundaries, APIs, MCP tools, or worker contracts.

## Integrated Submodules

| Runtime | Path | Purpose | License Boundary |
| --- | --- | --- | --- |
| EverOS | `vendor/runtimes/everos` | Automatic memory extraction and retrieval | Apache-2.0 |
| TrendRadar | `vendor/runtimes/trendradar` | Trend, RSS, hot-list, and public-opinion intelligence | GPLv3 |
| MiroFish | `vendor/runtimes/mirofish` | Scenario simulation and multi-agent rehearsal | AGPLv3 |

## External Runtime Reference

| Runtime | Source | Purpose | Note |
| --- | --- | --- | --- |
| SearXNG | `https://github.com/searxng/searxng` | Optional metasearch | AGPLv3; Windows checkout has incompatible file names, so use Docker or Linux checkout. |

## Commercial Rule

External runtime source may speed up delivery, but it must not erase ownership
boundaries:

- Hermes core source belongs under `src/`.
- External code remains under `vendor/runtimes/`.
- Adapter code belongs under `src/`.
- License files and attribution must remain intact.
- GPLv3 and AGPLv3 modules require special commercial compliance review before
  distribution or hosted use.

## Integration Order

1. EverOS adapter for memory candidates.
2. TrendRadar adapter for intelligence input.
3. MiroFish adapter for simulation briefs and reports.
4. SearXNG as an optional Docker-based runtime after Linux/server deployment.
