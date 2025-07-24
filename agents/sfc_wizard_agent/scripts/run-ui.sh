#!/bin/bash

# Script to run the SFC Wizard Chat UI
# This script installs dependencies and starts the web interface

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏭 SFC Wizard Chat UI Setup${NC}"
echo "================================="

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    echo -e "${RED}❌ Error: pyproject.toml not found. Please run this script from the sfc_wizard_agent directory.${NC}"
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠️  uv is not installed. Please install uv first:${NC}"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo -e "${BLUE}📦 Installing dependencies...${NC}"
if uv sync; then
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Check for .env file and create from template if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo -e "${YELLOW}⚠️ No .env file found. Creating one from template...${NC}"
    if [[ -f ".env.template" ]]; then
        cp .env.template .env
        echo -e "${GREEN}✅ Created .env file from template${NC}"
    else
        echo -e "${YELLOW}⚠️ No .env.template found. Using default configuration.${NC}"
    fi
fi

echo ""
echo -e "${PURPLE}🚀 Starting SFC Wizard Chat UI...${NC}"
# Get the port from .env or use default
if [[ -f ".env" ]]; then
    PORT=$(grep "FLASK_PORT" .env | cut -d "=" -f2)
fi
PORT=${PORT:-5000}

echo -e "${YELLOW}💡 The web interface will be available at: http://127.0.0.1:${PORT}${NC}"
echo -e "${YELLOW}💡 Open that URL in your web browser to start chatting${NC}"
echo -e "${YELLOW}💡 Press Ctrl+C to stop the server${NC}"
echo ""

# Run the UI
if uv run sfc-wizard-ui; then
    echo -e "${GREEN}✅ SFC Wizard Chat UI stopped gracefully${NC}"
else
    echo -e "${RED}❌ SFC Wizard Chat UI encountered an error${NC}"
    exit 1
fi
