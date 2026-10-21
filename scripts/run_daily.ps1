param([string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $ProjectRoot
try {
    $logDirectory = Join-Path $ProjectRoot 'logs'
    New-Item -ItemType Directory -Force $logDirectory | Out-Null
    $logFile = Join-Path $logDirectory ((Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
    & operations-bi build 2>&1 | Tee-Object -FilePath $logFile
    if ($LASTEXITCODE -ne 0) { throw 'ETL failed; inspect the job log before refreshing reports.' }
} finally {
    Pop-Location
}
