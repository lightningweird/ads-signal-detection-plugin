# Start Freqtrade Execution Plugin
Write-Host "Starting Freqtrade Execution Plugin..." -ForegroundColor Green
Write-Host "Make sure Redis is running!" -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot

# Start in dry run mode (paper trading)
python -m freqtrade trade --config config.json --strategy AdsExecutionStrategy --dry-run

Read-Host "Press Enter to exit"
