@echo off
echo Starting Freqtrade Execution Plugin...
echo Make sure Redis is running!
echo.

cd /d "%~dp0"

REM Start in dry run mode (paper trading)
python -m freqtrade trade --config config.json --strategy AdsExecutionStrategy --dry-run

pause
