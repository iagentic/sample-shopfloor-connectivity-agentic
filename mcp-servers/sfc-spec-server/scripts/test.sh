#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

set -e

cd "$(dirname "$0")/.."
ROOT_DIR="$(pwd)"

# Print debugging info
echo "Running tests from: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"

# Test script for the SFC Spec MCP Server
echo "Running tests for the SFC Spec MCP Server..."

cd $ROOT_DIR

# Run the agent using uv
uv run python -m sfc_spec.server

echo "Test complete!"
