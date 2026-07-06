@echo off
cd /d "%~dp0"

echo.
echo ====================================================
echo   Step 3: Calendar Deletion
echo ====================================================
echo.

node process-menu.mjs --delete-latest

echo.
pause
