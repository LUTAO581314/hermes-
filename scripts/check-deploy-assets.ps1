$ErrorActionPreference = "Stop"

$required = @(
    "infra/hermes/env.example",
    "infra/hermes/systemd/bairui-hermes.service",
    "infra/hermes/scripts/deploy-hermes.sh",
    "scripts/deploy-usable.ps1",
    "scripts/deploy-usable.sh",
    "docker-compose.production.yml",
    ".env.example"
)

foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing deployment asset: $path"
    }
}

$parts = @()
foreach ($path in $required) {
    $parts += Get-Content -LiteralPath $path -Raw
}
$combined = $parts -join "`n"

if ($combined -match "BEGIN (RSA|OPENSSH) PRIVATE KEY") {
    throw "Deployment assets must not contain private keys."
}

if ($combined -notmatch "bairui") {
    throw "Deployment assets must include bairui branding."
}

[pscustomobject]@{
    status = "ok"
    mode = "deployment-assets"
    message = "bairui Hermes deployment assets are present."
}
