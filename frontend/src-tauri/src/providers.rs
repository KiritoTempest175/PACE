//! Native BYOK requests. The webview never receives or stores API secrets.
//! Every call is explicit and secrets stay in the OS credential vault.
use serde::Deserialize;
use serde_json::{json, Value};
use std::time::Duration;
use url::Url;

use super::credential_entry;

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProviderRequest {
    pub credential_id: String,
    pub provider: String,
    pub model_id: String,
    pub base_url: String,
    pub prompt: String,
}

fn checked_base(request: &ProviderRequest) -> Result<Url, String> {
    let default = match request.provider.as_str() {
        "openai" => "https://api.openai.com/v1",
        "openrouter" => "https://openrouter.ai/api/v1",
        "anthropic" => "https://api.anthropic.com/v1",
        "google" => "https://generativelanguage.googleapis.com/v1beta",
        "custom" => "",
        _ => return Err("Unsupported provider".into()),
    };
    let base = if request.base_url.trim().is_empty() { default } else { request.base_url.trim() };
    if base.is_empty() { return Err("Enter a provider base URL".into()); }
    let url = Url::parse(base).map_err(|_| "Invalid provider address")?;
    let loopback = matches!(url.host_str(), Some("localhost" | "127.0.0.1" | "::1"));
    if (url.scheme() != "https" && !(loopback && url.scheme() == "http"))
        || !url.username().is_empty() || url.password().is_some()
        || url.query().is_some() || url.fragment().is_some()
    {
        return Err("Use HTTPS (or a local loopback server), without URL credentials".into());
    }
    if request.model_id.is_empty() || request.model_id.len() > 200
        || request.prompt.trim().is_empty() || request.prompt.len() > 1_000_000 {
        return Err("Invalid model name or request text".into());
    }
    Ok(url)
}

#[tauri::command]
pub async fn desktop_provider_request(request: ProviderRequest) -> Result<String, String> {
    let base = checked_base(&request)?;
    let key = credential_entry(&request.credential_id)?
        .get_password().map_err(|_| "The key is not in your operating-system vault".to_string())?;

    let mut target = base;
    {
        let mut path = target.path_segments_mut().map_err(|_| "Unsupported provider URL")?;
        match request.provider.as_str() {
            "anthropic" => { path.push("messages"); }
            "google" => {
                path.push("models");
                path.push(&format!("{}:generateContent", request.model_id));
            }
            _ => { path.push("chat").push("completions"); }
        }
    }
    // No redirects: do not forward an Authorization header to another host.
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(600))
        .redirect(reqwest::redirect::Policy::none())
        .build().map_err(|_| "Could not initialize native HTTPS client")?;
    let req = match request.provider.as_str() {
        "anthropic" => client.post(target)
            .header("x-api-key", key)
            .header("anthropic-version", "2023-06-01")
            .json(&json!({"model":request.model_id,"max_tokens":8192,"messages":[{"role":"user","content":request.prompt}]})),
        "google" => client.post(target)
            .header("x-goog-api-key", key)
            .json(&json!({"contents":[{"parts":[{"text":request.prompt}]}]})),
        _ => client.post(target)
            .bearer_auth(key)
            .json(&json!({"model":request.model_id,"messages":[{"role":"user","content":request.prompt}]})),
    };
    let response = req.send().await.map_err(|_| "Provider connection failed or timed out")?;
    if !response.status().is_success() {
        return Err(format!("Provider returned HTTP {}. Check permissions, billing and model name.", response.status().as_u16()));
    }
    if response.content_length().unwrap_or(0) > 8 * 1024 * 1024 {
        return Err("Provider response is too large to render safely".into());
    }
    let bytes = response.bytes().await.map_err(|_| "Could not read provider response")?;
    if bytes.len() > 8 * 1024 * 1024 { return Err("Provider response exceeds desktop memory safety limit".into()); }
    let data: Value = serde_json::from_slice(&bytes).map_err(|_| "Provider returned invalid JSON")?;
    let text = match request.provider.as_str() {
        "anthropic" => data["content"].as_array().map(|parts| parts.iter()
            .filter_map(|p| p["text"].as_str()).collect::<Vec<_>>().join("\n")),
        "google" => data["candidates"][0]["content"]["parts"].as_array().map(|parts|
            parts.iter().filter_map(|p| p["text"].as_str()).collect::<Vec<_>>().join("\n")),
        _ => data["choices"][0]["message"]["content"].as_str().map(String::from),
    };
    text.filter(|s| !s.trim().is_empty()).ok_or_else(|| "Provider returned no text output".into())
}

#[tauri::command]
pub fn desktop_has_key(model_id: String) -> Result<bool, String> {
    match credential_entry(&model_id)?.get_password() {
        Ok(_) => Ok(true),
        Err(keyring::Error::NoEntry) => Ok(false),
        Err(_) => Err("Cannot access OS credential vault".into()),
    }
}

#[tauri::command]
pub fn desktop_credential_location() -> String {
    if cfg!(target_os = "windows") {
        "Windows Credential Manager > Windows Credentials > Generic Credentials (service: app.pace.workspaces.byok)".into()
    } else if cfg!(target_os = "macos") {
        "macOS Keychain Access (service: app.pace.workspaces.byok)".into()
    } else {
        "Linux Secret Service / desktop keyring (service: app.pace.workspaces.byok)".into()
    }
}
