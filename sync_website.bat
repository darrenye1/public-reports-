@echo off
cd /d "%~dp0"
python sync_website.py
if errorlevel 1 exit /b 1
echo Done.
