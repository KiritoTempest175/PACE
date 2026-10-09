import { describe, expect, it } from 'vitest';
import { validApiOrigin, DEFAULT_API } from '../lib/desktopApi';

describe('desktop API endpoint restrictions', () => {
  it('allows the official hosted API', () => {
    expect(validApiOrigin(DEFAULT_API)).toBe(DEFAULT_API);
  });
  it('allows local PACE API endpoints', () => {
    expect(validApiOrigin('http://127.0.0.1:8000/')).toBe('http://127.0.0.1:8000');
    expect(validApiOrigin('http://localhost:8000')).toBe('http://localhost:8000');
  });
  it('blocks insecure remote hosts and unapproved origins', () => {
    expect(() => validApiOrigin('http://example.com')).toThrow();
    expect(() => validApiOrigin('https://example.com')).toThrow();
  });
  it('blocks embedded credentials, paths and query strings', () => {
    expect(() => validApiOrigin('https://bob:password@pace-phase2-api.onrender.com')).toThrow();
    expect(() => validApiOrigin(DEFAULT_API + '/admin')).toThrow();
    expect(() => validApiOrigin('http://localhost:8000?secret=x')).toThrow();
  });
});
