@echo off
cd /d "%~dp0"

echo.
echo ====================================================
echo   Step 2: Calendar Registration
echo ====================================================
echo.

node process-menu.mjs --calendar-latest

echo.
pause
