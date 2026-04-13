$ip = (Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike "169.254*" -and $_.IPAddress -ne "127.0.0.1" } |
  Select-Object -First 1 -ExpandProperty IPAddress)

if (-not $ip) {
  Write-Host "Could not auto-detect LAN IP."
  exit 1
}

Write-Host "API URL: http://$ip`:8000"
Write-Host "Dashboard URL: http://$ip`:8501"
Write-Host "Prometheus URL: http://$ip`:9090"
