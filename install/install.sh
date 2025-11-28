#!/bin/bash
# Hiero Review Tool Installer - Linux/Mac
# ========================================

echo "Hiero Review Tool Installer"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run installer
python3 "$SCRIPT_DIR/install.py" install "$@"

if [ $? -ne 0 ]; then
    echo ""
    echo "Installation failed."
    exit 1
fi

echo ""
echo "Installation successful!"

