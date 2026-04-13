$pidFile = ".\logs\platform-pids.json"
if (-not (Test-Path $pidFile)) {
  Write-Host "No running platform PID file found at $pidFile"
  exit 0
}

$pids = Get-Content $pidFile | ConvertFrom-Json

foreach ($name in @("api_pid", "ui_pid")) {
  $pidValue = $pids.$name
  if ($pidValue) {
    try {
      Stop-Process -Id $pidValue -Force -ErrorAction Stop
      Write-Host "Stopped $name process id $pidValue"
    } catch {
      Write-Host "$name process id $pidValue not running."
    }
  }
}

Remove-Item $pidFile -Force
Write-Host "Platform stopped."
