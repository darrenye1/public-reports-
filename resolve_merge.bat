@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo  Merge conflict helper (PDF + JS files)
echo ========================================
echo.

cd /d "%~dp0"

set "GIT="
where git >nul 2>&1
if not errorlevel 1 (
  set "GIT=git"
  goto :found_git
)

for /f "delims=" %%G in ('dir /b /ad /o-n "%LOCALAPPDATA%\GitHubDesktop\app-*" 2^>nul') do (
  if exist "%LOCALAPPDATA%\GitHubDesktop\%%G\resources\app\git\cmd\git.exe" (
    set "GIT=%LOCALAPPDATA%\GitHubDesktop\%%G\resources\app\git\cmd\git.exe"
    goto :found_git
  )
)

if exist "%ProgramFiles%\Git\cmd\git.exe" (
  set "GIT=%ProgramFiles%\Git\cmd\git.exe"
  goto :found_git
)

echo Git not found. Use GitHub Desktop:
echo   Repository -^> Open in Git Bash
echo   then run:  bash resolve_merge.sh
pause
exit /b 1

:found_git
echo Using Git: !GIT!
echo.

"!GIT!" diff --name-only --diff-filter=U 2>nul | findstr /r "." >nul
if errorlevel 1 (
  echo No active merge conflicts.
  echo.
  echo If you aborted merge, in GitHub Desktop click Pull origin again,
  echo then run this script while the conflict dialog is open.
  pause
  exit /b 0
)

echo [1/3] Keeping YOUR branch for PDF + generated JS...
"!GIT!" checkout --ours -- reports/ public/reports/ docs/reports/
"!GIT!" checkout --ours -- public/summary-data.js public/dashboard-data.js docs/summary-data.js docs/dashboard-data.js
"!GIT!" add reports/ public/reports/ docs/reports/
"!GIT!" add public/summary-data.js public/dashboard-data.js docs/summary-data.js docs/dashboard-data.js

echo.
echo [2/3] Remaining conflicts (fix in Cursor if listed):
"!GIT!" diff --name-only --diff-filter=U

echo.
echo [3/3] If nothing listed above:
echo   GitHub Desktop -^> Continue merge -^> Commit
echo   Then run:
echo     python equity_research.py --batch-top20 --force
echo     python sync_website.py
echo.
pause
