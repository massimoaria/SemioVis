// SemioVis — Tauri v2 entry point

mod sidecar;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
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
