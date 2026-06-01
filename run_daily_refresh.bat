@echo off
REM Run daily via Task Scheduler: refresh only when financial period changes or data is stale.
cd /d "%~dp0"
python equity_research.py --batch-top20 --refresh-stale --force
if errorlevel 1 (
    echo Refresh failed with exit code %errorlevel%
    exit /b %errorlevel%
)
echo Stale refresh completed.
