import {useCallback,useEffect,useRef,useState} from 'react';
import {ArrowUp,ArrowRight,BookOpen,Code2,FileText,LayoutDashboard,Menu,Plus,Upload,Trash2,X,WifiOff,LoaderCircle,TerminalSquare,Play,ChevronRight} from 'lucide-react';
import {Badge,Button,Card,Skeleton,Tabs,Toast,Tooltip} from './components/ui.jsx';
import {createPythonRun} from './lib/pythonRunner.js';
import {InfoPage,Footer,BrandLogo} from './components/InfoPages.jsx';
import CodeResponse from './components/CodeResponse.jsx';
import {parseGeneratedResponse} from './lib/parseGeneratedResponse.js';
import {codingTurns,isLikelyCodeInput} from './lib/codingTurns.js';
import {codeOverview} from './lib/codeOverview.js';
import {generateLongCode} from './lib/longCode.js';
import {json,wakeServer,streamAnswer} from './lib/api.js';

const WORKSPACES=[{id:'coding',label:'Coding',Icon:Code2,description:'Implementation and code explanations'},{id:'literacy',label:'Literacy',Icon:BookOpen,description:'General questions, explanations and document understanding'}];

function App(){
 const [workspace,setWorkspace]=useState(()=>{
  const route=window.location.pathname.slice(1).replace(/\/$/,'')||'dashboard';
  return ['dashboard','coding','literacy','docs','privacy'].includes(route)?route:'not-found';
 });
 const [stage,setStage]=useState('');
 const [incomplete,setIncomplete]=useState(false);
 const [online,setOnline]=useState('checking');
 const [provider,setProvider]=useState('disabled');
 const [conversations,setConversations]=useState([]);
 const [activeId,setActiveId]=useState(null);
 const [messages,setMessages]=useState([]);
 const [selectedTurnOffset,setSelectedTurnOffset]=useState(0);
 const [text,setText]=useState('');
 const [busy,setBusy]=useState(false);
 const [loadingHistory,setLoadingHistory]=useState(false);
 const [sidebarOpen,setSidebarOpen]=useState(false);
 const [notice,setNotice]=useState('');
 const [document,setDocument]=useState(null);
 const [uploading,setUploading]=useState(false);
 const [speed,setSpeed]=useState('fast');
 const [error,setError]=useState('');
 const [boot,setBoot]=useState(0);
 const [code,setCode]=useState('print(42)');
 const [runningCode,setRunningCode]=useState(false);
 const [codeResult,setCodeResult]=useState(null);
 const inputRef=useRef(null);
 const scrollRef=useRef(null);
 const fileRef=useRef(null);
 const pythonRunRef=useRef(null);
 const [pythonStatus,setPythonStatus]=useState('');
 const abortRef=useRef(null);
 useEffect(()=>{const onPop=()=>{const route=window.location.pathname.slice(1).replace(/\/$/,'')||'dashboard';setWorkspace(['dashboard','coding','literacy','docs','privacy'].includes(route)?route:'not-found');};window.addEventListener('popstate',onPop);return()=>window.removeEventListener('popstate',onPop);},[]);
 useEffect(()=>{const title=({dashboard:'Dashboard',coding:'Coding',literacy:'Literacy',docs:'Docs',privacy:'Privacy','not-found':'404'})[workspace]||'Dashboard';window.document.title=title+' | PACE';const meta=window.document.querySelector('meta[name="description"]');if(meta)meta.setAttribute('content',title+' in PACE — coding and PDF literacy with configurable AI inference.');},[workspace]);
 useEffect(()=>{if(!sidebarOpen)return;const nav=window.document.querySelector('.sidebar');const previous=window.document.activeElement;const focus=nav?.querySelector('button,a,[tabindex]:not([tabindex="-1"])');focus?.focus();const key=e=>{if(e.key==='Escape'){setSidebarOpen(false);return;}if(e.key!=='Tab')return;const nodes=[...(nav?.querySelectorAll('button:not([disabled]),a[href],[tabindex]:not([tabindex="-1"])')||[])];if(!nodes.length)return;const first=nodes[0],last=nodes[nodes.length-1];if(e.shiftKey&&window.document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&window.document.activeElement===last){e.preventDefault();first.focus();}};window.document.addEventListener('keydown',key);return()=>{window.document.removeEventListener('keydown',key);previous?.focus?.();};},[sidebarOpen]);
 const statusLabel=online==='online'?'API online':online==='waking'?'Waking up API':online==='checking'?'Connecting':'API unavailable';
 const refreshList=useCallback(async()=>{try{setConversations(await json('/conversations'));}catch(e){setNotice(`Could not load chats: ${e.message}`);}},[]);
 useEffect(()=>{let cancelled=false;setOnline('checking');wakeServer(()=>!cancelled&&setOnline('waking')).then(async data=>{if(cancelled)return;setOnline('online');setProvider(data.ai_provider||'disabled');await refreshList();}).catch(()=>!cancelled&&setOnline('offline'));return()=>{cancelled=true;};},[boot,refreshList]);
 useEffect(()=>{scrollRef.current?.scrollIntoView({behavior:'smooth'});},[messages]);
 useEffect(()=>()=>{pythonRunRef.current?.cancel();},[]);
 const executeLocalPython=async()=>{
  if(runningCode||!code.trim())return;
  setRunningCode(true);setCodeResult(null);
  try{
   const job=createPythonRun(code,{onStatus:setPythonStatus});
   pythonRunRef.current=job;
   const result=await job.promise;
   setCodeResult(result);
  }catch(e){setCodeResult({status:'error',stdout:'',stderr:e?.message||'Python runner failed'});}
  finally{pythonRunRef.current=null;setRunningCode(false);setPythonStatus('');}
 };
 const stopLocalPython=()=>pythonRunRef.current?.cancel();

 const openConversation=async item=>{if(busy)return;setLoadingHistory(true);setActiveId(item.id);setWorkspace(item.workspace==='research'?'coding':item.workspace);setSidebarOpen(false);try{const res=await json(`/conversations/${encodeURIComponent(item.id)}`);setMessages(res.messages||[]);setSelectedTurnOffset(0);setDocument(res.document_id?{document_id:res.document_id,displayName:'Saved PDF context'}:null);}catch(e){setError(e.message);}finally{setLoadingHistory(false);}};
 const newChat=()=>{if(busy)return;setActiveId(null);setMessages([]);setSelectedTurnOffset(0);setDocument(null);setError('');setSidebarOpen(false);inputRef.current?.focus();};
 const clearAllData=async()=>{if(!window.confirm('Delete your PACE session conversations and PDF text from the connected backend?'))return;try{await json('/my-data',{method:'DELETE'});setConversations([]);setMessages([]);setActiveId(null);setDocument(null);localStorage.removeItem('pace.session.v2');setNotice('Session conversations and PDF text deleted from the connected API.');}catch(e){setError('Deletion failed: '+e.message);}};
 const send=async e=>{
  e?.preventDefault?.();if(busy||!text.trim())return;
  const value=text.trim();setText('');setSelectedTurnOffset(0);setError('');setBusy(true);setIncomplete(false);setStage('actor');
  const user={role:'user',text:value,id:'local-'+Date.now()};
  const assistantId='reply-'+Date.now();
  setMessages(prev=>[...prev,user,{id:assistantId,role:'assistant',text:''}]);
  const controller=new AbortController();abortRef.current=controller;
  let output='';let lastRender=0;
  const paint=()=>setMessages(prev=>prev.map(m=>m.id===assistantId?{...m,text:output}:m));
  try {
   const request={text:value,mode:workspace==='literacy'&&!document?'coding':workspace,speed_mode:speed,conversation_id:activeId,document_id:document?.document_id};
   const onStreamEvent=evt=>{
    if(evt.type==='init'){setActiveId(evt.conversation_id);setStage(evt.stage||'actor');}
    if(evt.type==='stage')setStage(evt.stage);
    if(evt.type==='token'){output+=evt.content||'';if(Date.now()-lastRender>=90){paint();lastRender=Date.now();}}
    if(evt.type==='done')paint();
    if(evt.type==='progress')setStage('section '+evt.round+' / '+evt.maxRounds);
    if(evt.type==='long_done'&&!evt.complete){
     setIncomplete(true);
     setError('Generation stopped at the safety limit ('+evt.reason+'). Partial code is preserved. Use Continue for the remaining implementation.');
    }
   };
   if(workspace==='coding')await generateLongCode(request,onStreamEvent,controller.signal);
   else await streamAnswer(request,onStreamEvent,controller.signal);
   paint();await refreshList();
  }catch(err){
   paint();setMessages(prev=>prev.map(m=>m.id===assistantId?{...m,text:output,incomplete:true}:m));setIncomplete(true);
   setError(output?'The response was interrupted. Partial output is preserved; use Continue for the next section.':err.status===503?'The hosted model could not finish. Its output length or quota may be limited; try one file or function at a time.':err.message||'Generation failed');
   
  }finally{setBusy(false);setStage('');abortRef.current=null;}
 };
 const uploadPdf=async file=>{if(!file)return;if(!file.name.toLowerCase().endsWith('.pdf')||file.size>8*1024*1024){setError('Select a PDF smaller than 8 MB.');return;}setUploading(true);setError('');try{const data=new FormData();data.append('file',file);const outcome=await json('/upload',{method:'POST',body:data});setDocument({...outcome,displayName:file.name});setNotice('Document processed. You can now ask questions about it.');}catch(e){setError(e.message);}finally{setUploading(false);if(fileRef.current)fileRef.current.value='';}};
 const removeChat=async item=>{if(!window.confirm('Delete this conversation?'))return;try{await json(`/conversations/${encodeURIComponent(item.id)}`,{method:'DELETE'});if(item.id===activeId)newChat();await refreshList();}catch(e){setError(e.message);}};
 const activeWorkspace=WORKSPACES.find(w=>w.id===workspace) || {label:({dashboard:'Dashboard',docs:'Docs',privacy:'Privacy','not-found':'404'})[workspace]||'Dashboard',description:'System overview',Icon:LayoutDashboard};
 const turns=workspace==='coding'?codingTurns(messages):[];
 const selectedCodingTurn=turns[Math.max(0,turns.length-1-selectedTurnOffset)]||null;
 const parsedCodingResponse=parseGeneratedResponse(selectedCodingTurn?.response||'');
 const unfinishedCode=workspace==='coding'&&!busy&&parsedCodingResponse.files.some(f=>f.incomplete);
 const navigate=page=>{window.history.pushState(null,'',page==='dashboard'?'/':'/'+page);setWorkspace(page);setSidebarOpen(false);setError('');};
 const goDashboard=()=>navigate('dashboard');
 return <div className="app-shell">
  <a href="#main" className="skip-link">Skip to workspace</a>
  {sidebarOpen&&<button className="mobile-backdrop" aria-label="Close navigation" onClick={()=>setSidebarOpen(false)}/>}
  <aside id="pace-sidebar" className={`sidebar ${sidebarOpen?'open':''}`} aria-label="Main navigation">
   <button className="brand brand-button" onClick={goDashboard} aria-label="PACE dashboard"><BrandLogo size={36}/><div><strong>PACE</strong><small>Actor / Critic</small></div></button>
   <p className="section-caption">WORKSPACE</p><nav aria-label="Workspaces" className="workspace-nav">
    <button className={workspace==='dashboard'?'selected':''} aria-current={workspace==='dashboard'?'page':undefined} onClick={goDashboard}><LayoutDashboard size={18}/>Dashboard</button>
    {WORKSPACES.map(({id,label,Icon})=><button key={id} className={workspace===id?'selected':''} aria-current={workspace===id?'page':undefined} onClick={()=>{navigate(id);newChat();}}><Icon size={18}/>{label}</button>)}
    <button onClick={()=>navigate('docs')} className={workspace==='docs'?'selected':''}><BookOpen size={18}/>Docs</button>
   </nav>
   <Button variant="secondary" className="new-chat" onClick={()=>{navigate(workspace==='literacy'?'literacy':'coding');newChat();}}><Plus size={16}/>New conversation</Button>
   <div className="sidebar-history"><p className="section-caption">RECENT CONVERSATIONS</p>{conversations.length===0?<p className="muted small">Your recent conversations appear here.</p>:conversations.slice(0,25).map(item=><div className="history-row" key={item.id}><button className={activeId===item.id?'active':''} onClick={()=>openConversation(item)} title={item.title}>{item.title}</button><Tooltip text="Delete conversation"><button className="icon-action" aria-label={`Delete ${item.title}`} onClick={()=>removeChat(item)}><Trash2 size={14}/></button></Tooltip></div>)}</div>
   <div className="sidebar-footer"><Button variant="ghost" onClick={()=>navigate('privacy')}>Privacy & data</Button></div>
  </aside>
  <main id="main" className="main-panel">
   <header className="topbar"><div className="topbar-left"><Button size="sm" variant="ghost" className="mobile-menu" aria-label="Open navigation" aria-expanded={sidebarOpen} aria-controls="pace-sidebar" onClick={()=>setSidebarOpen(true)}><Menu size={20}/></Button><div><h1><span style={{color:'#797288'}}>PACE / </span>{activeWorkspace.label}</h1></div></div><div className="topbar-actions"><span className={'connection-indicator '+(online==='online'?'is-online':online==='offline'?'is-offline':'')}><span className="connection-dot"/>{statusLabel}</span></div></header>
   {workspace==='coding'&&<div className="coding-tools"><details><summary><TerminalSquare size={16}/> Python runner <Badge tone="success">Runs on your device</Badge></summary>
     <label className="field" htmlFor="sandbox-code"><span>Python source (local WebAssembly runtime)</span><textarea id="sandbox-code" spellCheck="false" value={code} maxLength={20000} onChange={e=>setCode(e.target.value)} rows={5} placeholder="print('Hello from PACE')"/></label>
     <div className="runner-actions">
       <Button size="sm" disabled={runningCode||!code.trim()} onClick={executeLocalPython}><Play size={14}/>{runningCode?'Running…':'Run Python'}</Button>
       {runningCode&&<Button size="sm" variant="secondary" onClick={stopLocalPython}>Stop</Button>}
       <span className="small muted">{pythonStatus||'Python 3 runs in a local Web Worker; no Render code execution. 8-second run limit.'}</span>
     </div>
     {codeResult&&<div className="runner-output" role="status"><strong>Result: {codeResult.status}</strong><pre>{(codeResult.stdout||'')+(codeResult.stderr?'\n'+codeResult.stderr:'')||'(No output. Use print() to display values.)'}</pre></div>}
     <p className="small muted">Runs Python locally in a browser worker. Not a hardened security sandbox; do not run untrusted code. Some native Python packages and OS features are unavailable.</p>
    </details></div>}
   {workspace==='dashboard'&&<section className="dashboard-panel" aria-label="System overview">
     <div className="dashboard-hero">
      <img className="hero-brand-art" src="/pace-logo.svg" width="300" height="300" alt="PACE — Pipelined Actor-Critic Ensemble"/>
      <span className="hero-kicker">PACE / THE INTELLIGENCE WORKSPACE</span>
      <h2>Build with a<br/><em>second perspective.</em></h2>
      <p>One system creates. Another reviews. You stay in control of the final result.</p>
      <div className="dashboard-actions"><Button onClick={()=>{navigate('coding');newChat();}}>Start coding <ArrowRight size={16}/></Button><Button variant="secondary" onClick={()=>{navigate('literacy');newChat();}}>Explore Literacy</Button></div>
     </div>
     <h3 className="sectionhead">System overview</h3>
     <div className="dashboard-grid">
      <Card><h3>Connection</h3><p className="metric cyan">{online==='online'?'Connected':online==='waking'?'Waking up':online==='checking'?'Connecting':'Offline'}</p><p>{statusLabel}</p></Card>
      <Card><h3>Provider</h3><p className="metric">{provider==='disabled'?'Not configured':provider}</p><p>PACE backend inference</p></Card>
      <Card><h3>Actor / Critic</h3><p className="metric purple">Standby</p><p>Reviewer runs in Pro when supported</p></Card>
      <Card><h3>Recent sessions</h3><p className="metric">{String(conversations.length).padStart(2,'0')}</p><p>Available to your session</p></Card>
     </div>
     <h3 className="sectionhead">YOUR WORKSPACE</h3>
     <div className="dashboard-workspaces">
      <Card><h3>Dual-engine workflow</h3><p>Transparent generation and review. Hosted Pro may use the same model for both stages.</p>
       <div className="pipeline"><div className="stage"><strong>Actor</strong><span>Generate</span></div><span className="arrow">→</span><div className="stage"><strong>Critic</strong><span>Review</span></div><span className="arrow">→</span><div className="stage"><strong>Result</strong><span>Inspect</span></div></div>
      </Card>
      <Card><h3>Start something</h3>
       <button className="dashboard-route" onClick={()=>{navigate('coding');newChat();}}><span className="dashboard-route-icon"><Code2 size={18}/></span><span><b>Coding</b><small>Generate, refactor and debug</small></span><ChevronRight size={17}/></button>
       <button className="dashboard-route" onClick={()=>{navigate('literacy');newChat();}}><span className="dashboard-route-icon"><BookOpen size={18}/></span><span><b>Literacy</b><small>General questions and document analysis</small></span><ChevronRight size={17}/></button>
      </Card>
     </div>
     <div className="recent-panel card"><strong>Recent activity</strong><p>{conversations.length?conversations.length+' conversation(s) available. Open one from the sidebar.':'No recent sessions yet. Start with Coding or Literacy.'}</p></div>
    </section>}
   {['docs','privacy','not-found'].includes(workspace)&&<InfoPage page={workspace} onNavigate={navigate}/>}
   {workspace==='privacy'&&<section className="privacy-controls card"><div><h3>Session data controls</h3><p>Delete conversation history and stored PDF text for this browser session from the connected API.</p></div><Button variant="secondary" disabled={online!=='online'} onClick={clearAllData}>Delete session data</Button></section>}
   <div className={['coding','literacy'].includes(workspace)?'workspace-stage'+(workspace==='coding'?' is-coding':''):'workspace-empty'}>
   {workspace==='coding'&&<section className="conversation" aria-label="AI explanation panel">
     <div className="conversation-content">
       <h2 className="explanation-heading">AI explanation</h2>
       {loadingHistory?<div className="history-loading"><Skeleton/><Skeleton width="75%"/><Skeleton width="90%"/></div>:
       !selectedCodingTurn?<div className="empty-state"><div className="empty-icon"><Code2 size={23}/></div><h2>Ask PACE to write code</h2><p>Submit a programming request. The explanation and generated source will appear in separate panels.</p>{online!=='online'&&<div className="connect-hint"><WifiOff size={16}/> The API may be waking up. <Button size="sm" variant="secondary" onClick={()=>setBoot(x=>x+1)}>Retry</Button></div>}</div>:
       <div className="focused-result">

         <div className="focus-explanation">
           {selectedCodingTurn.response?(parsedCodingResponse.explanation?
              <CodeResponse text={selectedCodingTurn.response} mode="explanation"/>:
              parsedCodingResponse.files.length?<div className="code-overview"><h3>Code overview</h3><p>{codeOverview(parsedCodingResponse.files)}</p><p className="small muted">This summary is derived from the source text. The model did not provide a written explanation, and the code has not been tested.</p></div>:
              <p className="muted">No usable AI explanation was provided.</p>):
             <p className="muted">{busy?'Generating code…':selectedCodingTurn.unverifiedReview?'The model returned an unsupported correctness claim. No code was tested or verified.':'No usable response was returned for this request.'}</p>}
           {selectedCodingTurn.incomplete&&<p className="inline-error">Generation was interrupted. Code may be incomplete.</p>}
         </div>
       </div>}
     </div>
   </section>}
   {workspace==='literacy'&&<section className="conversation" aria-label="Conversation panel"><div className="conversation-content">
     {loadingHistory?<div className="history-loading"><Skeleton/><Skeleton width="75%"/><Skeleton width="90%"/></div>:
      messages.length===0?<div className="empty-state"><div className="empty-icon"><BookOpen size={23}/></div><h2>Start with literacy</h2><p>Ask general questions or use a PDF for document-grounded answers.</p></div>:
      <div className="message-list" role="log" aria-live="polite" aria-relevant="additions text">{messages.map((m,i)=><article className={`message ${m.role==='user'?'is-user':''}`} key={m.id||i}>
        <div className="avatar" aria-hidden="true">{m.role==='user'?'Y':'P'}</div>
        <div className="message-body"><strong>{m.role==='user'?'You':'PACE'}</strong>{m.role==='assistant'?<CodeResponse text={m.text||(busy?'Generating response…':'')}/>:<p>{m.text}</p>}</div>
       </article>)}<div ref={scrollRef}/></div>}
   </div></section>}
   {workspace==='coding'&&<aside className="generated-panel" aria-label="Generated code panel">
      <header className="generated-panel-header"><Code2 size={17}/><h2>Generated code</h2><span>For the selected request only</span></header>
      <div className="generated-panel-scroll">
       {!selectedCodingTurn?<p className="muted generated-placeholder">Generated files will appear here after you submit a request.</p>:!selectedCodingTurn.response?<div className="generated-empty-result"><p>{busy?'Generating source code…':'No usable code was returned. No program has been verified.'}</p>{!busy&&<Button variant="secondary" size="sm" onClick={()=>{setText(selectedCodingTurn.request);inputRef.current?.focus();}}>Retry this request</Button>}</div>:
        parsedCodingResponse.files.length?<section className="generated-reply">
           <CodeResponse text={selectedCodingTurn.response} mode="code"/>
           {(selectedCodingTurn.incomplete||parsedCodingResponse.files.some(f=>f.incomplete))&&<p className="inline-error">This code is incomplete. Do not run it without reviewing and completing it.</p>}
           <p className="muted code-verification-note">AI-generated code has not been executed or verified by PACE.</p>
         </section>:
         <div className="generated-empty-result"><p>No usable code was returned for this request. A model review is not proof that the code works.</p>
           <Button variant="secondary" size="sm" onClick={()=>{setText(selectedCodingTurn.request);inputRef.current?.focus();}}>Retry this request</Button>
         </div>}
      </div>
   </aside>}
   {['coding','literacy'].includes(workspace)&&<div className="composer-wrap">{error&&<div className="inline-error" role="alert">{error}<button onClick={()=>setError('')} aria-label="Dismiss error"><X size={16}/></button></div>}
    {workspace==='literacy'&&<div className="document-row">{document?<><FileText size={16}/><span title={document.displayName}>{document.displayName}</span><Badge tone="success">Ready</Badge><Button variant="ghost" size="sm" onClick={async()=>{try{await json(`/documents/${document.document_id}`,{method:'DELETE'});}catch{}setDocument(null);}} aria-label="Remove document"><X size={16}/></Button></>:<span className="muted">No document selected.</span>}<input ref={fileRef} type="file" accept=".pdf,application/pdf" hidden onChange={e=>uploadPdf(e.target.files?.[0])}/><Button variant="secondary" size="sm" disabled={uploading||busy} onClick={()=>fileRef.current?.click()}><Upload size={14}/>{uploading?'Uploading…':'Upload PDF'}</Button></div>}
    <form className="composer" onSubmit={send}><label htmlFor="prompt" className="sr-only">Message PACE</label><textarea id="prompt" ref={inputRef} value={text}  disabled={busy} onChange={e=>setText(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(e);}}} placeholder={workspace==='literacy'?'Ask anything, or ask about your PDF…':'Describe a coding task…'} rows={3}/><div className="composer-actions">{busy&&<Badge tone="warning">{speed.toUpperCase()} · {stage==='critic'?'Critic reviewing':stage.startsWith('section')?('Generating '+stage):'Actor drafting'}</Badge>}<Tabs label="Model mode" items={[{value:'fast',label:'Fast'},{value:'pro',label:'Review'}]} value={speed} onChange={setSpeed}/><div className="composer-actions-right"><span className="small muted">{text.length} characters</span><Button type="submit" disabled={busy||online!=='online'||!text.trim()} aria-label="Send message">{busy?<LoaderCircle size={18} className="spin"/>:<ArrowUp size={18}/>}</Button></div></div></form>{workspace==='coding'&&turns.length>1&&<div className="request-history-control"><label htmlFor="coding-request-history">View request</label><select id="coding-request-history" value={selectedTurnOffset} onChange={e=>setSelectedTurnOffset(Number(e.target.value))}>{turns.map((turn,i)=><option value={turns.length-1-i} key={turn.id}>{i+1}. {isLikelyCodeInput(turn.request)?'Submitted source code':turn.request.replace(/\s+/g,' ').slice(0,68)}</option>)}</select></div>}
    {workspace==='coding'&&selectedCodingTurn&&(isLikelyCodeInput(selectedCodingTurn.request)?
       <details className="selected-request-card submitted-source"><summary>Submitted source code <span>View original input</span></summary><pre>{selectedCodingTurn.request}</pre></details>:
       <div className="focus-request selected-request-card"><strong>Your request</strong><p>{selectedCodingTurn.request}</p></div>)}{(incomplete||unfinishedCode)&&<div className="runner-actions"><Button variant="secondary" onClick={()=>{setText('Continue the unfinished code from exactly where it stopped. Output only the missing next section. Original task: '+(selectedCodingTurn?.request||'preceding coding task').slice(0,1100)+String.fromCharCode(10,10)+'PREVIOUS OUTPUT TAIL:'+String.fromCharCode(10)+(selectedCodingTurn?.response||'').slice(-950));inputRef.current?.focus();setIncomplete(false);}}>Continue</Button></div>}<p className="composer-footnote">AI output may contain mistakes. Review mode may reuse the same model; it is not independently verified.</p>
   </div>}
   </div>
   <Footer onNavigate={navigate}/>
   <nav className="pace-mobile-tabs" aria-label="Mobile navigation">{[['dashboard','Home',LayoutDashboard],['coding','Coding',Code2],['literacy','Literacy',BookOpen],['docs','Docs',BookOpen]].map(([id,label,Icon])=><button key={id} className={workspace===id?'selected':''} aria-current={workspace===id?'page':undefined} onClick={()=>{navigate(id);if(id==='coding'||id==='literacy')newChat();}}><Icon size={18}/>{label}</button>)}</nav>
  </main>
  <Toast message={notice} onClose={()=>setNotice('')}/>
 </div>;
}
export default App;
