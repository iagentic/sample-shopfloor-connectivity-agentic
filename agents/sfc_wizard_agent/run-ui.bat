@echo off
REM Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

echo SFC Wizard Chat UI Setup
echo =================================

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo Error: pyproject.toml not found. Please run this script from the sfc_wizard_agent directory.
    exit /b 1
)

REM Check if uv is available
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo uv is not installed. Please install it first:
    echo pip install uv
    exit /b 1
)

REM Check if dependencies are installed
call init.bat

echo.
echo Starting SFC Wizard Chat UI...

REM Get the port from .env or use default
set PORT=5000
for /f "tokens=2 delims==" %%a in ('findstr "FLASK_PORT" .env 2^>nul') do set PORT=%%a

echo The web interface will be available at: http://127.0.0.1:%PORT%
echo Open that URL in your web browser to start chatting
echo Press Ctrl+C to stop the server
echo.

REM Run the UI
uv run sfc-wizard-ui
if %ERRORLEVEL% NEQ 0 (
    echo SFC Wizard Chat UI encountered an error
    exit /b 1
) else (
    echo SFC Wizard Chat UI stopped gracefully
)
