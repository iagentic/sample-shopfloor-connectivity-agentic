#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

# lint.sh - Lint the python code

set -e  # Exit immediately if a command exits with a non-zero status

cd "$(dirname "$0")/.."
ROOT_DIR="$(pwd)"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if dependencies are installed
if [ ! -f "uv.lock" ]; then
    echo "Dependencies not found. Running init script..."
    ./scripts/init.sh
fi

# Install dev dependencies and run black formatter on all Python code
uv sync --extra dev
uv run black *.py
