const BASE=(import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/,'');
const SESSION_KEY='pace.session.v2';
export function sessionToken(){
  let token=localStorage.getItem(SESSION_KEY);
  if(!token || !/^[a-f0-9]{64}$/.test(token)){
    const bytes=new Uint8Array(32);
    crypto.getRandomValues(bytes);
    token=Array.from(bytes,x=>x.toString(16).padStart(2,'0')).join('');
    localStorage.setItem(SESSION_KEY,token);
  }
  return token;
}
export class ApiError extends Error{constructor(status,message){super(message);this.status=status;}}
export async function api(path,{method='GET',body,signal,headers={}}={}){
  const options={method,signal,headers:{'X-PACE-Session':sessionToken(),...headers}};
  if(body instanceof FormData)options.body=body;
  else if(body!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
  const response=await fetch(`${BASE}${path}`,options);
  if(!response.ok){let message='Request failed';try{const data=await response.json();message=typeof data.detail==='string'?data.detail:message;}catch{}throw new ApiError(response.status,message);}
  return response;
}
export async function json(path,options){return (await api(path,options)).json();}
export async function wakeServer(onStatus){
  let delay=1200;
  for(let i=0;i<6;i++){
    try{const res=await fetch(`${BASE}/health`,{signal:AbortSignal.timeout(20000)});if(res.ok)return res.json();}
    catch{onStatus?.('waking');}
    if(i<5){await new Promise(resolve=>setTimeout(resolve,delay));delay=Math.min(delay*2,8000);}
  }
  throw new Error('Backend is currently unreachable');
}
export async function streamAnswer(body,onEvent,signal){
  const response=await api('/generate',{method:'POST',body,signal});
  const reader=response.body?.getReader();if(!reader)throw new ApiError(502,'Streaming is not supported');
  const decoder=new TextDecoder();let pending='';let finished=false;
  try{
    while(true){
      const {value,done}=await reader.read();if(done)break;
      pending+=decoder.decode(value,{stream:true});
      const frames=pending.replaceAll('\r\n','\n').split('\n\n');pending=frames.pop()??'';
      for(const frame of frames){
        const line=frame.split('\n').find(x=>x.startsWith('data:'));
        if(!line)continue;
        let event;try{event=JSON.parse(line.slice(5));}catch{throw new ApiError(502,'Malformed AI response');}
        if(event.type==='error')throw new ApiError(503,event.content||'AI inference failed');
        onEvent(event);
        if(event.type==='done')finished=true;
      }
    }
    if(!finished)throw new ApiError(502,'AI response ended before completion');
  }finally{reader.releaseLock();}
}
