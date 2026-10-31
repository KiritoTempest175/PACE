//! Desktop process supervisor for the packaged Python FastAPI sidecar.
//! Local API is loopback-only and authenticated by an ephemeral capability.
use serde::Serialize;
use std::{net::TcpListener, sync::Mutex};
use tauri::{Manager, State, WindowEvent};
use tauri_plugin_shell::{process::CommandChild, ShellExt};
use uuid::Uuid;
mod providers;

struct BackendState {
    endpoint: String,
    key: String,
    process: Mutex<Option<CommandChild>>,
}

#[derive(Serialize)]
struct BackendInfo {
    endpoint: String,
    key: String,
}

#[tauri::command]
fn desktop_backend_info(state: State<'_, BackendState>) -> BackendInfo {
    BackendInfo {
        endpoint: state.endpoint.clone(),
        key: state.key.clone(),
    }
}


pub(super) fn credential_entry(id: &str) -> Result<keyring::Entry, String> {
    if id.is_empty() || id.len() > 128 || !id.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'-' || c == b'_') {
        return Err("Invalid credential identifier".into());
    }
    keyring::Entry::new("app.pace.workspaces.byok", id)
        .map_err(|_| "OS keychain is unavailable".to_string())
}

#[tauri::command]
fn desktop_store_key(model_id: String, secret: String) -> Result<(), String> {
    if secret.is_empty() || secret.len() > 8192 {
        return Err("Invalid API key length".into());
    }
    credential_entry(&model_id)?.set_password(&secret)
        .map_err(|_| "Could not save API key to OS keychain".to_string())
}

#[tauri::command]
fn desktop_delete_key(model_id: String) -> Result<(), String> {
    match credential_entry(&model_id)?.delete_credential() {
        Ok(()) | Err(keyring::Error::NoEntry) => Ok(()),
        Err(_) => Err("Could not delete keychain entry".into()),
    }
}

#[tauri::command]
fn desktop_data_location(app: tauri::AppHandle) -> Result<String, String> {
    app.path().app_local_data_dir()
        .map(|path| path.display().to_string())
        .map_err(|_| "Could not find desktop data directory".to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![desktop_backend_info, desktop_store_key, desktop_delete_key, desktop_data_location, providers::desktop_provider_request, providers::desktop_has_key, providers::desktop_credential_location])
        .setup(|app| {
            let app_data = app.path().app_local_data_dir()?;
            std::fs::create_dir_all(&app_data)?;
            let listener = TcpListener::bind("127.0.0.1:0")?;
            let port = listener.local_addr()?.port();
            drop(listener);
            let key = format!(
                "{}{}",
                Uuid::new_v4().simple(),
                Uuid::new_v4().simple()
            );
            let sidecar = app
                .shell()
                .sidecar("pace-api")?
                .env("PACE_DESKTOP_PORT", port.to_string())
                .env("PACE_DESKTOP_KEY", key.clone())
                .env("PACE_DESKTOP_DATA_DIR", app_data.to_string_lossy().to_string());
            let (mut events, process) = sidecar.spawn()?;
            tauri::async_runtime::spawn(async move {
                while events.recv().await.is_some() {
                    // Drain output events to prevent a blocked sidecar.
                }
            });
            app.manage(BackendState {
                endpoint: format!("http://127.0.0.1:{port}"),
                key,
                process: Mutex::new(Some(process)),
            });
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::Destroyed = event {
                if window.label() == "main" {
                    let state = window.state::<BackendState>();
                    if let Ok(mut guard) = state.process.lock() {
                        if let Some(child) = guard.take() {
                            // PyInstaller onefile uses an extraction parent.
                            // Kill the full Windows process tree so no local
                            // server survives app shutdown or holds SQLite open.
                            #[cfg(target_os = "windows")]
                            {
                                let pid = child.pid().to_string();
                                let status = std::process::Command::new("taskkill")
                                    .args(["/F", "/T", "/PID", &pid])
                                    .status();
                                if status.is_err() {
                                    let _ = child.kill();
                                }
                            }
                            #[cfg(not(target_os = "windows"))]
                            {
                                let _ = child.kill();
                            }
                        }
                    };
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("failed to start PACE desktop");
}
