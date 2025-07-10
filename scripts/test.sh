#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

# Test script for the SFC wizard agent
echo "Running tests for the SFC wizard agent..."

# Run the agent using uv
uv run python -m src.agents.sfc_wizard_agent

echo "Test complete!"
