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
export default function CodeResponse({text=''}){
 const re=/```([^\n]*)\n([\s\S]*?)```/g;const output=[];let last=0;let index=0;let match;
 while((match=re.exec(text))!==null){if(match.index>last)output.push(<p key={'p'+index}>{text.slice(last,match.index)}</p>);
 const header=match[1].trim().split(/\s+/);let lang=header[0]||'text';const filename=(header.slice(1).find(x=>x.startsWith('filename='))||'').replace(/^filename=/,'')||header.slice(1).find(x=>/\.[a-z0-9]+$/i.test(x));
 output.push(<CodeBlock key={'code'+index} lang={lang} filename={filename} code={match[2]}/>);last=re.lastIndex;index++;}
 if(last<text.length){const rest=text.slice(last);const open=rest.match(/```([^\n]*)\n([\s\S]*)$/);
 if(open){if(open.index>0)output.push(<p key="rest-text">{rest.slice(0,open.index)}</p>);output.push(<CodeBlock key="unfinished" lang={open[1].trim().split(/\s+/)[0]||'text'} code={open[2]} incomplete/>);}
 else output.push(<p key="rest">{rest}</p>);}
 return <div className="response-content">{output}</div>;
}
