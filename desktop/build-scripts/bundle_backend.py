#!/usr/bin/env python3
"""Bundle the FastAPI backend into a standalone binary with PyInstaller.

Usage:
    python bundle_backend.py

Output:
    desktop/src-tauri/bin/semiovis_api  (single executable)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
BACKEND = ROOT / "backend"
CPP_BUILD = BACKEND / "cpp" / "build"
MODELS_DIR = BACKEND / "models"
OUTPUT_DIR = ROOT / "desktop" / "src-tauri" / "bin"


def find_so_files():
    """Find the compiled C++ shared library."""
    so_files = list(CPP_BUILD.glob("semiovis_core*.so")) + list(CPP_BUILD.glob("semiovis_core*.pyd"))
    if not so_files:
        print("ERROR: No semiovis_core shared library found in", CPP_BUILD)
        print("  Run: cd backend/cpp && cmake -B build && cmake --build build")
        sys.exit(1)
    return so_files


def find_model_files():
    """Find downloaded model weight files."""
    patterns = ["*.pt", "*.onnx"]
    files = []
    for pat in patterns:
        files.extend(MODELS_DIR.glob(pat))
    return files


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    so_files = find_so_files()
    model_files = find_model_files()

    # Build add-binary args for C++ lib
    add_binaries = []
    for so in so_files:
        add_binaries.extend(["--add-binary", f"{so}:."])

    # Build add-data args for model files
    add_data = []
    for mf in model_files:
        add_data.extend(["--add-data", f"{mf}:models/"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(BACKEND / "main.py"),
        "--name", "semiovis_api",
        "--onefile",
        "--noconfirm",
        "--hidden-import", "semiovis_core",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        *add_binaries,
        *add_data,
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(ROOT / "desktop" / "build-scripts" / "build"),
        "--specpath", str(ROOT / "desktop" / "build-scripts"),
    ]

    print("Running PyInstaller...")
    print(" ".join(cmd[:10]), "...")
    result = subprocess.run(cmd, cwd=str(BACKEND))

    if result.returncode != 0:
        print("PyInstaller failed!")
        sys.exit(1)

    output_binary = OUTPUT_DIR / "semiovis_api"
    if not output_binary.exists():
        output_binary = OUTPUT_DIR / "semiovis_api.exe"

    if output_binary.exists():
        size_mb = output_binary.stat().st_size / (1024 * 1024)
        print(f"\nSuccess! Binary: {output_binary} ({size_mb:.1f} MB)")
    else:
        print("WARNING: Binary not found at expected location")


if __name__ == "__main__":
    main()
