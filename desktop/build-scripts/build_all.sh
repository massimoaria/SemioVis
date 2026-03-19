#!/bin/bash
# SemioVis — Full desktop build script
# Builds C++ core, bundles backend, builds frontend, and packages with Tauri
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "=== SemioVis Desktop Build ==="
echo "Root: $ROOT"

# 1. Build C++ core
echo ""
echo "--- Step 1: Build C++ core ---"
cd "$ROOT/backend/cpp"
/opt/homebrew/bin/cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="/opt/homebrew" 2>&1 | tail -3
/opt/homebrew/bin/cmake --build build -j$(sysctl -n hw.ncpu)
echo "C++ core built."

# 2. Build React frontend
echo ""
echo "--- Step 2: Build frontend ---"
cd "$ROOT/frontend"
npm run build
echo "Frontend built."

# 3. Bundle backend with PyInstaller (optional — for production builds)
if [ "$1" = "--bundle-backend" ]; then
    echo ""
    echo "--- Step 3: Bundle backend with PyInstaller ---"
    cd "$ROOT"
    "$ROOT/.venv/bin/pip" install pyinstaller 2>&1 | tail -2
    "$ROOT/.venv/bin/python" "$ROOT/desktop/build-scripts/bundle_backend.py"
    echo "Backend bundled."
fi

# 4. Build Tauri app
echo ""
echo "--- Step 4: Build Tauri desktop app ---"
cd "$ROOT/desktop/src-tauri"

if [ "$1" = "--release" ] || [ "$1" = "--bundle-backend" ]; then
    cargo tauri build
    echo ""

    # 5. Rebuild DMG with install script visible in the DMG window
    echo "--- Step 5: Rebuild DMG with install script ---"
    DMG_DIR="$ROOT/desktop/src-tauri/target/release/bundle/dmg"
    APP_DIR="$ROOT/desktop/src-tauri/target/release/bundle/macos"
    SCRIPT_SRC="$ROOT/desktop/src-tauri/scripts/Install SemioVis.command"

    if [ -d "$APP_DIR/SemioVis.app" ] && [ -f "$SCRIPT_SRC" ]; then
        # Create a staging directory with app + script
        STAGING=$(mktemp -d)
        cp -R "$APP_DIR/SemioVis.app" "$STAGING/"
        cp "$SCRIPT_SRC" "$STAGING/Install SemioVis.command"
        ln -s /Applications "$STAGING/Applications"

        # Remove old DMG
        rm -f "$DMG_DIR"/SemioVis_*.dmg

        # Create new DMG
        ARCH=$(uname -m)
        DMG_NAME="SemioVis_1.0.0_${ARCH}.dmg"
        hdiutil create -volname "SemioVis" -srcfolder "$STAGING" \
            -ov -format UDZO "$DMG_DIR/$DMG_NAME"

        rm -rf "$STAGING"
        echo "DMG created: $DMG_DIR/$DMG_NAME"
    fi

    echo ""
    echo "=== Release build complete ==="
    echo "App:  $APP_DIR/SemioVis.app"
    echo "DMG:  $DMG_DIR/$DMG_NAME"
else
    cargo build
    echo ""
    echo "=== Dev build complete ==="
    echo "Binary: $ROOT/desktop/src-tauri/target/debug/semiovis-desktop"
fi

echo ""
echo "To run the desktop app in dev mode:"
echo "  1. Start backend: cd backend && KMP_DUPLICATE_LIB_OK=TRUE ../.venv/bin/uvicorn main:app --port 8000"
echo "  2. Run app: cd desktop/src-tauri && cargo run"
