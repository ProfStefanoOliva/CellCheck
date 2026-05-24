param(
    [string]$ExecutablePath = "dist\\CellCheck.exe"
)

$resolvedPath = Join-Path (Get-Location) $ExecutablePath

if (-not (Test-Path -LiteralPath $resolvedPath)) {
    Write-Error "Executable not found: $resolvedPath"
    exit 1
}

$file = Get-Item -LiteralPath $resolvedPath
$hash = Get-FileHash -LiteralPath $resolvedPath -Algorithm SHA256

Write-Output "Executable path: $($file.FullName)"
Write-Output "Executable size: $($file.Length) bytes"
Write-Output "SHA256: $($hash.Hash)"
