$ErrorActionPreference = "Stop"

$required = @(
    "README.md",
    "docs/00-product-blueprint.md",
    "docs/17-three-pillar-commercial-project-plan.md",
    "docs/18-vendor-runtime-integration.md",
    "src/hermes/server.py",
    "src/hermes/storage.py",
    "tests/test_runtime.py",
    "Dockerfile",
    "docker-compose.production.yml",
    ".env.example"
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
