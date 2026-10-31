import {parseGeneratedResponse} from './parseGeneratedResponse.js';
import {streamAnswer} from './api.js';

export const MAX_CODE_ROUNDS=8;
export const MAX_CODE_CHARS=32000;

export function removeRepeatedPrefix(previous,next){
 const older=String(previous||'');
 const incoming=String(next||'');
 for(let length=Math.min(1600,older.length,incoming.length);length>=16;length--){
  if(older.endsWith(incoming.slice(0,length)))return incoming.slice(length);
 }
 return incoming;
}

export function needsCodeContinuation(text) {
 return parseGeneratedResponse(text).files.some(file=>file.incomplete);
}

function continuationPrompt(original,content) {
 return [
  'Continue ONLY the unfinished code in the previous output.',
  'Do not restart the program, duplicate imports, or explain the existing lines.',
  'If an opening Markdown fence is already present, do not open another one.',
  'Finish the implementation, close the existing Markdown fence, and stop.',
  'ORIGINAL TASK:',original.slice(0,1400),
  'PREVIOUS CODE TAIL:',content.slice(-1600),
  'MISSING CODE (start immediately after the tail):'
 ].join('\n');
}

function ensureCodingPrompt(original){
 return 'Write a runnable implementation for the following programming task. '+
  'Return at least one complete Markdown code fence, with its language and filename. '+
  'Explanations are optional but must be outside the code fence. Never claim code was tested.\n\n'+original.slice(0,1800);
}

function cleanContinuation(previous,next){
 let incoming=String(next||'').trimStart();
 if(!previous)return incoming;
 if(needsCodeContinuation(previous)){
  // The code fence is already open in the previous part.
  incoming=incoming.replace(/^(```[^\n`]*\n)/,'');
  // Remove a redundant opening after a short model preface.
  incoming=incoming.replace(/^(?:Here (?:is|are)[^\n]*\n){1,2}```[^\n`]*\n/i,'');
 }
 return removeRepeatedPrefix(previous,incoming);
}

export async function generateLongCode(request,onEvent,signal,{maxRounds=MAX_CODE_ROUNDS,send=streamAnswer}={}){
 const original=request.text;
 let accumulated='';
 let conversationId=request.conversation_id||null;
 let stopReason='round_limit';
 let completedCode=false;
 let usedNoCodeRetry=false;
 for(let round=0;round<maxRounds;round++){
  if(signal?.aborted)throw signal.reason||new Error('Generation cancelled');
  const prompt=round===0?original:
   (!accumulated?ensureCodingPrompt(original):continuationPrompt(original,accumulated));
  let section='';
  let completed=false;
  let failure=null;
  onEvent({type:'progress',round:round+1,maxRounds});
  try{
   await send({...request,text:prompt,conversation_id:conversationId,speed_mode:round===0?request.speed_mode:'fast'},event=>{
    if(event.type==='init'){
     conversationId=event.conversation_id||conversationId;
     if(round===0)onEvent(event);
    }else if(event.type==='stage'){
     if(round===0)onEvent(event);
    }else if(event.type==='token'){
     section+=event.content||'';
    }else if(event.type==='done'){
     completed=true;
    }
   },signal);
  }catch(error){
   if(signal?.aborted)throw error;
   failure=error;
  }

  if(!section.trim()){
   if(!accumulated){
    if(failure)throw failure;
    stopReason='empty_output';
   }else stopReason='empty_continuation';
   break;
  }
  if(!accumulated&&!parseGeneratedResponse(section).files.length){
   // The Pro reviewer sometimes returns "the code is correct" without any
   // code. Never display such a statement as a verified generation result.
   if(!usedNoCodeRetry&&round+1<maxRounds){
    usedNoCodeRetry=true;
    continue;
   }
   stopReason='no_code';
   break;
  }
  const delta=cleanContinuation(accumulated,section);
  if(!delta.trim()){
   stopReason='repeated_content';
   break;
  }
  // Send only validated, de-duplicated segments. Raw streamed prefixes may
  // repeat across requests, so emitting them immediately corrupts the output.
  accumulated+=delta;
  onEvent({type:'token',content:delta});
  if(accumulated.length>MAX_CODE_CHARS){
   stopReason='length_limit';
   break;
  }
  if(completed&&!needsCodeContinuation(accumulated)){
   completedCode=parseGeneratedResponse(accumulated).files.some(file=>!file.incomplete&&file.code.trim());
   stopReason=completedCode?'complete':'invalid_code';
   break;
  }
  if(round===maxRounds-1)stopReason='round_limit';
  else if(round>0&&delta.trim().length<12){
   stopReason='no_progress';
   break;
  }
 }
 // A completed code fence is not proof that a model's code actually runs.
 const complete=stopReason==='complete'&&completedCode;
 onEvent({type:'long_done',complete,reason:stopReason,conversation_id:conversationId});
 return {text:accumulated,complete,reason:stopReason,conversation_id:conversationId};
}
