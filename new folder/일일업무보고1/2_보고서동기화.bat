@echo off
chcp 65001 >nul
title 일일업무보고 백업 동기화
cd /d "%~dp0"
"C:\Python313\python.exe" "_core\백업동기화.py"
pause
