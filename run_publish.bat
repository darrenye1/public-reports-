@echo off
REM Update reports + public/, then open GitHub Desktop to Commit and Push.
cd /d "%~dp0"

call run_daily_refresh.bat
if errorlevel 1 (
    pause
    exit /b %errorlevel%
)

echo.
echo Done. Next steps in GitHub Desktop:
echo   1. Review changes under public/
echo   2. Summary: Update Top20 and reports
echo   3. Commit to main -^> Push origin
echo   4. Vercel will auto-deploy in 1-2 minutes
echo.
start "" "%LocalAppData%\GitHubDesktop\GitHubDesktop.exe" 2>nul
pause
