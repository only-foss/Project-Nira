#!/bin/bash
# Project Nira — Automated Setup Script (Linux/macOS)
set -e

echo "=== Project Nira: One-Command Setup ==="

# 1. Install uv if missing
if ! command -v uv &> /dev/null; then
    echo "Installing 'uv'..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Install Python 3.12 and Create .venv
echo "Setting up Python 3.12 and .venv..."
uv venv --clear --python 3.12 .venv

# 3. Install dependencies
echo "Installing dependencies..."
uv pip install -r python/requirements.txt

# 4. Set up VS Code settings
echo "Configuring VS Code..."
mkdir -p .vscode
cat <<EOF > .vscode/settings.json
{
  "python.defaultInterpreterPath": "\${workspaceFolder}/.venv/bin/python",
  "python.interpreterPaths": ["\${workspaceFolder}/.venv/bin/python"],
  "python.envFile": "\${workspaceFolder}/.env",
  "python.terminal.activateEnvironment": true,
  "python.terminal.activateEnvInCurrentTerminal": true,
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.extraPaths": [
    "\${workspaceFolder}/.venv/lib/python3.12/site-packages"
  ]
}
EOF

echo "=== Setup Complete! ==="
echo "To start the application, run:"
echo "  source .venv/bin/activate"
echo "  python python/nira_dashboard.py"
