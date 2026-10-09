// No arbitrary shell, filesystem, or local-process commands are exposed.
// The React frontend communicates only with the configured PACE HTTP API.
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("failed to initialize PACE Desktop");
}
