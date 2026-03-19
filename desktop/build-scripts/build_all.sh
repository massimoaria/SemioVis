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
    cargo build --release
    echo ""
    echo "=== Release build complete ==="
    echo "Binary: $ROOT/desktop/src-tauri/target/release/semiovis-desktop"
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
