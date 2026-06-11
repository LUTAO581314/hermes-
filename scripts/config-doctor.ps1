param(
    [string]$OutputPath = "",
    [switch]$AllowBlocked
)

$ErrorActionPreference = "Stop"

$raw = python -m src.hermes config-status | Out-String
$exitCode = $LASTEXITCODE
$payload = $raw | ConvertFrom-Json
$status = $payload.config_status.status

if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $raw.Trim() | Set-Content -LiteralPath $OutputPath -Encoding UTF8
}

$blocked = $status -eq "blocked" -or $exitCode -ne 0
$result = [pscustomobject]@{
    service = "bairui"
    status = $(if ($blocked) { "blocked" } else { "ok" })
    config_status = $status
    secret_policy = $payload.config_status.secret_policy
    blocker_count = @($payload.config_status.blockers).Count
    blockers = $payload.config_status.blockers
    next_step = $payload.config_status.next_step
    output_path = $OutputPath
}

$result | ConvertTo-Json -Depth 20

if ($blocked -and -not $AllowBlocked) {
    throw "bairui configuration is blocked"
}
