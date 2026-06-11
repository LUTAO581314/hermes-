# bairui Product Demo Acceptance

This checklist proves that the local/server Agent product can be demonstrated as
a closed loop without fake success states.

Run from the repository root:

```powershell
.\scripts\product-acceptance.ps1
```

Optional JSON report:

```powershell
.\scripts\product-acceptance.ps1 -OutputPath artifacts\product-acceptance.json
```

Configuration diagnostics can be checked separately:

```powershell
.\scripts\config-doctor.ps1
```

The same acceptance can be run through the smoke entry point:

```powershell
.\scripts\smoke-test.ps1 -FullAcceptance
.\scripts\smoke-test.ps1 -FullAcceptance -AcceptanceOutputPath artifacts\product-acceptance.json
```

The script runs `python -m src.hermes demo flow` in an isolated temporary data
directory and verifies these product scenarios:

| Scenario | Proof |
| --- | --- |
| Research task | Command session runs, agent output is promoted to a report, and Reports can show the deliverable. |
| Document knowledge base | A memory candidate is reviewed and long-term memory write remains disabled unless owner-approved. |
| Customer communication draft | Channel draft is planned and reviewed while `will_send=false`. |
| Code understanding | CodeGraph registers, scans, queries, and reports that code structure is separate from long-term memory. |
| Runtime diagnostics | Dashboard, Settings, and Events have audit evidence from the completed demo flow. |
| Safe configuration diagnostics | `python -m src.hermes config-status` reports required paths and secret states without returning secret values. |

Safety gates that must stay true:

- `no_external_send=true`
- `no_auto_memory_write=true`
- channel plan and review both keep `will_send=false`
- memory flow keeps `will_write_long_term_memory=false`
- promotion idempotency is `event_id + target`

Use this script before an internal demo. Use `scripts/smoke-test.ps1` for the
faster CI-style repository health check, and add `-FullAcceptance` when the
demo needs scenario-level proof. Use `scripts/config-doctor.ps1` when you need
the same operator-safe configuration check without opening the browser.
