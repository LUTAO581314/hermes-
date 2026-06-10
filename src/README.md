# bairui Runtime Source

This directory contains the bairui runtime source.

The runtime is mature-source-first: use existing source code where it reduces
product risk, preserve upstream attribution and licenses inside engineering
boundaries, and add bairui product behavior through clear adapters, deployment
scripts, readiness checks, CLI commands, tests, and platform contracts.

The frontend may use the owner-approved open-source UI project known as
Xiaobailong/Bailongma as a source base for interaction patterns and component
behavior. That project name is an internal engineering reference only; customer
surfaces must show only the `bairui` brand.

Current CLI entrypoint:

```bash
python -m src.hermes --help
python -m src.hermes status
python -m src.hermes serve
```
