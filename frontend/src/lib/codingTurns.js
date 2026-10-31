import {parseGeneratedResponse} from './parseGeneratedResponse.js';

// The deployed backend currently stores every continuation as an ordinary
// chat turn. Build a useful UI view without modifying or deleting stored data.
export function isInternalContinuation(text='') {
 const value=String(text).trim();
 return value.startsWith('Continue the exact same implementation, do not start over.')
   || value.startsWith('Continue the unfinished code from exactly where it stopped.')
   || value.startsWith('Continue exactly where the preceding response ended');
}

export function removeOverlap(previous='', next='') {
 const older=String(previous);
 const incoming=String(next);
 for(let size=Math.min(1600,older.length,incoming.length);size>=16;size--){
  if(older.endsWith(incoming.slice(0,size)))return incoming.slice(size);
 }
 return incoming;
}

export function codingTurns(messages=[]) {
 const turns=[];
 let turn=null;
 let continuation=false;
 for(const message of messages){
  if(message.role==='user'){
   continuation=isInternalContinuation(message.text);
   if(!continuation){
    turn={id:message.id||'turn-'+turns.length,request:message.text||'',response:'',incomplete:false};
    turns.push(turn);
   }
  }else if(message.role==='assistant'&&turn){
   const text=message.text||'';
   if(!text.trim())continue;
   // A follow-up that only claims that code is correct is not a code segment.
   if(continuation&&turn.response&&parseGeneratedResponse(turn.response).files.length
     &&!parseGeneratedResponse(text).files.length
     &&!/^\s*(?:import |from |def |class |function |const |let |var |#include)/m.test(text))continue;
   if(continuation&&turn.response&&!parseGeneratedResponse(turn.response).files.length
     &&parseGeneratedResponse(text).files.length){
    turn.response=text; // Replace earlier non-code reviewer commentary.
   }else{
    turn.response+=removeOverlap(turn.response,text);
   }
   turn.incomplete=Boolean(message.incomplete);
  }
 }
 return turns;
}
