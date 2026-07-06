@echo off
chcp 65001 >nul
title 자동 전송 통합 제어 설정
py -3.13 "%~dp0_core\설정변경.py"
pause
