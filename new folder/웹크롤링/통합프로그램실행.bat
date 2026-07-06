@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo Starting integrated LH/HUG program.
echo Working folder: %CD%
echo.

set "APP_PY=%CD%\runtime\python\python.exe"
if not exist "%APP_PY%" (
    echo Included Python was not found: %APP_PY%
    echo Please reinstall the program with the Python-included installer.
    pause
    exit /b 1
)

echo Checking first-run setup...
"%APP_PY%" -m app.bootstrap
if errorlevel 1 (
    echo.
    echo Setup failed. Internet may be required for the first package install.
    pause
    exit /b 1
)

"%APP_PY%" -m app.server
if errorlevel 1 (
    echo.
    echo Failed to start the integrated program.
    echo Check that the app folder exists beside this batch file.
    pause
    exit /b 1
)
