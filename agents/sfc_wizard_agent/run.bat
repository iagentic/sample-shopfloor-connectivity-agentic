@echo off
REM Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

REM Check if uv is installed
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo uv is not installed. Please install it first:
    echo pip install uv
    exit /b 1
)

REM Check if dependencies are installed
call init.bat

REM Run the agent using uv
uv run python -m sfc_wizard.agent
