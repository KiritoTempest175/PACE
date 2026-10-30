import {parseGeneratedResponse} from './parseGeneratedResponse.js';
import {streamAnswer} from './api.js';

// Client-side bounded continuation works with the existing PACE Render API.
// The hosted model may stop after ~256 tokens, returning partial tokens and
// then an SSE error. Preserve those tokens instead of discarding the answer.
export const MAX_CODE_ROUNDS=8;
export const MAX_CODE_CHARS=32000;

export function removeRepeatedPrefix(previous, next){
 const oldText=String(previous||'');
 const newText=String(next||'');
 const limit=Math.min(1000,oldText.length,newText.length);
 for(let length=limit;length>=24;length--){
  if(oldText.endsWith(newText.slice(0,length)))return newText.slice(length);
 }
 return newText;
}

export function needsCodeContinuation(text){
 const {files}=parseGeneratedResponse(text);
 return files.some(file=>file.incomplete);
}

function continuationPrompt(original,content){
 // Keep within both the backend's and the Space's input context windows.
 const originalTask=original.slice(0,1300);
 const tail=content.slice(-1100);
 return ['Continue the exact same implementation, do not start over.',
  'Return ONLY the missing continuation, without a new introductory paragraph.',
  'Do not repeat any preceding lines. Do not open a new Markdown code fence if one is already open.',
  'Finish the current file and close the existing code fence when done.',
  'Original task:',originalTask,'ALREADY GENERATED (last section):',tail,
  'CONTINUE IMMEDIATELY AFTER THE LAST CHARACTER ABOVE:'].join('\n');
}

// onEvent preserves the normal SSE contract to the caller. Each new hosted
// response is de-duplicated before being appended to the displayed output.
export async function generateLongCode(request,onEvent,signal,{maxRounds=MAX_CODE_ROUNDS,send=streamAnswer}={}){
 const original=request.text;
 let accumulated='';
 let conversationId=request.conversation_id||null;
 let stopReason='complete';
 for(let round=0;round<maxRounds;round++){
  if(signal?.aborted)throw signal.reason||new Error('Generation cancelled');
  const prompt=round===0?original:continuationPrompt(original,accumulated);
  let section='';
  let completed=false;
  let lastError=null;
  let announced=false;
  onEvent({type:'progress',round:round+1,maxRounds});
  try{
   await send({...request,text:prompt,conversation_id:conversationId,speed_mode:round===0?request.speed_mode:'fast'},event=>{
    if(event.type==='init'){
     conversationId=event.conversation_id||conversationId;
     onEvent({...event,conversation_id:conversationId});
    }else if(event.type==='stage'){
     onEvent(event);
    }else if(event.type==='token'){
     section+=event.content||'';
     // If the model starts repeating the tail, suppress it before emission.
     if(!announced&&section.length<1200){
      const delta=removeRepeatedPrefix(accumulated,section);
      // Wait for enough context to identify a substantial repeated prefix.
      if(round>0&&accumulated&&section.length<64) return;
      if(delta) {onEvent({type:'token',content:delta});announced=true;}
     }else{
      const newText=event.content||'';
      onEvent({type:'token',content:newText});
      announced=true;
     }
    }else if(event.type==='done'){
     completed=true;
    }else if(event.type==='error'){
     throw new Error(event.content||'Generation interrupted');
    }
   },signal);
  }catch(error){
   lastError=error;
   if(signal?.aborted)throw error;
  }
  const deduplicated=removeRepeatedPrefix(accumulated,section);
  // Emit any held prefix when the provider finished before the first 64 chars.
  if(!announced&&deduplicated)onEvent({type:'token',content:deduplicated});
  if(!deduplicated&&section){
   stopReason='repeated_content';break;
  }
  if(!section.trim()){
   if(lastError)throw lastError;
   stopReason='empty_section';break;
  }
  accumulated+=deduplicated;
  if(accumulated.length>=MAX_CODE_CHARS){stopReason='length_limit';break;}
  if(completed&&!needsCodeContinuation(accumulated)){
   stopReason='complete';break;
  }
  if(round===maxRounds-1){stopReason='round_limit';break;}
  if(round>0&&deduplicated.trim().length<25){
   stopReason='no_progress';break;
  }
 }
 const complete=stopReason==='complete';
 onEvent({type:'long_done',complete,reason:stopReason,conversation_id:conversationId});
 return {text:accumulated,complete,reason:stopReason,conversation_id:conversationId};
}
