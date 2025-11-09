#!/bin/bash
# Create macOS DMG installer with proper layout

set -e

APP_NAME="node3-agent"
DMG_NAME="${APP_NAME}-installer"
VERSION=$(python3 -c "import re; content=open('main.py').read(); match=re.search(r\"VERSION\s*=\s*['\\\"]([^'\\\"]+)['\\\"]\", content); print(match.group(1) if match else '1.0.0')" 2>/dev/null || echo "1.0.0")
DMG_FILE="${DMG_NAME}-${VERSION}.dmg"

echo "Creating macOS DMG installer..."
echo "Version: ${VERSION}"

# Check if .app exists
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo "Error: dist/${APP_NAME}.app not found"
    echo "Run: python build.py --type macos"
    exit 1
fi

# Create temporary DMG directory
DMG_TEMP="dist/dmg_temp"
rm -rf "${DMG_TEMP}"
mkdir -p "${DMG_TEMP}"

# Copy .app to temp directory
cp -R "dist/${APP_NAME}.app" "${DMG_TEMP}/"

# Create Applications symlink
ln -s /Applications "${DMG_TEMP}/Applications"

# Create a nice background (optional - can add .png background)
# cp dmg_background.png "${DMG_TEMP}/.background.png" 2>/dev/null || true

# Remove old DMG if exists
rm -f "${DMG_FILE}"

# Create DMG
echo "Creating DMG image..."
hdiutil create -volname "${APP_NAME}" \
    -srcfolder "${DMG_TEMP}" \
    -ov \
    -format UDZO \
    -fs HFS+ \
    "${DMG_FILE}"

# Clean up temp directory
rm -rf "${DMG_TEMP}"

# Get DMG size
DMG_SIZE=$(du -h "${DMG_FILE}" | cut -f1)
echo ""
echo "✓ DMG created successfully!"
echo "  File: ${DMG_FILE}"
echo "  Size: ${DMG_SIZE}"

# Optional: Mount DMG to verify
echo ""
read -p "Mount DMG to verify? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    hdiutil attach "${DMG_FILE}"
    echo "DMG mounted. Check it out, then press Enter to unmount..."
    read
    hdiutil detach "/Volumes/${APP_NAME}"
fi

