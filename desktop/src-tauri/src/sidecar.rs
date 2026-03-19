// Sidecar: spawns the FastAPI backend process

use std::process::Command;
use std::net::TcpListener;

fn find_free_port() -> u16 {
    TcpListener::bind("127.0.0.1:0")
        .expect("Failed to bind to find free port")
        .local_addr()
        .expect("Failed to get local address")
        .port()
}

pub fn spawn_backend() {
    let port = find_free_port();

    // In dev mode, we assume the backend is already running
    if cfg!(debug_assertions) {
        println!("Dev mode: expecting backend at http://localhost:8000");
        println!("  Start it with: cd backend && KMP_DUPLICATE_LIB_OK=TRUE ../.venv/bin/uvicorn main:app --port 8000");
        return;
    }

    // In production, spawn the PyInstaller-bundled backend binary
    let exe_dir = std::env::current_exe()
        .expect("Failed to get current exe path")
        .parent()
        .expect("Failed to get exe parent dir")
        .to_path_buf();

    let binary = if cfg!(target_os = "windows") {
        exe_dir.join("bin").join("semiovis_api.exe")
    } else {
        exe_dir.join("bin").join("semiovis_api")
    };

    if !binary.exists() {
        eprintln!("WARNING: Backend binary not found at {:?}", binary);
        eprintln!("  The app will run but analysis features require the backend.");
        return;
    }

    match Command::new(&binary)
        .env("API_PORT", port.to_string())
        .env("API_HOST", "127.0.0.1")
        .env("IS_DESKTOP", "true")
        .env("KMP_DUPLICATE_LIB_OK", "TRUE")
        .spawn()
    {
        Ok(child) => {
            println!("Backend sidecar started (PID {}) on port {}", child.id(), port);
        }
        Err(e) => {
            eprintln!("Failed to spawn backend sidecar: {}", e);
        }
    }
}
