import {afterEach,describe,it,expect,vi} from 'vitest';
import {render,screen,waitFor,cleanup} from '@testing-library/react';
import DesktopDownloads from '../components/DesktopDownloads.jsx';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});

describe('desktop installer download links',()=>{
 it('uses actual release assets and does not navigate to a GitHub release page',async()=>{
  const fetcher=vi.fn().mockResolvedValue({ok:true,json:async()=>({assets:[
   {name:'PACE_2.0.0_x64-setup.exe',browser_download_url:'https://github.com/KiritoTempest175/PACE/releases/download/desktop-v2.0.0/PACE_2.0.0_x64-setup.exe'}
  ]})});
  vi.stubGlobal('fetch',fetcher);
  render(<DesktopDownloads/>);
  const link=await screen.findByRole('link',{name:'Download .exe for Windows'});
  expect(link.getAttribute('href')).toContain('/releases/download/desktop-v2.0.0/');
  expect(screen.queryByRole('link',{name:/macOS/})).not.toBeInTheDocument();
 });
 it('does not show broken download links if the release does not exist',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false}));
  render(<DesktopDownloads/>);
  await waitFor(()=>expect(screen.getByRole('status')).toHaveTextContent('not yet available'));
  expect(screen.queryByRole('link',{name:/Download .exe/})).not.toBeInTheDocument();
 });
});
