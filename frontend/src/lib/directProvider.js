import {IS_PACE_DESKTOP} from './desktopApi.js';
function endpoint(model){
 let base=model.baseUrl.trim().replace(/\/$/,'');
 if(!base){
  base=({openai:'https://api.openai.com/v1',openrouter:'https://openrouter.ai/api/v1',anthropic:'https://api.anthropic.com/v1',google:'https://generativelanguage.googleapis.com/v1beta'}[model.provider]||'');
 }
 const url=new URL(base);
 if(url.username||url.password||url.hash||url.search||!(url.protocol==='https:'||(url.protocol==='http:'&&['localhost','127.0.0.1'].includes(url.hostname))))throw new Error('Use an HTTPS provider origin or loopback URL without credentials, fragments or query.');
 return url.toString().replace(/\/$/,'');
}
export async function providerReply(model,question,{signal}={}){
 if(IS_PACE_DESKTOP){
   if(signal?.aborted)throw new Error('Request cancelled');
   const invoke=window.__TAURI__?.core?.invoke;
   if(typeof invoke!=='function')throw new Error('Desktop native provider is unavailable');
   return invoke('desktop_provider_request',{request:{
     credentialId:model.id,provider:model.provider,modelId:model.modelId,
     baseUrl:model.baseUrl||'',prompt:question
   }});
 }
 if(!model.key)throw new Error('Add an API key in Models before sending a request.');
 const base=endpoint(model);
 const common={'Content-Type':'application/json'};
 let url,headers,body;
 if(model.provider==='anthropic'){
  url=base+'/messages'; headers={...common,'x-api-key':model.key,'anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'};
  body={model:model.modelId,max_tokens:2048,messages:[{role:'user',content:question}]};
 }else if(model.provider==='google'){
  url=base+'/models/'+encodeURIComponent(model.modelId)+':generateContent';headers={...common,'x-goog-api-key':model.key};body={contents:[{parts:[{text:question}]}]};
 }else{
  url=base+'/chat/completions';headers={...common,Authorization:'Bearer '+model.key};
  body={model:model.modelId,max_tokens:2048,messages:[{role:'user',content:question}]};
 }
 let response;
 try{response=await fetch(url,{method:'POST',headers,body:JSON.stringify(body),signal});}
 catch(error){throw new Error('Direct provider request failed (network/CORS). Use the desktop app if this provider blocks browser access. '+error.message);}
 if(!response.ok)throw new Error('Provider returned HTTP '+response.status+'; check model, endpoint, billing and permissions.');
 const result=await response.json();
 const answer=model.provider==='anthropic'?result.content?.filter(i=>i.type==='text').map(i=>i.text).join('\n'):model.provider==='google'?result.candidates?.[0]?.content?.parts?.map(p=>p.text||'').join('\n'):result.choices?.[0]?.message?.content;
 if(typeof answer!=='string'||!answer.trim())throw new Error('Provider returned no usable answer; output may have been limited.');
 return answer;
}
export async function directGenerate(model,question,speed,{signal,onStage}={}){
 onStage?.('actor');
 const draft=await providerReply(model,question,{signal});
 if(speed==='fast')return draft;
 onStage?.('critic');
 return providerReply(model,'Review and improve this response without losing code or details. State uncertainty. Return only the complete reviewed response.\n\nREQUEST:\n'+question+'\n\nDRAFT:\n'+draft,{signal});
}
