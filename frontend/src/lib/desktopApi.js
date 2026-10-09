/* Desktop local service is auto-started by the Tauri Rust host.
   Connection secret stays in memory; do not persist it in localStorage. */
export const IS_PACE_DESKTOP = import.meta.env.VITE_PACE_DESKTOP === 'true';
export const DEFAULT_API = 'https://pace-phase2-api.onrender.com';
const SETTING = 'pace.desktop.mode.v2';
const LEGACY_SETTING = 'pace.desktop.api.v1';
let runtime = null;

export function validApiOrigin(raw) {
  if (typeof raw !== 'string') throw new Error('API URL must be text.');
  let parsed;
  try { parsed = new URL(raw.trim()); } catch { throw new Error('Enter a valid API URL.'); }
  if (parsed.username || parsed.password || parsed.search || parsed.hash ||
      (parsed.pathname !== '/' && parsed.pathname !== '')) {
    throw new Error('Use an API origin only (no path, query, username, or password).');
  }
  const isLocal = parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1';
  if (parsed.protocol !== 'https:' && !(parsed.protocol === 'http:' && isLocal)) {
    throw new Error('Use HTTPS for remote APIs; HTTP is allowed only on localhost.');
  }
  if (parsed.origin !== DEFAULT_API && !isLocal) {
    throw new Error('This desktop build allows only the official hosted API or loopback servers.');
  }
  return parsed.origin;
}

function chosenMode() {
  if (!IS_PACE_DESKTOP) return 'hosted';
  const saved = window.localStorage.getItem(SETTING);
  if (saved === 'hosted' || saved === 'local') return saved;
  const legacy = window.localStorage.getItem(LEGACY_SETTING);
  return legacy === DEFAULT_API ? 'hosted' : 'local';
}

export async function initDesktopRuntime() {
  if (!IS_PACE_DESKTOP) return;
  if (runtime) return;
  const invoke = window.__TAURI__?.core?.invoke;
  if (typeof invoke !== 'function') {
    throw new Error('Tauri desktop host is unavailable. This is not a desktop build.');
  }
  const result = await invoke('desktop_backend_info');
  if (!result || typeof result.endpoint !== 'string' ||
      !/^http:\/\/127\.0\.0\.1:\d+$/.test(result.endpoint) ||
      !/^[a-f0-9]{64}$/.test(result.key || '')) {
    throw new Error('Bundled local backend did not supply a valid connection.');
  }
  runtime = {endpoint: result.endpoint, key: result.key};
}

export function getApiBase() {
  if (!IS_PACE_DESKTOP) return (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
  if (chosenMode() === 'hosted') return DEFAULT_API;
  if (!runtime) throw new Error('Bundled local backend is starting');
  return runtime.endpoint;
}

export function desktopApiHeaders() {
  if (!IS_PACE_DESKTOP || chosenMode() === 'hosted') return {};
  if (!runtime) throw new Error('Local backend is starting');
  return {'X-PACE-Desktop-Key': runtime.key};
}

export function setDesktopApiBase(choice) {
  if (!IS_PACE_DESKTOP) throw new Error('Desktop-only preference.');
  let mode;
  if (choice === 'hosted' || choice === DEFAULT_API) mode = 'hosted';
  else if (choice === 'local' || (runtime && choice === runtime.endpoint)) mode = 'local';
  else throw new Error('Select the bundled Local API or the official Hosted API.');
  window.localStorage.setItem(SETTING, mode);
  return getApiBase();
}

export function desktopConnectionKind() {
  return chosenMode();
}

export function desktopSessionScope() {
  return IS_PACE_DESKTOP ? chosenMode() : 'web';
}
