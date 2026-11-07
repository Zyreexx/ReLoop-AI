#!/usr/bin/env bash
# ReLoop AI Diagnostics Agent - macOS Standalone Application Packager
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "================================================================================"
echo "  Packaging ReLoop AI Diagnostics Agent for macOS (Universal / x86_64 / arm64)"
echo "================================================================================"

cd "${REPO_ROOT}"

PYTHON_BIN="python3"
if [ -f "backend/.venv/bin/python" ]; then
    PYTHON_BIN="backend/.venv/bin/python"
fi

${PYTHON_BIN} -m pip install -q pyinstaller

# Build single-file CLI
${PYTHON_BIN} scripts/package_agent.py

# Optional: Bundle as macOS .app bundle
APP_DIR="${REPO_ROOT}/dist/ReLoopDiagnostics.app"
mkdir -p "${APP_DIR}/Contents/MacOS"
mkdir -p "${APP_DIR}/Contents/Resources"

cp "${REPO_ROOT}/dist/reloop-agent" "${APP_DIR}/Contents/MacOS/reloop-agent"
chmod +x "${APP_DIR}/Contents/MacOS/reloop-agent"

cat << 'EOF' > "${APP_DIR}/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>reloop-agent</string>
    <key>CFBundleIdentifier</key>
    <string>ai.reloop.diagnostics</string>
    <key>CFBundleName</key>
    <string>ReLoop Diagnostics</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.2.0</string>
</dict>
</plist>
EOF

echo "[SUCCESS] macOS Standalone executable and .app bundle created in dist/"

