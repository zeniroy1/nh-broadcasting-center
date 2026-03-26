@echo off
chcp 65001 > nul
echo.
py -3.13 "%~dp0_core\kakao_msg_sender.py"
