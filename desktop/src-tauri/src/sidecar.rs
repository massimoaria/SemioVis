// Sidecar: spawns the FastAPI backend process

use std::process::Command;
use std::path::PathBuf;

const BACKEND_PORT: u16 = 8000;

fn find_backend_binary() -> Option<PathBuf> {
    let exe_path = std::env::current_exe().ok()?;
    let exe_dir = exe_path.parent()?;

    // Candidate paths (in priority order):
    let candidates: Vec<PathBuf> = if cfg!(target_os = "macos") {
        // macOS .app bundle: Resources dir is sibling to MacOS dir
        let resources_dir = exe_dir.parent().map(|p| p.join("Resources"));
        let mut c = Vec::new();
        if let Some(ref res) = resources_dir {
            c.push(res.join("bin").join("semiovis_api"));
            c.push(res.join("semiovis_api"));
        }
        c.push(exe_dir.join("bin").join("semiovis_api"));
        c.push(exe_dir.join("semiovis_api"));
        c
    } else if cfg!(target_os = "windows") {
        vec![
            exe_dir.join("bin").join("semiovis_api.exe"),
            exe_dir.join("semiovis_api.exe"),
        ]
    } else {
        vec![
            exe_dir.join("bin").join("semiovis_api"),
            exe_dir.join("semiovis_api"),
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

pub fn spawn_backend() {
    // In dev mode, we assume the backend is already running
    if cfg!(debug_assertions) {
        println!("Dev mode: expecting backend at http://localhost:{}", BACKEND_PORT);
        println!("  Start it with: cd backend && KMP_DUPLICATE_LIB_OK=TRUE ../.venv/bin/uvicorn main:app --port {}", BACKEND_PORT);
        return;
    }

    let binary = match find_backend_binary() {
        Some(b) => b,
        None => {
            eprintln!("  The app will run but analysis features require the backend.");
            return;
        }
    };

    println!("Starting backend from: {:?}", binary);

    match Command::new(&binary)
        .env("API_PORT", BACKEND_PORT.to_string())
        .env("API_HOST", "127.0.0.1")
        .env("IS_DESKTOP", "true")
        .env("KMP_DUPLICATE_LIB_OK", "TRUE")
        .spawn()
    {
        Ok(child) => {
            println!("Backend sidecar started (PID {}) on port {}", child.id(), BACKEND_PORT);
        }
        Err(e) => {
            eprintln!("Failed to spawn backend sidecar: {}", e);
        }
    }
}
