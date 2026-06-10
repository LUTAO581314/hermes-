param(
    [ValidateSet("local", "domain")]
    [string] $Mode = "local",
    [string] $Domain = ""
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

Write-Step "Preparing MOXI Hermes runtime environment"
Ensure-EnvFile
Ensure-EnvValue "POSTGRES_DB" "moxi"
Ensure-EnvValue "POSTGRES_USER" "moxi"

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
    throw "Domain mode requires -Domain, for example: -Mode domain -Domain moxi.example.com"
}

Write-Step "Starting PostgreSQL and Hermes"
& docker compose -f docker-compose.production.yml up -d --build
if ($LASTEXITCODE -ne 0) { throw "docker compose failed" }

Write-Step "Deployment started"
Write-Host "Hermes health:       http://127.0.0.1:8787/health"
Write-Host "Hermes ready:        http://127.0.0.1:8787/ready"
Write-Host "Hermes capabilities: http://127.0.0.1:8787/capabilities"
Write-Host "Runtime readiness:   http://127.0.0.1:8787/runtime/readiness"
