@echo off
chcp 65001 > nul
echo.
echo ==============================
echo  농협방송단 근태현황 자동 생성
echo ==============================
echo.
echo 원본 파일을 탐색 중...

node "%~dp0tools\create_all.js"

echo.
if %errorlevel% == 0 (
    echo [완료] 농협방송단_근태현황 파일이 생성되었습니다.
) else (
    echo [오류] 문제가 발생했습니다. 원본 파일을 확인해주세요.
)

echo.
pause