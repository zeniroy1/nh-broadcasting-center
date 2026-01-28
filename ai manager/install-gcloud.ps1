# Google Cloud SDK 자동 설치 스크립트

Write-Host "Google Cloud SDK 다운로드 및 설치 시작..." -ForegroundColor Green

$installerPath = "$env:TEMP\GoogleCloudSDKInstaller.exe"
$downloadUrl = "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe"

try {
    # SDK 다운로드
    Write-Host "다운로드 중... 이 작업은 몇 분이 걸릴 수 있습니다." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    
    Write-Host "다운로드 완료!" -ForegroundColor Green
    Write-Host "설치 프로그램을 실행합니다..." -ForegroundColor Yellow
    
    # 설치 프로그램 실행 (사용자 확인 필요)
    Start-Process -FilePath $installerPath -Wait
    
    Write-Host "`n설치가 완료되었습니다!" -ForegroundColor Green
    Write-Host "새 PowerShell 창을 열어 'gcloud init' 명령어를 실행하세요." -ForegroundColor Cyan
    
} catch {
    Write-Host "오류 발생: $_" -ForegroundColor Red
    Write-Host "`n수동 설치를 위해 다음 링크를 열어주세요:" -ForegroundColor Yellow
    Write-Host "https://cloud.google.com/sdk/docs/install" -ForegroundColor Cyan
}
