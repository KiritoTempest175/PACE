/* The desktop app supports the hosted PACE API or a user-operated local server.
   Never put API tokens or private secrets into Vite build-time values. */
export const IS_PACE_DESKTOP = import.meta.env.VITE_PACE_DESKTOP === 'true';
export const DEFAULT_API = 'https://pace-phase2-api.onrender.com';
const SETTING = 'pace.desktop.api.v1';

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
  // Tauri's CSP deliberately allows only PACE hosted and HTTP loopback hosts.
  if (parsed.origin !== DEFAULT_API && !isLocal) {
    throw new Error('This desktop build allows only the official hosted API or loopback servers.');
  }
  return parsed.origin;
}

export function getApiBase() {
  if (!IS_PACE_DESKTOP) return (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
  try {
    const saved = window.localStorage.getItem(SETTING);
    return saved ? validApiOrigin(saved) : DEFAULT_API;
  } catch {
    return DEFAULT_API;
  }
}

export function setDesktopApiBase(raw) {
  if (!IS_PACE_DESKTOP) throw new Error('Desktop-only preference.');
  const value = validApiOrigin(raw);
  window.localStorage.setItem(SETTING, value);
  return value;
}

export function desktopConnectionKind(url = getApiBase()) {
  return url === DEFAULT_API ? 'hosted' : 'local';
}
