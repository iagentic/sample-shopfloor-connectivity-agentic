#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

set -e  # Exit immediately if a command exits with a non-zero status

# Initialize the environment
echo "Setting up the agent environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install dependencies using uv
echo "Installing dependencies with uv..."
uv sync

# Check if .env file exists, if not create it from template
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
fi

# Generate Flask secret key if it doesn't exist
if ! grep -q "^FLASK_SECRET_KEY=" .env; then
    echo "Generating Flask secret key..."
    # Generate a secure random key using Python
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "" >> .env
    echo "# Flask Secret Key (auto-generated)" >> .env
    echo "FLASK_SECRET_KEY=$SECRET_KEY" >> .env
    echo "✅ Generated Flask secret key and saved to .env file"
else
    echo "Flask secret key already exists in .env file"
fi

echo "Setup complete!"
