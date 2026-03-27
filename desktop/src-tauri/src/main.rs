// SemioVis — Tauri v2 entry point

mod sidecar;

use sidecar::BACKEND_PORT;
use std::sync::atomic::Ordering;

#[tauri::command]
fn get_backend_port() -> u16 {
    BACKEND_PORT.load(Ordering::SeqCst)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![get_backend_port])
        .setup(|_app| {
            sidecar::spawn_backend();
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running SemioVis");
}

fn main() {
    run();
}
