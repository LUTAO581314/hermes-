$ErrorActionPreference = "Stop"

$required = @(
    "README.md",
    "docs/00-product-blueprint.md",
    "docs/17-three-pillar-commercial-project-plan.md",
    "docs/18-vendor-runtime-integration.md",
    "src/hermes/server.py",
    "src/hermes/storage.py",
    "src/hermes/model_gateway.py",
    "src/hermes/db.py",
    "src/hermes/runtime_readiness.py",
    "src/hermes/adapters/funasr.py",
    "src/hermes/adapters/sonic.py",
    "requirements.txt",
    "tests/test_runtime.py",
    "Dockerfile",
    "docker-compose.production.yml",
    ".env.example",
    "infra/hermes/env.example",
    "infra/hermes/systemd/bairui-hermes.service",
    "infra/hermes/scripts/deploy-hermes.sh",
    "infra/sonic/config.cfg"
)

foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing required skeleton file: $path"
    }
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("bairui-smoke-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    $env:HERMES_DATA_DIR = Join-Path $tmp "data"
    $env:HERMES_LOG_DIR = Join-Path $tmp "logs"
    $env:HERMES_OBSIDIAN_VAULT_DIR = Join-Path $tmp "vault"
    $env:BAIRUI_CODEGRAPH_ROOT = Join-Path $tmp "codegraph"
    $env:BAIRUI_CHANNELS_ENABLED = "1"
    $flowRaw = python -m src.hermes demo flow
    $flow = $flowRaw | ConvertFrom-Json
    if ($flow.demo_flow.status -ne "completed") {
        throw "Demo flow did not complete: $($flowRaw)"
    }
    if ($flow.demo_flow.checkpoints.no_external_send -ne $true) {
        throw "Demo flow external-send checkpoint failed."
    }
    if ($flow.demo_flow.checkpoints.no_auto_memory_write -ne $true) {
        throw "Demo flow memory safety checkpoint failed."
    }
}
finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

[pscustomobject]@{
    status = "ok"
    mode = "product-closure"
    message = "bairui runtime foundation and demo flow are present."
}
