import {parseGeneratedResponse} from '../lib/parseGeneratedResponse.js';
import {useState} from 'react';
import {Check,Copy,Download,WrapText} from 'lucide-react';

function highlighted(code,language){
 if(!/^(py|python|js|javascript|jsx|ts|tsx|rust|go|java|cpp|c|json|bash|sh|sql)$/.test(language))return code;
 const tokens=code.split(/("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:def|class|return|import|from|for|while|if|else|elif|try|except|async|await|function|const|let|var|export|default|public|private|fn|struct|impl|package|func|SELECT|FROM|WHERE|true|false|null|None)\b)/g);
 return tokens.map((t,i)=>t.startsWith('"')||t.startsWith("'")?<span className="code-string" key={i}>{t}</span>:/^(def|class|return|import|from|for|while|if|else|elif|try|except|async|await|function|const|let|var|export|default|public|private|fn|struct|impl|package|func|SELECT|FROM|WHERE|true|false|null|None)$/.test(t)?<span className="code-keyword" key={i}>{t}</span>:t);
}
function CodeBlock({lang='text',filename,code,incomplete=false}){
 const [copied,setCopied]=useState(false);const [wrap,setWrap]=useState(false);
 const file=filename||('snippet.'+({python:'py',javascript:'js',typescript:'ts',bash:'sh',rust:'rs',cpp:'cpp'}[lang]||lang||'txt'));
 const copy=async()=>{try{await navigator.clipboard.writeText(code);setCopied(true);}catch{setCopied(false);}};
 const download=()=>{const blob=new Blob([code],{type:'text/plain;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=file;a.click();URL.revokeObjectURL(url);};
 return <div className="pace-code-block"><div className="pace-code-head"><span>{file} · {lang||'text'}{incomplete?' · unfinished block':''}</span><div><button onClick={copy} aria-label="Copy code">{copied?<Check size={14}/>:<Copy size={14}/>} {copied?'Copied':'Copy'}</button><button onClick={()=>setWrap(v=>!v)} aria-pressed={wrap} title="Toggle line wrap"><WrapText size={14}/></button><button onClick={download} title="Download file" aria-label={'Download '+file}><Download size={14}/></button></div></div><pre className={wrap?'code-wrap':''}><code>{highlighted(code,lang)}</code></pre></div>;
}
export default function CodeResponse({text='',mode='both'}) {
 const {explanation,files}=parseGeneratedResponse(text);
 const showExplanation=mode!=='code';
 const showCode=mode!=='explanation';
 return <div className="response-content">
  {showExplanation&&(explanation?<p>{explanation}</p>:mode==='explanation'?<p className="muted">{files.length?'Code is displayed in the Generated code panel.':'Waiting for an AI explanation…'}</p>:null)}
  {showCode&&(files.length?files.map((file,i)=><CodeBlock key={i} lang={file.language} filename={file.filename} code={file.code} incomplete={file.incomplete}/>):mode==='code'?<p className="muted">No code artifact in this reply yet.</p>:null)}
 </div>;
}
