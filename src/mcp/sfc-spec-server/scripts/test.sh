#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

set -e

cd "$(dirname "$0")/.."
ROOT_DIR="$(pwd)"

# Print debugging info
echo "Running tests from: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"

# Test script for the SFC spec MCP server
echo "Running tests for the SFC spec MCP server..."

cd $ROOT_DIR

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

# Run the test using uv
uv run python test_server.py

echo "Test complete!"
