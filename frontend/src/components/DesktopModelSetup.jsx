import {useCallback,useEffect,useState} from 'react';
import {api,json} from '../lib/api.js';
import {Button,Modal,Badge} from './ui.jsx';
import {useTheme} from '../ThemeContext.jsx';

const DEFAULT_ACTOR='qwen2.5-coder:1.5b';
const DEFAULT_CRITIC='qwen2.5-coder:3b';

export async function readSetupStream(path,body,onProgress){
  const response=await api(path,{method:'POST',body});
  const reader=response.body?.getReader();
  if(!reader)throw new Error('Desktop backend does not support streamed downloads');
  const decoder=new TextDecoder();let pending='';let complete=false;
  try{
    while(true){
      const {value,done}=await reader.read();if(done)break;
      pending+=decoder.decode(value,{stream:true}).replaceAll('\r\n','\n');
      const frames=pending.split('\n\n');pending=frames.pop()||'';
      for(const frame of frames){
        const line=frame.split('\n').find(x=>x.startsWith('data: '));
        if(!line)continue;
        let event;try{event=JSON.parse(line.slice(6));}catch{throw new Error('Malformed setup progress response');}
        if(event.type==='error')throw new Error(event.message||'Setup failed');
        onProgress(event);
        if(['done','installer_opened','already_installed'].includes(event.type))complete=true;
      }
    }
    if(!complete)throw new Error('Setup stopped unexpectedly. Retry to resume the download.');
  }finally{reader.releaseLock();}
}

function fmt(bytes){return bytes?(bytes/1048576).toFixed(0)+' MB':'';}

export function DesktopModelSetup({open,onClose,onChanged,onOpenProviders,firstRun=false}){
  const theme=useTheme();
  const [importChoice,setImportChoice]=useState('actor');
  const [status,setStatus]=useState(null);
  const [actor,setActor]=useState(DEFAULT_ACTOR);
  const [critic,setCritic]=useState(DEFAULT_CRITIC);
  const [task,setTask]=useState('');
  const [progress,setProgress]=useState(null);
  const [error,setError]=useState('');
  const [info,setInfo]=useState('');
  const [discovered,setDiscovered]=useState([]);
  const [scanning,setScanning]=useState(false);
  const reload=useCallback(async()=>{
    const next=await json('/desktop/setup/status');
    setStatus(next);
    if(next.selected.actor)setActor(next.selected.actor);
    if(next.selected.critic)setCritic(next.selected.critic);
    onChanged?.(next);
    return next;
  },[onChanged]);
  useEffect(()=>{if(!open)return;let alive=true;json('/desktop/setup/status').then(s=>{
    if(!alive)return;setStatus(s);if(s.selected.actor)setActor(s.selected.actor);if(s.selected.critic)setCritic(s.selected.critic);
  }).catch(e=>alive&&setError(e.message));return()=>{alive=false;};},[open]);
  async function execute(name,fn){
    if(task)return;setTask(name);setError('');setInfo('');setProgress(null);
    try{await fn();await reload();}catch(e){setError(e.message||'Setup failed');}finally{setTask('');}
  }
  const percentage=progress?.total?Math.min(100,Math.floor((progress.completed||0)/progress.total*100)):null;
  const install=()=>execute('install',async()=>{
    await readSetupStream('/desktop/setup/install',{},event=>{
      setProgress(event);
      if(event.type==='installer_opened')setInfo('Finish the official Ollama installation window, then click Refresh status.');
    });
  });
  const start=()=>execute('start',async()=>{
    await json('/desktop/setup/start',{method:'POST',body:{}});
    setInfo('Starting Ollama. It may take a few seconds; click Refresh status.');
  });
  const pull=(role,model)=>execute(role,async()=>{
    await readSetupStream('/desktop/setup/pull',{role,model},setProgress);
    setInfo(model+' downloaded and selected as '+(role==='actor'?'Generator.':'Reviewer.'));
  });
  const select=(role,model)=>execute(role,async()=>{
    await json('/desktop/setup/select',{method:'POST',body:{role,model}});
    setInfo(model+' selected as '+(role==='actor'?'Generator.':'Reviewer.'));
  });
  const importGGUF=file=>execute('import',async()=>{
    await readSetupStream('/desktop/setup/import',{role:importChoice,path:file.path},setProgress);
    setInfo(file.name+' imported into your local Ollama library. The original file remains on your computer.');
  });
  const scan=async()=>{setScanning(true);setError('');try{const result=await json('/desktop/setup/scan');setDiscovered(result.models||[]);setInfo('Local file scan completed. Direct file inference is not verified.');}catch(e){setError(e.message);}finally{setScanning(false);}};
  const models=status?.catalog||[];
  const installed=new Set(status?.installed_models||[]);
  const loaded=status?.running;
  function picker(role,value,setValue){return <div className="model-role" key={role}>
    <div className="model-role-header"><strong>{role==='actor'?'Generator / Actor':'Reviewer / Critic'}</strong><Badge tone={status?.selected?.[role]&&installed.has(status.selected[role])?'success':'neutral'}>{status?.selected?.[role]||'Not configured'}</Badge></div>
    <p className="small muted">{role==='actor'?'Creates the first answer in Fast and Pro mode.':'Reviews the draft in Pro mode. This is model-based review, not formal verification.'}</p>
    <label className="field"><span>Choose a model (download size is approximate)</span>
      <select value={value} onChange={e=>setValue(e.target.value)} disabled={Boolean(task)}>
        {models.map(m=><option value={m.id} key={m.id}>{m.id} · {m.size} · ~{m.gb} GB · {m.use}</option>)}
      </select></label>
    <div className="setup-action-row">
      <Button disabled={Boolean(task)||!loaded} onClick={()=>installed.has(value)?select(role,value):pull(role,value)}>{installed.has(value)?'Use installed model':'Download & select model'}</Button>
      <span className="small muted">{installed.has(value)?'Already downloaded':'Downloads inside PACE (internet required)'}</span>
    </div>
  </div>;}
  return <Modal title={firstRun?'Welcome to PACE Desktop':'Local AI & model setup'} open={open} onClose={onClose}>
    <div className="model-setup desktop-onboarding" aria-live="polite">
      <div className="desktop-welcome-banner"><img src="/pace-monogram.svg" width="68" height="68" alt="PACE logo"/><div><p className="eyebrow">PACE / PERSONAL AI WORKSPACE</p><h3>{firstRun?'Set up your experience':'Your model workspace'}</h3><p>Private local intelligence, or your choice of external AI provider.</p></div></div>
      {firstRun&&<section className="onboarding-personalize"><h3>1. Choose your appearance</h3><p className="small muted">You can change this at any time in Preferences.</p><div className="setup-appearance">{['dark','light','system'].map(option=><button key={option} className={theme.preference===option?'selected':''} onClick={()=>theme.setPreference(option)} type="button">{option==='system'?'Follow device':option==='dark'?'Dark':'Light'}</button>)}</div></section>}
      <div className="model-setup-divider"/>
      <h3>2. Choose how PACE thinks</h3>
      <p className="small muted">Local models run on this computer. You can also add a hosted AI account in Models; credentials stay in your OS keychain.</p>
      <div className="setup-action-row"><Button variant="secondary" onClick={onOpenProviders} disabled={Boolean(task)}>Configure external AI provider</Button><Badge tone="success">Local by default</Badge></div>
      <p className="small muted">Your desktop app already includes FastAPI, PDF processing and SQLite. Select free-to-download Ollama models for local AI. You can change your choices later in Preferences.</p>
      <div className="model-role-header"><strong>Ollama service</strong><Badge tone={loaded?'success':'warning'}>{loaded?'Running':status?.installed?'Installed · not running':'Not installed'}</Badge></div>
      {!loaded&&<div className="setup-action-row">
        {!status?.installed?<Button disabled={Boolean(task)} onClick={install}>Download & install Ollama</Button>:<Button disabled={Boolean(task)} onClick={start}>Start Ollama</Button>}
        <Button variant="secondary" disabled={Boolean(task)} onClick={()=>execute('refresh',reload)}>Refresh status</Button>
      </div>}
      {loaded&&<Button variant="secondary" size="sm" disabled={Boolean(task)} onClick={()=>execute('refresh',reload)}>Refresh installed models</Button>}
      {loaded&&<><div className="model-setup-divider"/>{picker('actor',actor,setActor)}<div className="model-setup-divider"/>{picker('critic',critic,setCritic)}</>}
      <div className="model-setup-divider"/><section><h3>3. Use models already on your PC</h3><p className="small muted">Read-only scan of Ollama, LM Studio, Hugging Face and familiar model folders. PACE never uploads these files. Compatible GGUF models can be imported into Ollama after your confirmation; other formats are shown for reference.</p><div className="setup-action-row"><Button size="sm" variant="secondary" disabled={scanning||Boolean(task)} onClick={scan}>{scanning?'Scanning local folders…':'Scan this PC for models'}</Button><label className="field model-import-role"><span>Import as</span><select value={importChoice} onChange={e=>setImportChoice(e.target.value)}><option value="actor">Generator</option><option value="critic">Reviewer</option></select></label></div>{discovered.length===0&&<p className="small muted">Select Scan to find compatible downloaded models.</p>}{discovered.slice(0,50).map(m=><div className="discovered-model" key={m.path}><div><strong>{m.name}</strong><p className="small muted">{m.format.toUpperCase()} · {m.size_gb} GB · {m.quantization}</p><small title={m.path}>{m.path}</small></div><Button size="sm" variant="secondary" disabled={!loaded||Boolean(task)||m.format!=='gguf'} onClick={()=>importGGUF(m)}>{m.format==='gguf'?'Import into Ollama':'Reference only'}</Button></div>)}</section>
      {loaded&&actor===critic&&<p className="small muted">Two different models give an independent model-based second pass. The same model can be selected for both roles, but does not provide independent review.</p>}
      {task&&<div role="status"><p className="small">{task==='install'?'Downloading official Ollama setup':task==='start'?'Starting Ollama':task==='refresh'?'Checking Ollama':task==='import'?'Importing your model locally':'Downloading or selecting model'} — {progress?.status||'please wait'}</p>{percentage!==null&&<progress max="100" value={percentage}>{percentage}%</progress>}{progress?.completed>0&&<span className="small muted"> {fmt(progress.completed)} {progress.total?'of '+fmt(progress.total):''}</span>}</div>}
      {info&&<p className="setup-info" role="status">{info}</p>}{error&&<p className="inline-error" role="alert">{error}</p>}
      <div className="setup-action-row"><Button variant="secondary" onClick={onClose} disabled={Boolean(task)}>{firstRun?'Finish setup':'Close setup'}</Button>{status?.actor_ready&&<Badge tone="success">Fast ready</Badge>}{status?.critic_ready&&<Badge tone="success">Pro reviewer ready</Badge>}</div>
      <p className="small muted">Ollama downloads are free to access but have separate model licenses. Larger models need more disk space and memory. Installation may require approving the official Windows installer. No model weights are installed without your choice.</p>
    </div>
  </Modal>;
}
