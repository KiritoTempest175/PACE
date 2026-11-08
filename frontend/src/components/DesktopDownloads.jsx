import {useEffect,useState} from 'react';
import {Download,MonitorDown} from 'lucide-react';

const RELEASE_API='https://api.github.com/repos/KiritoTempest175/PACE/releases/tags/desktop-v2.0.0';
const PLATFORMS=[
 {name:'Windows',detail:'Windows 10/11 · 64-bit',file:'PACE_2.0.0_x64-setup.exe',action:'Download .exe'},
 {name:'macOS',detail:'Apple Silicon (ARM64) · unsigned',file:'PACE_2.0.0_aarch64.dmg',action:'Download .dmg'},
 {name:'Linux',detail:'Debian / Ubuntu · 64-bit',file:'PACE_2.0.0_amd64.deb',action:'Download .deb'},
 {name:'Linux portable',detail:'AppImage · 64-bit',file:'PACE_2.0.0_amd64.AppImage',action:'Download AppImage'}
];

export default function DesktopDownloads(){
 const [release,setRelease]=useState(null);
 const [error,setError]=useState('');
 const [revision,retry]=useState(0);
 useEffect(()=>{
  const controller=new AbortController();
  setError('');
  fetch(RELEASE_API,{signal:controller.signal,headers:{Accept:'application/vnd.github+json'}})
   .then(async response=>{if(!response.ok)throw new Error('Release not available');return response.json();})
   .then(data=>{if(!controller.signal.aborted)setRelease(data);})
   .catch(()=>{if(!controller.signal.aborted){setRelease(null);setError('The verified desktop installers are not yet available. Please retry shortly.');}});
  return ()=>controller.abort();
 },[revision]);
 const assets=new Map((release?.assets||[]).map(asset=>[asset.name,asset.browser_download_url]));
 return <section className="desktop-downloads" aria-label="Download PACE Desktop">
  <p className="eyebrow">PACE DESKTOP 2.0</p>
  <h3><MonitorDown size={21} aria-hidden="true"/> Install PACE on your computer</h3>
  <p>Use local Ollama models or connect a supported API provider. Choose your operating system to download the installer directly, without visiting a release page.</p>
  {release? <div className="download-grid">{PLATFORMS.filter(item=>assets.has(item.file)).map(item=><div className="download-item" key={item.file}>
    <strong>{item.name}</strong><small>{item.detail}</small><a href={assets.get(item.file)} aria-label={item.action+' for '+item.name}><Download size={16} aria-hidden="true"/> {item.action}</a>
   </div>)}</div>:<p role="status">{error||'Checking verified installers…'}</p>}
  {release&& !PLATFORMS.some(item=>assets.has(item.file))&&<p role="status">The release is being prepared; no supported installer is available yet.</p>}
  {error&&<button type="button" className="button button--secondary" onClick={()=>retry(n=>n+1)}>Retry download check</button>}
  <small className="download-sub">Windows and macOS installers are unsigned. Your operating system may ask you to confirm the publisher. Installation starts after the downloaded file is opened.</small>
 </section>;
}
