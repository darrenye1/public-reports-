@echo off
REM Daily/weekly refresh: only updates tickers with new financials or stale data.
cd /d "%~dp0"
python equity_research.py --batch-top20 --refresh-stale --weekly --replace-old
if errorlevel 1 (
    echo Batch run failed with exit code %errorlevel%
    exit /b %errorlevel%
)
echo Reports updated successfully.
