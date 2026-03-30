#!/bin/bash
# Project Nira — Environment Setup Script
# This script automates the installation of all Python dependencies.

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Project Nira: Automated Setup ===${NC}"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install it to proceed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv and install dependencies
echo -e "${GREEN}Installing dependencies from python/requirements.txt...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r python/requirements.txt

# Check for GNU Octave
if ! command -v octave &> /dev/null; then
    echo -e "${BLUE}Note: GNU Octave is not detected. It is required for the analysis scripts in tests/analysis/.${NC}"
    echo "On Debian/Ubuntu: sudo apt install octave"
fi

echo -e "${GREEN}Setup complete!${NC}"
echo -e "To start the dashboard, run: ${BLUE}source venv/bin/activate && python python/nira_dashboard.py${NC}"
