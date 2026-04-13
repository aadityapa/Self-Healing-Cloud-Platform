$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null

$streamlitDir = Join-Path $env:USERPROFILE ".streamlit"
New-Item -ItemType Directory -Force -Path $streamlitDir | Out-Null
@"
[general]
email = ""
"@ | Set-Content (Join-Path $streamlitDir "credentials.toml")
@"
[browser]
gatherUsageStats = false
[server]
headless = true
"@ | Set-Content (Join-Path $streamlitDir "config.toml")

Write-Host "Starting orchestrator API on 0.0.0.0:8000..."
$apiProc = Start-Process -FilePath ".\.venv\Scripts\python.exe" `
  -ArgumentList "-m uvicorn services.orchestrator.app.main:app --host 0.0.0.0 --port 8000" `
  -RedirectStandardOutput ".\logs\api.out.log" `
  -RedirectStandardError ".\logs\api.err.log" `
  -PassThru

Write-Host "Starting dashboard on 0.0.0.0:8501..."
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
$env:STREAMLIT_SERVER_HEADLESS = "true"
$uiProc = Start-Process -FilePath ".\.venv\Scripts\python.exe" `
  -ArgumentList "-m streamlit run tools/dashboard/app.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false --server.headless true" `
  -RedirectStandardOutput ".\logs\ui.out.log" `
  -RedirectStandardError ".\logs\ui.err.log" `
  -PassThru

@{
  api_pid = $apiProc.Id
  ui_pid = $uiProc.Id
  started_at = (Get-Date).ToString("s")
} | ConvertTo-Json | Set-Content ".\logs\platform-pids.json"

Write-Host "Platform started."
Write-Host "API: http://localhost:8000"
Write-Host "Dashboard: http://localhost:8501"
Write-Host "Prometheus (when Docker is available): http://localhost:9090"
