#!/bin/bash
# Build standalone executable with PyInstaller

set -e

echo "Building Lakeventory standalone executable..."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/

# Build executable
echo "Building executable..."
pyinstaller lakeventory.spec

# Check result
if [ -f "dist/lakeventory" ] || [ -f "dist/lakeventory.exe" ]; then
    echo ""
    echo "✓ Build successful!"
    echo ""
    echo "Executable location:"
    ls -lh dist/lakeventory* 2>/dev/null || true
    echo ""
    echo "Test the executable:"
    echo "  ./dist/lakeventory version"
    echo "  ./dist/lakeventory collect --help"
else
    echo "✗ Build failed - executable not found"
    exit 1
fi
