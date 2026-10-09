import {afterEach, describe, expect, it, vi} from 'vitest';

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
  localStorage.clear();
  delete window.__TAURI__;
});

describe('packaged desktop sidecar binding', () => {
  it('waits for native startup, uses private loopback and adds launch key', async () => {
    vi.stubEnv('VITE_PACE_DESKTOP', 'true');
    vi.resetModules();
    const key = 'a'.repeat(64);
    const invoke = vi.fn().mockResolvedValue({endpoint: 'http://127.0.0.1:52341', key});
    window.__TAURI__ = {core: {invoke}};
    const api = await import('../lib/desktopApi.js');
    expect(api.IS_PACE_DESKTOP).toBe(true);
    expect(() => api.getApiBase()).toThrow('starting');
    await api.initDesktopRuntime();
    expect(invoke).toHaveBeenCalledWith('desktop_backend_info');
    expect(api.getApiBase()).toBe('http://127.0.0.1:52341');
    expect(api.desktopApiHeaders()).toEqual({'X-PACE-Desktop-Key': key});
    expect(api.desktopSessionScope()).toBe('local');
    expect(api.setDesktopApiBase('hosted')).toBe(api.DEFAULT_API);
    expect(api.desktopApiHeaders()).toEqual({});
    expect(api.desktopSessionScope()).toBe('hosted');
    expect(api.setDesktopApiBase('local')).toBe('http://127.0.0.1:52341');
  });

  it('rejects malformed native endpoint or token', async () => {
    vi.stubEnv('VITE_PACE_DESKTOP', 'true');
    vi.resetModules();
    window.__TAURI__ = {core: {invoke: vi.fn().mockResolvedValue({
      endpoint: 'http://attacker.example:8090', key: 'x'
    })}};
    const api = await import('../lib/desktopApi.js');
    await expect(api.initDesktopRuntime()).rejects.toThrow('valid connection');
  });
});
