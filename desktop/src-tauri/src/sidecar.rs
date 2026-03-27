// Sidecar: spawns the FastAPI backend process on a free port

use std::net::TcpListener;
use std::process::Command;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU16, Ordering};


const DEFAULT_PORT: u16 = 8000;
const PORT_RANGE: u16 = 10; // try 8000..8010

/// The port the backend actually bound to (readable from Tauri commands).
pub static BACKEND_PORT: AtomicU16 = AtomicU16::new(DEFAULT_PORT);

/// Find a free TCP port starting from `DEFAULT_PORT`.
fn find_free_port() -> u16 {
    for port in DEFAULT_PORT..DEFAULT_PORT + PORT_RANGE {
        if TcpListener::bind(("127.0.0.1", port)).is_ok() {
            return port;
        }
    }
    eprintln!("WARNING: no free port found in {}..{}, falling back to {}", DEFAULT_PORT, DEFAULT_PORT + PORT_RANGE, DEFAULT_PORT);
    DEFAULT_PORT
}

fn find_backend_binary() -> Option<PathBuf> {
    let exe_path = std::env::current_exe().ok()?;
    let exe_dir = exe_path.parent()?;

    // Support both onedir layout (semiovis_api/semiovis_api) and onefile (semiovis_api)
    let bin_name = if cfg!(target_os = "windows") { "semiovis_api.exe" } else { "semiovis_api" };

    let candidates: Vec<PathBuf> = if cfg!(target_os = "macos") {
        let resources_dir = exe_dir.parent().map(|p| p.join("Resources"));
        let mut c = Vec::new();
        if let Some(ref res) = resources_dir {
            // Tauri relative resource path: _up_/bin/semiovis_api/semiovis_api
            c.push(res.join("_up_").join("bin").join("semiovis_api").join(bin_name));
            // onedir layout: bin/semiovis_api/semiovis_api
            c.push(res.join("bin").join("semiovis_api").join(bin_name));
            // onefile layout: bin/semiovis_api
            c.push(res.join("bin").join(bin_name));
            c.push(res.join(bin_name));
        }
        c.push(exe_dir.join("bin").join("semiovis_api").join(bin_name));
        c.push(exe_dir.join("bin").join(bin_name));
        c.push(exe_dir.join(bin_name));
        c
    } else if cfg!(target_os = "windows") {
        vec![
            exe_dir.join("bin").join("semiovis_api").join(bin_name),
            exe_dir.join("bin").join(bin_name),
            exe_dir.join(bin_name),
        ]
    } else {
        vec![
            exe_dir.join("bin").join("semiovis_api").join(bin_name),
            exe_dir.join("bin").join(bin_name),
            exe_dir.join(bin_name),
        ]
    };

    for path in &candidates {
        if path.exists() {
            return Some(path.clone());
        }
    }

    eprintln!("WARNING: Backend binary not found. Searched:");
    for path in &candidates {
        eprintln!("  - {:?}", path);
    }
    None
}

/// Spawn the backend in a background thread so it never blocks the Tauri window.
pub fn spawn_backend() {
    // In dev mode, we assume the backend is already running
    if cfg!(debug_assertions) {
        println!("Dev mode: expecting backend at http://localhost:{}", DEFAULT_PORT);
        println!("  Start it with: cd backend && KMP_DUPLICATE_LIB_OK=TRUE ../.venv/bin/uvicorn main:app --port {}", DEFAULT_PORT);
        BACKEND_PORT.store(DEFAULT_PORT, Ordering::SeqCst);
        return;
    }

    // Find the binary and port synchronously (fast), then spawn in background
    let binary = match find_backend_binary() {
        Some(b) => b,
        None => {
            eprintln!("  The app will run but analysis features require the backend.");
            return;
        }
    };

    let port = find_free_port();
    BACKEND_PORT.store(port, Ordering::SeqCst);

    // Spawn the backend process in a background thread so the Tauri
    // window appears immediately while the backend boots up.
    std::thread::spawn(move || {
        println!("Starting backend from: {:?} on port {}", binary, port);

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
    });
}
