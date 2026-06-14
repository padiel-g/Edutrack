param(
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$BackupPath = $env:BACKUP_PATH,
    [string]$MaterialUploadPath = $env:MATERIAL_UPLOAD_PATH,
    [int]$RetentionDays = $(if ($env:BACKUP_RETENTION_DAYS) { [int]$env:BACKUP_RETENTION_DAYS } else { 14 })
)

$ErrorActionPreference = "Stop"

if (-not $DatabaseUrl) {
    throw "DATABASE_URL is required."
}
if (-not $BackupPath) {
    throw "BACKUP_PATH is required."
}

$resolvedBackupPath = [System.IO.Path]::GetFullPath($BackupPath)
[System.IO.Directory]::CreateDirectory($resolvedBackupPath) | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path $resolvedBackupPath "edutrack-$timestamp.dump"

& pg_dump --format=custom --no-owner --no-privileges --file=$target $DatabaseUrl
if ($LASTEXITCODE -ne 0) {
    throw "pg_dump failed with exit code $LASTEXITCODE."
}

if ($MaterialUploadPath -and (Test-Path -LiteralPath $MaterialUploadPath -PathType Container)) {
    $uploadTarget = Join-Path $resolvedBackupPath "learning-materials-$timestamp.zip"
    Compress-Archive -LiteralPath $MaterialUploadPath -DestinationPath $uploadTarget -CompressionLevel Optimal
    Write-Output "Upload backup created: $uploadTarget"
}

$cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -LiteralPath $resolvedBackupPath -Filter "edutrack-*.dump" -File |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force
Get-ChildItem -LiteralPath $resolvedBackupPath -Filter "learning-materials-*.zip" -File |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force

Write-Output "Backup created: $target"
