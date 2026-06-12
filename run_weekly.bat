@echo off
REM Weekly refresh (Mondays only via --weekly): stale tickers + sync site.
cd /d "%~dp0"
python equity_research.py --batch-top20 --refresh-stale --weekly --replace-old
if errorlevel 1 (
    echo Batch run failed with exit code %errorlevel%
    exit /b %errorlevel%
)
call sync_website.bat
if errorlevel 1 exit /b %errorlevel%
echo Reports and website synced successfully.
