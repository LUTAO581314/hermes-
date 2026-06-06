$ErrorActionPreference = "Stop"

$port = if ($env:HERMES_PORT) { $env:HERMES_PORT } else { "8787" }
$baseUrl = "http://127.0.0.1:$port"

$health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 5
$ready = Invoke-RestMethod -Uri "$baseUrl/ready" -TimeoutSec 5

[pscustomobject]@{
    health = $health.status
    ready = $ready.status
    service = $health.service
    safe_mode = $health.safe_mode
}
