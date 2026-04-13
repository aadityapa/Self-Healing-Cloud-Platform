param(
  [string]$HostAddress = "0.0.0.0",
  [int]$Port = 8000
)

Write-Host "Starting local orchestrator on $HostAddress:$Port"
python -m uvicorn services.orchestrator.app.main:app --host $HostAddress --port $Port --reload
