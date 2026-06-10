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

[pscustomobject]@{
    status = "ok"
    mode = "runtime-foundation"
    message = "MOXI Hermes runtime foundation is present."
}
