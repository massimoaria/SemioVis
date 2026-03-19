#!/bin/bash
# SemioVis — Post-install script
# Removes macOS quarantine flag so the app can run without Gatekeeper warnings.

APP="/Applications/SemioVis.app"

echo ""
echo "  SemioVis — Post-Install Setup"
echo "  =============================="
echo ""

if [ ! -d "$APP" ]; then
    echo "  ERROR: SemioVis.app not found in /Applications."
    echo "  Please drag SemioVis.app to the Applications folder first,"
    echo "  then run this script again."
    echo ""
    read -n 1 -s -r -p "  Press any key to close..."
    exit 1
fi

echo "  Removing quarantine flag from SemioVis.app..."
xattr -cr "$APP"

echo ""
echo "  Done! You can now open SemioVis from your Applications folder."
echo ""
read -n 1 -s -r -p "  Press any key to close..."
