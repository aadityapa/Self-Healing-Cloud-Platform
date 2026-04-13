Write-Host "Installing orchestrator dependencies..."
.\.venv\Scripts\python.exe -m pip install -r .\services\orchestrator\requirements.txt

Write-Host "Installing dashboard dependencies..."
.\.venv\Scripts\python.exe -m pip install -r .\tools\dashboard\requirements.txt

Write-Host "Dependency installation completed."
