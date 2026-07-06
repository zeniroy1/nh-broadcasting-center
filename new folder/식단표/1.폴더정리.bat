@echo off
cd /d "%~dp0"

echo.
echo ====================================================
echo   Weekly Menu - Step 1: Folder Organizer
echo ====================================================
echo.
echo Detecting image files...
echo.

node process-menu.mjs --setup

echo.
pause
