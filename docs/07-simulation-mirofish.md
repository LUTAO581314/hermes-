# Simulation: MiroFish

## 1. Simulation Decision

MiroFish is the scenario simulation and report lab.

It is not the backend brain, not the memory source of truth, and not an action
executor. It is an external runtime used by Hermes for structured simulation.

## 2. Use Cases

Use MiroFish for:

- product strategy comparison;
- project go/no-go decisions;
- market bull/bear scenarios;
- risk and opportunity rehearsal;
- multi-agent debate;
- execution plan stress tests;
- commercial positioning review.

## 3. Simulation Flow

```text
Obsidian context
  -> Hermes simulation brief
  -> MiroFish multi-agent run
  -> simulation report
  -> PostgreSQL simulation_runs metadata
  -> Obsidian 70-Reports/simulations
  -> decision note in 60-Decisions when owner approves
```

## 3.1 Hermes Adapter Contract

Hermes integrates MiroFish through an adapter boundary:

- source discovery under `vendor/runtimes/mirofish`;
- AGPLv3 license and hosted-service boundary reporting;
- npm command planning for the upstream root scripts;
- Flask API contract discovery for `/health`, graph, simulation, and report
  routes;
- future live calls through `MIROFISH_BACKEND_BASE_URL`.

Current Hermes CLI surface:

```bash
python -m src.hermes simulation status
python -m src.hermes simulation setup-command
python -m src.hermes simulation backend-command
python -m src.hermes simulation frontend-command
python -m src.hermes simulation dev-command
```

`MIROFISH_BACKEND_BASE_URL` enables future live simulation API calls. Without
it, Hermes reports `source_ready` and still exposes the real upstream commands
needed to install, start, or diagnose MiroFish.

## 4. Simulation Brief

A simulation brief must include:

- question;
- decision owner;
- background;
- known facts;
- unknowns;
- constraints;
- options;
- risk categories;
- evidence links;
- required output format.

## 5. Output Requirements

MiroFish output must include:

- executive summary;
- competing viewpoints;
- assumptions;
- risk matrix;
- opportunity matrix;
- recommended option;
- confidence;
- what would change the recommendation;
- owner decision checkpoint.

No simulation output may directly trigger a high-risk action.
