import {useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {Activity,ArrowUp,BookOpen,Code2,FileText,FlaskConical,Menu,Plus,Settings,Upload,Trash2,X,WifiOff,LoaderCircle,TerminalSquare,Play} from 'lucide-react';
import {Badge,Button,Card,Input,Modal,Skeleton,Tabs,Toast,Tooltip} from './components/ui.jsx';
import {useTheme} from './ThemeContext.jsx';
import {json,wakeServer,streamAnswer} from './lib/api.js';
import {IS_PACE_DESKTOP, getApiBase, initDesktopRuntime, setDesktopApiBase, desktopConnectionKind} from './lib/desktopApi.js';

const WORKSPACES=[{id:'coding',label:'Coding',Icon:Code2,description:'Implementation and code explanations'},{id:'literacy',label:'Literacy',Icon:BookOpen,description:'Ask questions about an uploaded PDF'},{id:'research',label:'Research',Icon:FlaskConical,description:'Exploration without verified external citations'}];

function App(){
 const [workspace,setWorkspace]=useState('coding');
 const [online,setOnline]=useState('checking');
 const [provider,setProvider]=useState('disabled');
 const [conversations,setConversations]=useState([]);
 const [activeId,setActiveId]=useState(null);
 const [messages,setMessages]=useState([]);
 const [text,setText]=useState('');
 const [busy,setBusy]=useState(false);
 const [loadingHistory,setLoadingHistory]=useState(false);
 const [telemetryOpen,setTelemetryOpen]=useState(false);
 const [telemetry,setTelemetry]=useState(null);
 const [settingsOpen,setSettingsOpen]=useState(false);
 const [desktopEndpoint,setDesktopEndpoint]=useState(()=>IS_PACE_DESKTOP?'local':'');
 const [sidebarOpen,setSidebarOpen]=useState(false);
 const [notice,setNotice]=useState('');
 const [document,setDocument]=useState(null);
 const [uploading,setUploading]=useState(false);
 const [speed,setSpeed]=useState('fast');
 const [error,setError]=useState('');
 const [boot,setBoot]=useState(0);
 const [sandboxAvailable,setSandboxAvailable]=useState(false);
 const [code,setCode]=useState('print(42)');
 const [runningCode,setRunningCode]=useState(false);
 const [codeResult,setCodeResult]=useState(null);
 const inputRef=useRef(null);
 const scrollRef=useRef(null);
 const fileRef=useRef(null);
 const abortRef=useRef(null);
 const theme=useTheme();
 const statusLabel=online==='online'?'API online':online==='waking'?'Waking up API':online==='checking'?'Connecting':'API unavailable';
 const refreshList=useCallback(async()=>{try{setConversations(await json('/conversations'));}catch(e){setNotice(`Could not load chats: ${e.message}`);}},[]);
 useEffect(()=>{let cancelled=false;setOnline('checking');const connect=async()=>{try{await initDesktopRuntime();if(cancelled)return;if(IS_PACE_DESKTOP)setDesktopEndpoint(getApiBase());const data=await wakeServer(()=>!cancelled&&setOnline('waking'));if(cancelled)return;setOnline('online');setProvider(data.ai_provider||'disabled');setSandboxAvailable(Boolean(data.sandbox_available));await refreshList();}catch(e){if(!cancelled){setOnline('offline');setError(e.message||'Local backend could not start');}}};void connect();return()=>{cancelled=true;};},[boot,refreshList]);
 useEffect(()=>{if(online!=='online'||!telemetryOpen)return;let live=true;const refresh=()=>json('/telemetry').then(v=>live&&setTelemetry(v)).catch(()=>live&&setTelemetry(null));refresh();const timer=setInterval(refresh,12000);return()=>{live=false;clearInterval(timer);};},[telemetryOpen,online]);
 useEffect(()=>{scrollRef.current?.scrollIntoView({behavior:'smooth'});},[messages]);
 const openConversation=async item=>{if(busy)return;setLoadingHistory(true);setActiveId(item.id);setWorkspace(item.workspace);setSidebarOpen(false);try{const res=await json(`/conversations/${encodeURIComponent(item.id)}`);setMessages(res.messages||[]);setDocument(res.document_id?{document_id:res.document_id,displayName:'Saved PDF context'}:null);}catch(e){setError(e.message);}finally{setLoadingHistory(false);}};
 const newChat=()=>{if(busy)return;setActiveId(null);setMessages([]);setDocument(null);setError('');setSidebarOpen(false);inputRef.current?.focus();};
 const send=async e=>{e?.preventDefault?.();if(busy||!text.trim())return;if(workspace==='literacy'&&!document){setError('Upload a PDF to begin literacy mode.');return;}const value=text.trim();setText('');setError('');setBusy(true);const user={role:'user',text:value,id:`local-${Date.now()}`};const assistantId=`reply-${Date.now()}`;setMessages(prev=>[...prev,user,{id:assistantId,role:'assistant',text:''}]);const controller=new AbortController();abortRef.current=controller;try{
   await streamAnswer({text:value,mode:workspace,speed_mode:speed,conversation_id:activeId,document_id:document?.document_id},evt=>{
     if(evt.type==='init')setActiveId(evt.conversation_id);
     if(evt.type==='token')setMessages(prev=>prev.map(m=>m.id===assistantId?{...m,text:m.text+(evt.content||'')}:m));
     
   },controller.signal);
   await refreshList();
  }catch(err){setMessages(prev=>prev.filter(m=>m.id!==assistantId));setError(err.status===503?'AI is unavailable or its free quota was reached. Retry later.':err.message||'Generation failed');if(err.status===503)setProvider('unavailable');}finally{setBusy(false);abortRef.current=null;}
 };
 const uploadPdf=async file=>{if(!file)return;if(!file.name.toLowerCase().endsWith('.pdf')||file.size>8*1024*1024){setError('Select a PDF smaller than 8 MB.');return;}setUploading(true);setError('');try{const data=new FormData();data.append('file',file);const outcome=await json('/upload',{method:'POST',body:data});setDocument({...outcome,displayName:file.name});setNotice('Document processed. You can now ask questions about it.');}catch(e){setError(e.message);}finally{setUploading(false);if(fileRef.current)fileRef.current.value='';}};
 const removeChat=async item=>{if(!window.confirm('Delete this conversation?'))return;try{await json(`/conversations/${encodeURIComponent(item.id)}`,{method:'DELETE'});if(item.id===activeId)newChat();await refreshList();}catch(e){setError(e.message);}};
 const saveDesktopEndpoint=()=>{if(busy){setError('Wait for the current response before changing endpoints.');return;}try{const next=setDesktopApiBase(desktopEndpoint);setDesktopEndpoint(next);setConversations([]);setActiveId(null);setMessages([]);setDocument(null);setProvider('disabled');setOnline('checking');setSettingsOpen(false);setNotice('Connecting to '+next);setBoot(v=>v+1);}catch(e){setError(e.message);}};
 const activeWorkspace=WORKSPACES.find(w=>w.id===workspace);
 return <div className="app-shell">
  <a href="#main" className="skip-link">Skip to workspace</a>
  {sidebarOpen&&<button className="mobile-backdrop" aria-label="Close navigation" onClick={()=>setSidebarOpen(false)}/>}
  <aside className={`sidebar ${sidebarOpen?'open':''}`} aria-label="Main navigation">
   <div className="brand"><div className="brand-mark" aria-hidden="true">P</div><div><strong>PACE</strong><small>AI workspaces</small></div></div>
   <Button variant="secondary" className="new-chat" onClick={newChat}><Plus size={17}/> New conversation</Button>
   <p className="section-caption">WORKSPACES</p><nav aria-label="Workspaces" className="workspace-nav">{WORKSPACES.map(({id,label,Icon})=><button key={id} className={workspace===id?'selected':''} aria-current={workspace===id?'page':undefined} onClick={()=>{setWorkspace(id);newChat();}}><Icon size={18}/>{label}</button>)}</nav>
   <div className="sidebar-history"><p className="section-caption">RECENT CONVERSATIONS</p>{conversations.length===0?<p className="muted small">Your recent conversations appear here.</p>:conversations.slice(0,25).map(item=><div className="history-row" key={item.id}><button className={activeId===item.id?'active':''} onClick={()=>openConversation(item)} title={item.title}>{item.title}</button><Tooltip text="Delete conversation"><button className="icon-action" aria-label={`Delete ${item.title}`} onClick={()=>removeChat(item)}><Trash2 size={14}/></button></Tooltip></div>)}</div>
   <div className="sidebar-footer"><Button variant="ghost" onClick={()=>setSettingsOpen(true)}><Settings size={17}/> Preferences</Button><p className="small muted">Privacy-aware session storage</p></div>
  </aside>
  <main id="main" className="main-panel">
   <header className="topbar"><div className="topbar-left"><Button size="sm" variant="ghost" className="mobile-menu" aria-label="Open navigation" onClick={()=>setSidebarOpen(true)}><Menu size={20}/></Button><div><p className="eyebrow">WORKSPACE</p><h1>{activeWorkspace.label}</h1></div></div><div className="topbar-actions"><Badge tone={online==='online'?'success':online==='waking'?'warning':'neutral'}>{online==='waking'&&<LoaderCircle size={12} className="spin"/>}{statusLabel}</Badge><Tooltip text="System telemetry"><Button variant="ghost" size="sm" aria-label="Toggle telemetry" aria-expanded={telemetryOpen} onClick={()=>setTelemetryOpen(x=>!x)}><Activity size={18}/></Button></Tooltip><Tooltip text="Settings"><Button variant="ghost" size="sm" aria-label="Settings" onClick={()=>setSettingsOpen(true)}><Settings size={18}/></Button></Tooltip></div></header>
   {telemetryOpen&&<Card className="telemetry"><div className="telemetry-head"><h2>System telemetry</h2><Badge>Measured on API host</Badge></div>{!telemetry?<p className="muted">Live telemetry is not currently available.</p>:<dl><div><dt>CPU usage</dt><dd>{telemetry.cpu_utilization??'—'}%</dd></div><div><dt>Memory</dt><dd>{telemetry.ram_usage_mb??'—'} MB</dd></div><div><dt>Device</dt><dd>{telemetry.device??'Unknown'}</dd></div><div><dt>Status</dt><dd>{telemetry.status??'Unknown'}</dd></div></dl>}</Card>}
   {workspace==='coding'&&<div className="coding-tools"><details><summary><TerminalSquare size={16}/> Isolated Python runner <Badge tone={sandboxAvailable?'success':'neutral'}>{sandboxAvailable?'Local Docker enabled':'Hosted execution disabled'}</Badge></summary>
     <label className="field" htmlFor="sandbox-code"><span>Python source (local sandbox only)</span><textarea id="sandbox-code" spellCheck="false" value={code} maxLength={20000} onChange={e=>setCode(e.target.value)} rows={5} placeholder="Write a short Python exercise"/></label>
     <div className="runner-actions"><Button size="sm" disabled={!sandboxAvailable||runningCode||!code.trim()} onClick={async()=>{setRunningCode(true);setCodeResult(null);try{setCodeResult(await json('/sandbox/run',{method:'POST',body:{code,timeout:8}}));}catch(e){setCodeResult({status:'error',stderr:e.message});}finally{setRunningCode(false);}}}><Play size={14}/>{runningCode?'Running…':'Run in isolated container'}</Button><span className="small muted">No network access; CPU, memory and time limits.</span></div>
     {codeResult&&<div className="runner-output" role="status"><strong>Result: {codeResult.status}</strong><pre>{(codeResult.stdout||'')+(codeResult.stderr?'\n'+codeResult.stderr:'')}</pre></div>}
    </details></div>}
   <section className="conversation" aria-label="Conversation panel"><div className="conversation-content">
    {loadingHistory?<div className="history-loading"><Skeleton/><Skeleton width="75%"/><Skeleton width="90%"/></div>:messages.length===0?<div className="empty-state"><div className="empty-icon"><activeWorkspace.Icon size={23}/></div><h2>Start with {activeWorkspace.label.toLowerCase()}</h2><p>{activeWorkspace.description}. Responses require a configured, available AI service.</p>{workspace==='literacy'&&<p>Upload a PDF before asking a document question.</p>}{online!=='online'&&<div className="connect-hint"><WifiOff size={16}/><span>The API may be sleeping on Render.</span><Button size="sm" variant="secondary" onClick={()=>setBoot(x=>x+1)}>Retry connection</Button></div>}</div>:<div className="message-list" role="log" aria-live="polite" aria-relevant="additions text">{messages.map((m,i)=><article className={`message ${m.role==='user'?'is-user':''}`} key={m.id||i}><div className="avatar" aria-hidden="true">{m.role==='user'?'Y':'P'}</div><div className="message-body"><strong>{m.role==='user'?'You':'PACE'}</strong><p>{m.text||(busy?'Generating response…':'')}</p></div></article>)}<div ref={scrollRef}/></div>}
   </div></section>
   <div className="composer-wrap">{error&&<div className="inline-error" role="alert">{error}<button onClick={()=>setError('')} aria-label="Dismiss error"><X size={16}/></button></div>}
    {workspace==='literacy'&&<div className="document-row">{document?<><FileText size={16}/><span title={document.displayName}>{document.displayName}</span><Badge tone="success">Ready</Badge><Button variant="ghost" size="sm" onClick={async()=>{try{await json(`/documents/${document.document_id}`,{method:'DELETE'});}catch{}setDocument(null);}} aria-label="Remove document"><X size={16}/></Button></>:<span className="muted">No document selected.</span>}<input ref={fileRef} type="file" accept=".pdf,application/pdf" hidden onChange={e=>uploadPdf(e.target.files?.[0])}/><Button variant="secondary" size="sm" disabled={uploading||busy} onClick={()=>fileRef.current?.click()}><Upload size={14}/>{uploading?'Uploading…':'Upload PDF'}</Button></div>}
    <form className="composer" onSubmit={send}><label htmlFor="prompt" className="sr-only">Message PACE</label><textarea id="prompt" ref={inputRef} value={text} maxLength={6000} disabled={busy} onChange={e=>setText(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(e);}}} placeholder={online==='online'?`Ask about ${activeWorkspace.label.toLowerCase()}…`:'Backend connecting…'} rows={3}/><div className="composer-actions"><Tabs label="Model mode" items={[{value:'fast',label:'Fast'},{value:'pro',label:'Review'}]} value={speed} onChange={setSpeed}/><div className="composer-actions-right"><span className="small muted">{text.length}/6000</span><Button type="submit" disabled={busy||online!=='online'||!text.trim()} aria-label="Send message">{busy?<LoaderCircle size={18} className="spin"/>:<ArrowUp size={18}/>}</Button></div></div></form><p className="composer-footnote">AI output may contain mistakes. Review mode may reuse the same model; it is not independently verified.</p>
   </div>
  </main>
  <Modal open={settingsOpen} onClose={()=>setSettingsOpen(false)} title="Preferences"><div className="settings-grid"><label className="field"><span>Appearance</span><select value={theme.preference} onChange={e=>theme.setPreference(e.target.value)}><option value="system">Follow system</option><option value="light">Light</option><option value="dark">Dark</option></select></label>{IS_PACE_DESKTOP&&<div className="settings-info desktop-endpoint"><strong>Desktop backend</strong><p>PACE installs and launches its own Python API with local SQLite and PDF extraction. Local AI uses an Ollama model installed separately.</p><label className="field"><span>Connection</span><select value={desktopEndpoint==='local'?'local':desktopEndpoint==='hosted'?'hosted':desktopConnectionKind()} onChange={e=>setDesktopEndpoint(e.target.value)}><option value="local">Bundled local API (default)</option><option value="hosted">Hosted PACE API</option></select></label><p>Local data is saved under Windows Local AppData. Install Ollama and pull qwen2.5-coder:1.5b for AI responses without Internet.</p><Button variant="secondary" disabled={busy} onClick={saveDesktopEndpoint}>Apply connection</Button></div>}<div className="settings-info"><strong>AI provider</strong><Badge>{provider}</Badge><p>Provider credentials are managed on the backend and never placed in the browser.</p></div><div className="settings-info"><strong>Sandbox</strong><Badge>Unavailable on hosted free tier</Badge><p>Executing generated programs requires a separate isolated runtime.</p></div></div></Modal>
  <Toast message={notice} onClose={()=>setNotice('')}/>
 </div>;
}
export default App;
