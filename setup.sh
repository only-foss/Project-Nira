#!/bin/bash
# Project Nira — Automated Setup Script (Linux/macOS)
set -e

echo "=== Project Nira: One-Command Setup ==="

# 1. Install system dependencies (Linux)
if command -v apt-get &> /dev/null; then
    echo "Installing system GUI dependencies (python3-tk)..."
    sudo apt-get update
    sudo apt-get install -y python3-tk
elif command -v dnf &> /dev/null; then
    echo "Installing system GUI dependencies (python3-tkinter)..."
    sudo dnf install -y python3-tkinter
fi

# 2. Install uv if missing
if ! command -v uv &> /dev/null; then
    echo "Installing 'uv'..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 3. Install Python 3.12 and Create .venv
echo "Setting up Python 3.12 and .venv..."
uv venv --clear --python 3.12 .venv

# 4. Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt
uv pip install -e .

# 5. Set up VS Code settings
echo "Configuring VS Code..."
mkdir -p .vscode
echo '{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.interpreterPaths": ["${workspaceFolder}/.venv/bin/python"],
  "python.envFile": "${workspaceFolder}/.env",
  "python.terminal.activateEnvironment": true,
  "python.terminal.activateEnvInCurrentTerminal": true,
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.extraPaths": [
    "${workspaceFolder}/.venv/lib/python3.12/site-packages"
  ]
}' > .vscode/settings.json

echo "=== Setup Complete! ==="
echo "To run the dashboard:"
echo "source .venv/bin/activate"
echo "python python/nira_dashboard.py"
