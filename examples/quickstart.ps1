param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PythonExecutable = 'python'
)

$ErrorActionPreference = 'Stop'

# The CLI composes emails with a deterministic mock backend; no network calls are made.
$fixtures = Join-Path $RepositoryRoot 'tests\fixtures'
if (-not (Test-Path -Path $fixtures)) {
    throw "Fixture directory not found: $fixtures"
}

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("uas-pipeline-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempDir | Out-Null
Copy-Item -Path (Join-Path $fixtures '*.html') -Destination $tempDir

Write-Host 'Running pipeline CLI with mocked network dependencies...'
$arguments = @(
    'run',
    '--input', $tempDir,
    '--from', 'parse',
    '--to', 'compose',
    '--limit', '1',
    '--language', 'en'
)

try {
    & $PythonExecutable (Join-Path $RepositoryRoot 'src\pipeline\cli.py') @arguments
} finally {
    if (Test-Path -LiteralPath $tempDir) {
        Remove-Item -LiteralPath $tempDir -Force -Recurse
    }
}
