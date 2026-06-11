param(
    [ValidateSet("local", "domain")]
    [string] $Mode = "local",
    [string] $Domain = "",
    [string] $HermesLocalUrl = "http://127.0.0.1:8787",
    [string] $ReadinessFile = "data/readiness.json",
    [int] $ReadinessTimeoutSeconds = 90
)

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host "== $Message =="
}

function New-Secret {
    $bytes = New-Object byte[] 24
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return ([BitConverter]::ToString($bytes) -replace "-", "").ToLowerInvariant()
}

function Ensure-EnvFile {
    if (-not (Test-Path -LiteralPath ".env")) {
        if (-not (Test-Path -LiteralPath ".env.example")) {
            throw ".env.example is missing"
        }
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
    }
}

function Ensure-EnvValue($Name, $Value) {
    $content = Get-Content -LiteralPath ".env" -Raw
    if ($content -match "(?m)^$([regex]::Escape($Name))=") {
        if ($content -match "(?m)^$([regex]::Escape($Name))=\s*$") {
            $content = $content -replace "(?m)^$([regex]::Escape($Name))=.*$", "$Name=$Value"
            Set-Content -LiteralPath ".env" -Value $content -NoNewline
        }
        return
    }
    Add-Content -LiteralPath ".env" -Value "$Name=$Value"
}

function Set-EnvValue($Name, $Value) {
    $content = Get-Content -LiteralPath ".env" -Raw
    if ($content -match "(?m)^$([regex]::Escape($Name))=") {
        $content = $content -replace "(?m)^$([regex]::Escape($Name))=.*$", "$Name=$Value"
        Set-Content -LiteralPath ".env" -Value $content -NoNewline
        return
    }
    Add-Content -LiteralPath ".env" -Value "$Name=$Value"
}

function Wait-Endpoint($Label, $Path) {
    $deadline = (Get-Date).AddSeconds($ReadinessTimeoutSeconds)
    $url = "$HermesLocalUrl$Path"
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-RestMethod -Uri $url -TimeoutSec 5 | Out-Null
            Write-Host "$Label reachable: $url"
            return
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    throw "$Label did not become reachable before timeout: $url"
}

function Write-ReadinessFile {
    $parent = Split-Path -Parent $ReadinessFile
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    $endpoints = [ordered]@{}
    $overall = "ready"
    foreach ($item in @(
        @{ Name = "health"; Path = "/health" },
        @{ Name = "ready"; Path = "/ready" },
        @{ Name = "capabilities"; Path = "/capabilities" },
        @{ Name = "runtime_readiness"; Path = "/runtime/readiness" }
    )) {
        $url = "$HermesLocalUrl$($item.Path)"
        try {
            $body = Invoke-RestMethod -Uri $url -TimeoutSec 10
            $endpoints[$item.Name] = [ordered]@{
                status = "reachable"
                url = $url
                body = $body
            }
        } catch {
            $overall = "blocked"
            $endpoints[$item.Name] = [ordered]@{
                status = "error"
                url = $url
                error = $_.Exception.Message
            }
        }
    }

    $demoFlowUrl = "$HermesLocalUrl/demo/flow"
    try {
        $demoFlow = Invoke-RestMethod -Uri $demoFlowUrl -Method Post -Body "{}" -ContentType "application/json" -TimeoutSec 30
        $endpoints["demo_flow"] = [ordered]@{
            status = "completed"
            url = $demoFlowUrl
            body = $demoFlow
        }
        if ($demoFlow.demo_flow.status -ne "completed") {
            $overall = "partial"
        }
    } catch {
        $overall = "blocked"
        $endpoints["demo_flow"] = [ordered]@{
            status = "error"
            url = $demoFlowUrl
            error = $_.Exception.Message
        }
    }

    $runtime = $endpoints["runtime_readiness"].body.runtime_readiness
    if ($runtime -and $runtime.status -eq "blocked") {
        $overall = "blocked"
    } elseif ($overall -eq "ready" -and $runtime -and $runtime.status -eq "partial") {
        $overall = "partial"
    }

    [ordered]@{
        status = $overall
        generated_at_unix = [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        base_url = $HermesLocalUrl
        console_url = "$HermesLocalUrl/console"
        endpoints = $endpoints
    } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $ReadinessFile -Encoding UTF8
}

Write-Step "Preparing bairui runtime environment"
Ensure-EnvFile
Set-EnvValue "POSTGRES_DB" "bairui"
Set-EnvValue "POSTGRES_USER" "bairui"

$envContent = Get-Content -LiteralPath ".env" -Raw
if ($envContent -match "(?m)^POSTGRES_PASSWORD=\s*$" -or $envContent -notmatch "(?m)^POSTGRES_PASSWORD=") {
    Ensure-EnvValue "POSTGRES_PASSWORD" (New-Secret)
}
if ($envContent -match "(?m)^SONIC_PASSWORD=\s*$" -or $envContent -notmatch "(?m)^SONIC_PASSWORD=") {
    Ensure-EnvValue "SONIC_PASSWORD" (New-Secret)
}

Ensure-EnvValue "HERMES_ENV" "production"
Ensure-EnvValue "HERMES_HOST" "127.0.0.1"
Ensure-EnvValue "HERMES_PORT" "8787"
Ensure-EnvValue "SONIC_HOST" "sonic"
Ensure-EnvValue "SONIC_PORT" "1491"

New-Item -ItemType Directory -Force -Path "src", "tests", "data/postgres", "data/sonic", "logs", "obsidian-vault" | Out-Null

if ($Mode -eq "domain" -and [string]::IsNullOrWhiteSpace($Domain)) {
    throw "Domain mode requires -Domain, for example: -Mode domain -Domain bairui.example.com"
}

Write-Step "Starting PostgreSQL and bairui"
& docker compose -f docker-compose.production.yml up -d --build
if ($LASTEXITCODE -ne 0) { throw "docker compose failed" }

Write-Step "Deployment started"
Wait-Endpoint "bairui health" "/health"
Wait-Endpoint "bairui ready" "/ready"
Wait-Endpoint "Runtime readiness" "/runtime/readiness"
Write-ReadinessFile

Write-Host "bairui health:       $HermesLocalUrl/health"
Write-Host "bairui ready:        $HermesLocalUrl/ready"
Write-Host "bairui capabilities: $HermesLocalUrl/capabilities"
Write-Host "Runtime readiness:   $HermesLocalUrl/runtime/readiness"
Write-Host "bairui console:      $HermesLocalUrl/console"
Write-Host "Demo Flow evidence:  $ReadinessFile -> endpoints.demo_flow"
Write-Host "Readiness file:      $ReadinessFile"
