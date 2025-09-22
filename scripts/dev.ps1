#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [ValidateSet('format', 'lint', 'test', 'all')]
    [string]  = 'all'
)

Set-StrictMode -Version Latest
 = 'Stop'

 = Resolve-Path (Join-Path  '..')
 = Join-Path  '.venv/Scripts/python.exe'
if (-not (Test-Path )) {
     = 'python'
}

function Invoke-Tool {
    param(
        [Parameter(Mandatory)] [string[]] 
    )

     =  -join ' '
    Write-Host ">> " -ForegroundColor Cyan
    & @Arguments
}

function Invoke-Format {
    Invoke-Tool -Arguments @(, '-m', 'ruff', 'format', )
    Invoke-Tool -Arguments @(, '-m', 'black', )
}

function Invoke-Lint {
    Invoke-Tool -Arguments @(, '-m', 'ruff', 'check', )
    Invoke-Tool -Arguments @(, '-m', 'mypy', '--config-file', (Join-Path  'mypy.ini'), )
}

function Invoke-Test {
    Invoke-Tool -Arguments @(, '-m', 'pytest', )
}

switch () {
    'format' { Invoke-Format }
    'lint' { Invoke-Lint }
    'test' { Invoke-Test }
    'all' {
        Invoke-Format
        Invoke-Lint
        Invoke-Test
    }
}
