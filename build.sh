#!/bin/bash
# Build script for creating distributable packages

set -e

echo "======================================"
echo "Building PDF Toolbox Packages"
echo "======================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Building for: $OS"
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.spec 2>/dev/null || true

# Build executable
echo "Building executable..."
if [ "$OS" == "windows" ]; then
    pyinstaller --noconsole --onefile --name split_pdf_gui \
        --icon=icon.ico \
        --add-data "presentation/i18n/locales;presentation/i18n/locales" \
        --hidden-import=tkinter \
        split_pdf_gui.py
elif [ "$OS" == "macos" ]; then
    pyinstaller --windowed --onefile --name "PDF Toolbox" \
        --icon=icon.icns \
        --add-data "presentation/i18n/locales:presentation/i18n/locales" \
        split_pdf_gui.py
else
    pyinstaller --onefile --name pdf-toolbox \
        --add-data "presentation/i18n/locales:presentation/i18n/locales" \
        split_pdf_gui.py
fi

echo ""
echo "✓ Build completed!"
echo "Output: dist/"

# Create installer (platform-specific)
if [ "$OS" == "windows" ]; then
    echo ""
    echo "To create Windows installer, run: makensis installer.nsi"
elif [ "$OS" == "macos" ]; then
    echo ""
    echo "To create DMG, run:"
    echo "  create-dmg --volname 'PDF Toolbox' --window-size 600 400 PDF-Toolbox.dmg 'dist/PDF Toolbox.app'"
fi
