param(
  [string]$DestinationRoot = $env:NH_PARTNERS_BACKUP_DIR,
  [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($DestinationRoot)) {
  $DestinationRoot = 'D:\codding\nh_partners_drive_backup'
}

$source = (Resolve-Path $SourceRoot).Path.TrimEnd('\')
$destinationRootPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($DestinationRoot)
$latest = Join-Path $destinationRootPath 'nh_partners_latest'

$destinationRootClean = $destinationRootPath.TrimEnd('\')
if ($destinationRootClean.Equals($source, [System.StringComparison]::OrdinalIgnoreCase) -or
    $destinationRootClean.StartsWith("$source\", [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "DestinationRoot must not be inside SourceRoot. Source=$source Destination=$destinationRootPath"
}

New-Item -ItemType Directory -Force -Path $latest | Out-Null

$excludeDirs = @(
  '.dart_tool',
  '.git',
  '.gradle',
  '.idea',
  '.vscode',
  'build',
  'android_broken'
)

$excludeFiles = @(
  '*.apk',
  '*.aab',
  '*.log',
  '*.tmp'
)

$robocopyArgs = @(
  $source,
  $latest,
  '/MIR',
  '/R:2',
  '/W:2',
  '/FFT',
  '/XD'
) + $excludeDirs + @('/XF') + $excludeFiles

Write-Host "[NH알리미] 백업 시작"
Write-Host "Source:      $source"
Write-Host "Destination: $latest"

& robocopy @robocopyArgs
$code = $LASTEXITCODE

if ($code -ge 8) {
  throw "robocopy failed with exit code $code"
}

$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$marker = Join-Path $latest 'BACKUP_INFO.txt'
@(
  "NH Partners backup",
  "UpdatedAt=$stamp",
  "Source=$source",
  "ExcludedDirs=$($excludeDirs -join ',')",
  "ExcludedFiles=$($excludeFiles -join ',')"
) | Set-Content -Encoding UTF8 -Path $marker

Write-Host "[NH알리미] 백업 완료 — $stamp"
