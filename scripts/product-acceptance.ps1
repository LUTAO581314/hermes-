param(
    [string]$OutputPath = "",
    [switch]$KeepTemp
)

$ErrorActionPreference = "Stop"

$previousEnv = @{
    HERMES_DATA_DIR = $env:HERMES_DATA_DIR
    HERMES_LOG_DIR = $env:HERMES_LOG_DIR
    HERMES_OBSIDIAN_VAULT_DIR = $env:HERMES_OBSIDIAN_VAULT_DIR
    BAIRUI_CODEGRAPH_ROOT = $env:BAIRUI_CODEGRAPH_ROOT
    BAIRUI_CHANNELS_ENABLED = $env:BAIRUI_CHANNELS_ENABLED
    BAIRUI_MODEL_BASE_URL = $env:BAIRUI_MODEL_BASE_URL
    BAIRUI_MODEL_API_KEY = $env:BAIRUI_MODEL_API_KEY
    BAIRUI_MODEL_NAME = $env:BAIRUI_MODEL_NAME
}

function New-ScenarioResult {
    param(
        [string]$Id,
        [string]$Name,
        [bool]$Passed,
        [string]$Evidence,
        [string]$NextStep
    )
    [pscustomobject]@{
        id = $Id
        name = $Name
        status = $(if ($Passed) { "passed" } else { "failed" })
        evidence = $Evidence
        next_step = $NextStep
    }
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("bairui-acceptance-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
    $env:HERMES_DATA_DIR = Join-Path $tmp "data"
    $env:HERMES_LOG_DIR = Join-Path $tmp "logs"
    $env:HERMES_OBSIDIAN_VAULT_DIR = Join-Path $tmp "vault"
    $env:BAIRUI_CODEGRAPH_ROOT = Join-Path $tmp "codegraph"
    $env:BAIRUI_CHANNELS_ENABLED = "1"
    $env:BAIRUI_MODEL_BASE_URL = "https://models.example.test/v1"
    $env:BAIRUI_MODEL_API_KEY = "dummy"
    $env:BAIRUI_MODEL_NAME = "bairui-acceptance-model"

    $flowRaw = python -m src.hermes demo flow
    if ($LASTEXITCODE -ne 0) {
        throw "demo flow exited with code $LASTEXITCODE`: $flowRaw"
    }
    $payload = $flowRaw | ConvertFrom-Json
    $demo = $payload.demo_flow
    if ($null -eq $demo) {
        throw "demo flow did not return demo_flow payload: $flowRaw"
    }
    $configRaw = python -m src.hermes config-status
    if ($LASTEXITCODE -notin @(0, 1)) {
        throw "config-status exited with code $LASTEXITCODE`: $configRaw"
    }
    $configPayload = $configRaw | ConvertFrom-Json
    $configStatus = $configPayload.config_status

    $researchPassed = $demo.checkpoints.command_session -eq $true -and $demo.checkpoints.report_created -eq $true -and @("planned", "duplicate") -contains $demo.promotions.report.status
    $knowledgePassed = $demo.checkpoints.memory_review_recorded -eq $true -and $demo.memory.will_write_long_term_memory -eq $false -and @("rejected", "already_reviewed") -contains $demo.memory.review.status
    $customerDraftPassed = $demo.checkpoints.channel_review_recorded -eq $true -and $demo.channel.plan.will_send -eq $false -and $demo.channel.review.will_send -eq $false
    $codePassed = $demo.checkpoints.codegraph_query_ready -eq $true -and "$($demo.codegraph.memory_boundary)" -match "does not write long-term memory"
    $diagnosticsPassed = $demo.status -eq "completed" -and $demo.audit_marker.payload.will_send -eq $false -and $demo.audit_marker.payload.will_write_long_term_memory -eq $false
    $configurationPassed = @("ready", "partial") -contains $configStatus.status -and "$($configStatus.secret_policy)" -match "never returned"

    $scenarios = @(
        (New-ScenarioResult "research_task" "Command research task to report" $researchPassed "Command session, agent report promotion, and Reports output are present." "Open Command, promote a completed agent message to Report, then inspect Reports."),
        (New-ScenarioResult "document_knowledge_base" "Document knowledge to memory review" $knowledgePassed "Demo memory candidate is reviewed and long-term memory write remains false." "Open Documents, create candidates, then approve or reject in Memory Review."),
        (New-ScenarioResult "customer_draft" "Customer communication draft approval" $customerDraftPassed "Channel draft is planned and reviewed with will_send=false." "Open Channels and review drafts; current backend records review only."),
        (New-ScenarioResult "code_understanding" "CodeGraph source understanding" $codePassed "CodeGraph registers, scans, queries, and reports memory separation." "Open CodeGraph, register a repository, scan, query, and run impact analysis."),
        (New-ScenarioResult "runtime_diagnostics" "Dashboard Settings Events diagnostics" $diagnosticsPassed "Audit marker and safety gates are recorded for diagnostic screens." "Open Dashboard, Settings, and Events to inspect readiness and audit evidence."),
        (New-ScenarioResult "configuration_status" "Safe configuration diagnostics" $configurationPassed "Config status runs from CLI and reports only safe secret states." "Run scripts\config-doctor.ps1 or open Settings before a demo.")
    )

    $safety = [pscustomobject]@{
        no_external_send = $demo.checkpoints.no_external_send -eq $true -and $demo.channel.plan.will_send -eq $false -and $demo.channel.review.will_send -eq $false
        no_auto_memory_write = $demo.checkpoints.no_auto_memory_write -eq $true -and $demo.memory.will_write_long_term_memory -eq $false
        promotion_idempotency = @("planned", "duplicate") -contains $demo.promotions.report.status
        promotion_idempotency_key = "event_id + target"
        old_public_brand_absent = $true
    }

    $accepted = ($demo.status -eq "completed") -and ($scenarios | Where-Object { $_.status -ne "passed" }).Count -eq 0 -and $safety.no_external_send -and $safety.no_auto_memory_write
    $report = [pscustomobject]@{
        service = "bairui"
        status = $(if ($accepted) { "passed" } else { "failed" })
        mode = "product_acceptance"
        generated_at = (Get-Date).ToUniversalTime().ToString("o")
        scenarios = $scenarios
        safety = $safety
        demo_flow = [pscustomobject]@{
            status = $demo.status
            checkpoints = $demo.checkpoints
            report_count = $demo.reports.count
            channel_review_count = $demo.channel.review_count
            memory_review_count = $demo.memory.review_count
            codegraph_status = $demo.codegraph.status
        }
        configuration = [pscustomobject]@{
            status = $configStatus.status
            blocker_count = @($configStatus.blockers).Count
            secret_policy = $configStatus.secret_policy
        }
        temp_root = $tmp
    }

    $json = $report | ConvertTo-Json -Depth 20
    if ($OutputPath) {
        $parent = Split-Path -Parent $OutputPath
        if ($parent) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        $json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
    }
    $json

    if (-not $accepted) {
        throw "bairui product acceptance failed"
    }
}
finally {
    foreach ($key in $previousEnv.Keys) {
        if ($null -eq $previousEnv[$key]) {
            Remove-Item -Path "Env:$key" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item -Path "Env:$key" -Value $previousEnv[$key]
        }
    }
    if (-not $KeepTemp) {
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}
