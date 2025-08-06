@echo off
REM Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

echo Setting up the agent environment...

REM Check if uv is installed
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo uv is not installed. Please install it first:
    echo pip install uv
    exit /b 1
)

REM Install dependencies using uv
echo Installing dependencies with uv...
uv sync

REM Check if .env file exists, if not create it from template
if not exist ".env" (
    echo Creating .env file from template...
    copy ..\..\\.env.template .env
)

REM Generate Flask secret key if it doesn't exist
findstr "^FLASK_SECRET_KEY=" .env >nul
if %ERRORLEVEL% NEQ 0 (
    echo Generating Flask secret key...
    REM Generate a secure random key using Python
    for /f %%i in ('python -c "import secrets; print(secrets.token_urlsafe(32))"') do set SECRET_KEY=%%i
    echo. >> .env
    echo # Flask Secret Key (auto-generated) >> .env
    echo FLASK_SECRET_KEY=%SECRET_KEY% >> .env
    echo ✅ Generated Flask secret key and saved to .env file
) else (
    echo Flask secret key already exists in .env file
)

echo Setup complete!
