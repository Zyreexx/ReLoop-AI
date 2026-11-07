#!/usr/bin/env bash
# ReLoop AI Diagnostics Agent - Linux Packager (ELF standalone / AppImage compatible)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "================================================================================"
echo "  Packaging ReLoop AI Diagnostics Agent for Linux (ELF x86_64)"
echo "================================================================================"

cd "${REPO_ROOT}"

PYTHON_BIN="python3"
if [ -f "backend/.venv/bin/python" ]; then
    PYTHON_BIN="backend/.venv/bin/python"
fi

${PYTHON_BIN} -m pip install -q pyinstaller
${PYTHON_BIN} scripts/package_agent.py

chmod +x "${REPO_ROOT}/dist/reloop-agent"

echo "[SUCCESS] Linux standalone executable generated at dist/reloop-agent"

