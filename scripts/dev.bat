@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%F in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fF"

if "%1"=="" goto run_all
set "TASK=%1"
goto dispatch

:run_all
set "TASK=all"

:dispatch
if /I "%TASK%"=="bootstrap" goto bootstrap
if /I "%TASK%"=="format" goto run_ps
if /I "%TASK%"=="lint" goto run_ps
if /I "%TASK%"=="test" goto run_ps
if /I "%TASK%"=="all" goto run_ps

echo Unsupported task: %TASK%
exit /b 1

:bootstrap
if not exist "%PROJECT_ROOT%\.venv" (
    python -m venv "%PROJECT_ROOT%\.venv"
)
set "VENV_PY=%PROJECT_ROOT%\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo Failed to locate virtual environment python executable.
    exit /b 1
)
call "%VENV_PY%" -m pip install --upgrade pip
call "%VENV_PY%" -m pip install ruff black mypy pytest pre-commit nox
call "%VENV_PY%" -m pre_commit install
exit /b 0

:run_ps
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\dev.ps1" -Task %TASK%
exit /b %errorlevel%
