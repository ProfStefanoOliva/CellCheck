param(
    [string]$Version = "0.25.0",
    [string]$ExecutablePath = "dist\\CellCheck.exe",
    [string]$OutputRoot = "release_candidates"
)

$projectRoot = Get-Location
$resolvedExe = Join-Path $projectRoot $ExecutablePath

if (-not (Test-Path -LiteralPath $resolvedExe)) {
    Write-Error "Executable not found: $resolvedExe"
    exit 1
}

$requiredFiles = @(
    "LICENSE",
    "NOTICE",
    "README.md",
    "DISCLAIMER.md",
    "TRADEMARKS.md",
    "BRAND_GUIDELINES.md",
    "docs\\RELEASE_CANDIDATE_CHECKLIST.md",
    "docs\\CLEAN_MACHINE_VALIDATION.md"
)

foreach ($relativePath in $requiredFiles) {
    $fullPath = Join-Path $projectRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath)) {
        Write-Error "Required file not found: $fullPath"
        exit 1
    }
}

$bundleRoot = Join-Path $projectRoot $OutputRoot
$bundlePath = Join-Path $bundleRoot ("CellCheck-v" + $Version)

if (Test-Path -LiteralPath $bundlePath) {
    Remove-Item -LiteralPath $bundlePath -Recurse -Force
}

New-Item -ItemType Directory -Path $bundlePath | Out-Null
New-Item -ItemType Directory -Path (Join-Path $bundlePath "docs") | Out-Null

Copy-Item -LiteralPath $resolvedExe -Destination (Join-Path $bundlePath "CellCheck.exe")
Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination $bundlePath
Copy-Item -LiteralPath (Join-Path $projectRoot "NOTICE") -Destination $bundlePath
Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination $bundlePath
Copy-Item -LiteralPath (Join-Path $projectRoot "DISCLAIMER.md") -Destination $bundlePath
Copy-Item -LiteralPath (Join-Path $projectRoot "TRADEMARKS.md") -Destination $bundlePath
Copy-Item -LiteralPath (Join-Path $projectRoot "BRAND_GUIDELINES.md") -Destination $bundlePath
Copy-Item -LiteralPath (Join-Path $projectRoot "docs\\RELEASE_CANDIDATE_CHECKLIST.md") -Destination (Join-Path $bundlePath "docs")
Copy-Item -LiteralPath (Join-Path $projectRoot "docs\\CLEAN_MACHINE_VALIDATION.md") -Destination (Join-Path $bundlePath "docs")

$stagedExe = Join-Path $bundlePath "CellCheck.exe"
$file = Get-Item -LiteralPath $stagedExe
$hash = Get-FileHash -LiteralPath $stagedExe -Algorithm SHA256
$hashFile = Join-Path $bundlePath "SHA256SUMS.txt"

@(
    "File: CellCheck.exe"
    "Size: $($file.Length) bytes"
    "SHA256: $($hash.Hash)"
) | Set-Content -LiteralPath $hashFile -Encoding UTF8

Write-Output "Release candidate bundle: $bundlePath"
Write-Output "Executable size: $($file.Length) bytes"
Write-Output "SHA256: $($hash.Hash)"
