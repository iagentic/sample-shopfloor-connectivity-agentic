#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

# Test script for the restricted agent
echo "Running tests for the restricted agent..."

# Run the agent using uv
uv run python -m sample_sfc_agent.restricted_agent

echo "Test complete!"
