$ErrorActionPreference = "Stop"

$source = "D:\codding\nh_partners\nh_reminder\docs\COMMUTE_ALERT_STABILITY_UPDATE_2026-05-08.md"
$fileName = Split-Path -Leaf $source

if (-not (Test-Path -LiteralPath $source)) {
  throw "Source report not found: $source"
}

$drive = Get-PSDrive -Name G -ErrorAction SilentlyContinue
if ($null -eq $drive -or -not (Test-Path -LiteralPath "G:\")) {
  throw "Google Drive G: is not ready. Start Google Drive for desktop and try again."
}

$candidateDirs = @(
  "G:\내 드라이브\nh_partners\docs",
  "G:\My Drive\nh_partners\docs",
  "G:\nh_partners\docs"
)

$targetDir = $candidateDirs | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ([string]::IsNullOrWhiteSpace($targetDir)) {
  $targetDir = $candidateDirs[0]
  New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
}

$target = Join-Path $targetDir $fileName
Copy-Item -LiteralPath $source -Destination $target -Force
Get-Item -LiteralPath $target | Select-Object FullName, Length, LastWriteTime
