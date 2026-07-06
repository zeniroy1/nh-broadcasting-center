@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo [1/4] Checking Python...
where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PY=python"
    ) else (
        echo Python is not installed.
        echo Install Python 3.10 or newer, then run this file again.
        echo https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo [2/4] Preparing virtual environment...
if exist ".venv\Scripts\python.exe" (
    call ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
    if errorlevel 1 (
        echo Existing virtual environment is invalid. Recreating...
        rmdir /s /q ".venv"
    )
)
if not exist ".venv\Scripts\python.exe" (
    %PY% -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [3/4] Installing required packages...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install packages.
    pause
    exit /b 1
)

echo [4/4] Generating reports...
call ".venv\Scripts\python.exe" "scripts\generate_reports.py"
if errorlevel 1 (
    echo Report generation failed.
    pause
    exit /b 1
)

echo.
echo Done. Check the generated md/csv files.
pause
