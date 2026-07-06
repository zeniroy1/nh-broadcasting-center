@echo off
REM Build MusinsaBuyerApp.exe from source.
REM Run this from anywhere; it locates submission/src relative to itself.
REM Requirements: Python 3.10+ on PATH, with pip able to install pyinstaller.

setlocal
set SCRIPT_DIR=%~dp0
set SRC_DIR=%SCRIPT_DIR%..

echo [0/3] Checking Python...
python --version
if errorlevel 1 goto :error

echo [1/3] Installing/upgrading PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto :error

echo [2/3] Running unit tests before packaging...
pushd "%SRC_DIR%"
python -m unittest discover -s tests -p "test_*.py"
if errorlevel 1 goto :popup_error

echo [3/3] Building MusinsaBuyerApp.exe with PyInstaller...
python -m PyInstaller packaging\musinsa_buyer_app.spec --noconfirm
if errorlevel 1 goto :popup_error

popd
echo.
echo Done. The executable is at: %SRC_DIR%\dist\MusinsaBuyerApp.exe
echo Double-click it to start the server and open the app in your browser.
echo.
pause
exit /b 0

:popup_error
popd

:error
echo.
echo Build failed. See the output above for details.
echo.
pause
exit /b 1
