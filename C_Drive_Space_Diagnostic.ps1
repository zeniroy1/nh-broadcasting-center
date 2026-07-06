# =====================================================================
# C: Drive Space Diagnostic Script
# C: 드라이브 용량 진단 스크립트
# =====================================================================
# 실행 방법:
#   1) PowerShell을 "관리자 권한"으로 실행
#   2) 이 파일이 있는 폴더로 이동:  cd D:\codding
#   3) 실행 정책 임시 허용:         Set-ExecutionPolicy -Scope Process Bypass
#   4) 스크립트 실행:               .\C_Drive_Space_Diagnostic.ps1
# =====================================================================

$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference = "SilentlyContinue"

function Write-Section($title) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host $title -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Format-Size($bytes) {
    if ($bytes -ge 1GB) { return "{0:N2} GB" -f ($bytes / 1GB) }
    elseif ($bytes -ge 1MB) { return "{0:N2} MB" -f ($bytes / 1MB) }
    elseif ($bytes -ge 1KB) { return "{0:N2} KB" -f ($bytes / 1KB) }
    else { return "$bytes B" }
}

# ---------------------------------------------------------------------
# 1) 드라이브 전체 사용량
# ---------------------------------------------------------------------
Write-Section "1. C: 드라이브 현재 상태"
$drive = Get-PSDrive -Name C
$total = $drive.Used + $drive.Free
$usedGB  = [math]::Round($drive.Used / 1GB, 2)
$freeGB  = [math]::Round($drive.Free / 1GB, 2)
$totalGB = [math]::Round($total       / 1GB, 2)
$pct     = [math]::Round(($drive.Used / $total) * 100, 1)

Write-Host ("총 용량  : {0} GB" -f $totalGB)
Write-Host ("사용 중  : {0} GB ({1}%)" -f $usedGB, $pct) -ForegroundColor Yellow
Write-Host ("남은 공간: {0} GB" -f $freeGB) -ForegroundColor Green

# ---------------------------------------------------------------------
# 2) C: 루트 1단계 폴더별 크기 (Top 15)
# ---------------------------------------------------------------------
Write-Section "2. C:\ 루트 폴더별 용량 (Top 15)"
Write-Host "  ※ 큰 폴더는 측정에 시간이 걸릴 수 있어요... " -ForegroundColor DarkGray

$rootFolders = Get-ChildItem -Path "C:\" -Directory -Force -ErrorAction SilentlyContinue
$results = @()
foreach ($f in $rootFolders) {
    try {
        $size = (Get-ChildItem -Path $f.FullName -Recurse -Force -File -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum
        if ($size) {
            $results += [PSCustomObject]@{
                Folder = $f.FullName
                SizeGB = [math]::Round($size / 1GB, 2)
                SizeBytes = $size
            }
        }
    } catch {}
}
$results | Sort-Object SizeBytes -Descending | Select-Object -First 15 |
    Format-Table Folder, SizeGB -AutoSize

# ---------------------------------------------------------------------
# 3) 흔한 "용량 도둑" 경로들
# ---------------------------------------------------------------------
Write-Section "3. 자주 용량을 차지하는 위치"

$suspects = @(
    "C:\Windows\SoftwareDistribution\Download",   # Windows Update 캐시
    "C:\Windows\Temp",                            # 시스템 임시파일
    "C:\Windows\Installer",                       # MSI 설치 캐시
    "C:\Windows\WinSxS",                          # 컴포넌트 스토어
    "C:\Windows.old",                             # 이전 Windows
    "C:\hiberfil.sys",                            # 최대절전모드 파일
    "C:\pagefile.sys",                            # 페이지 파일
    "C:\swapfile.sys",                            # 스왑 파일
    "$env:LOCALAPPDATA\Temp",                     # 사용자 임시폴더
    "$env:LOCALAPPDATA\Microsoft\Windows\INetCache",   # IE/엣지 캐시
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache",
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
    "$env:LOCALAPPDATA\Packages",                 # 스토어 앱 데이터
    "$env:LOCALAPPDATA\Programs",                 # 사용자 설치 프로그램
    "$env:LOCALAPPDATA\NVIDIA",
    "$env:LOCALAPPDATA\pip\Cache",
    "$env:LOCALAPPDATA\npm-cache",
    "$env:APPDATA\Code\Cache",                    # VSCode 캐시
    "$env:APPDATA\Code\CachedData",
    "$env:APPDATA\Cursor\Cache",
    "$env:USERPROFILE\Downloads",
    "$env:USERPROFILE\Documents",
    "$env:USERPROFILE\.cache",
    "$env:USERPROFILE\.docker",
    "$env:USERPROFILE\AppData\Local\Docker",
    "$env:USERPROFILE\.gradle",
    "$env:USERPROFILE\.m2",
    "$env:USERPROFILE\node_modules",
    "$env:USERPROFILE\OneDrive"
)

$suspectResults = @()
foreach ($p in $suspects) {
    if (Test-Path $p) {
        try {
            if ((Get-Item $p -Force).PSIsContainer) {
                $sz = (Get-ChildItem $p -Recurse -Force -File -ErrorAction SilentlyContinue |
                       Measure-Object Length -Sum).Sum
            } else {
                $sz = (Get-Item $p -Force).Length
            }
            if ($sz) {
                $suspectResults += [PSCustomObject]@{
                    Path = $p
                    Size = Format-Size $sz
                    Bytes = $sz
                }
            }
        } catch {}
    }
}
$suspectResults | Sort-Object Bytes -Descending | Format-Table Path, Size -AutoSize

# ---------------------------------------------------------------------
# 4) 최근 30일 안에 생성/변경된 큰 파일 (>= 100 MB)
# ---------------------------------------------------------------------
Write-Section "4. 최근 30일 안에 만들어진/변경된 큰 파일 (>= 100 MB)"
Write-Host "  ※ 시간이 좀 걸려요..." -ForegroundColor DarkGray

$cutoff = (Get-Date).AddDays(-30)
$bigRecent = Get-ChildItem -Path "C:\" -Recurse -File -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -ge 100MB -and $_.LastWriteTime -ge $cutoff } |
    Sort-Object Length -Descending |
    Select-Object -First 30 FullName, @{N='Size';E={Format-Size $_.Length}}, LastWriteTime

$bigRecent | Format-Table -AutoSize -Wrap

# ---------------------------------------------------------------------
# 5) 시스템 복원 지점 / 휴지통 / 하이버네이션 상태
# ---------------------------------------------------------------------
Write-Section "5. 시스템 복원 / 휴지통 / 최대절전모드"

Write-Host ">> 시스템 복원 지점 사용량:"
vssadmin list shadowstorage 2>$null | Select-String "사용|Used|Allocated|할당|Maximum|최대"

Write-Host ""
Write-Host ">> 휴지통 ($Recycle.Bin) 크기:"
$rb = "C:\`$Recycle.Bin"
if (Test-Path $rb) {
    $rbSize = (Get-ChildItem $rb -Recurse -Force -File -ErrorAction SilentlyContinue |
               Measure-Object Length -Sum).Sum
    Write-Host ("  {0}" -f (Format-Size $rbSize))
}

Write-Host ""
Write-Host ">> 최대절전모드(hiberfil.sys) 상태:"
if (Test-Path "C:\hiberfil.sys") {
    $hib = (Get-Item "C:\hiberfil.sys" -Force).Length
    Write-Host ("  {0}  (powercfg /h off 로 끄면 회수 가능)" -f (Format-Size $hib))
} else {
    Write-Host "  사용 안 함"
}

Write-Section "진단 완료"
Write-Host "결과를 보고 어떤 폴더가 의심되는지 알려주세요." -ForegroundColor Green
