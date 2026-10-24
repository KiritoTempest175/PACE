import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,waitFor,cleanup} from '@testing-library/react';
import App from '../App.jsx';
import {ThemeProvider} from '../ThemeContext.jsx';

vi.mock('../lib/api.js',()=>({
  json:vi.fn().mockResolvedValue([]),
  wakeServer:vi.fn().mockRejectedValue(new Error('Backend unavailable')),
  streamAnswer:vi.fn()
}));
afterEach(()=>{cleanup();window.history.replaceState(null,'','/');});

describe('PACE startup regression',()=>{
  it('renders the dashboard even without a backend and updates the page title',async()=>{
    window.history.replaceState(null,'','/');
    render(<ThemeProvider><App/></ThemeProvider>);
    expect(screen.getByRole('heading',{name:'System overview'})).toBeInTheDocument();
    await waitFor(()=>expect(window.document.title).toBe('Dashboard | PACE'));
  });
  it('opens Docs without crashing on document-title update',async()=>{
    window.history.replaceState(null,'','/docs');
    render(<ThemeProvider><App/></ThemeProvider>);
    expect(screen.getByRole('heading',{name:'PACE documentation'})).toBeInTheDocument();
    await waitFor(()=>expect(window.document.title).toBe('Docs | PACE'));
  });
});
