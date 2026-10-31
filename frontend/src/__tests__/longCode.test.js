import {describe,it,expect,vi} from 'vitest';
import {generateLongCode,removeRepeatedPrefix,needsCodeContinuation} from '../lib/longCode.js';

describe('bounded long-code streaming',()=>{
 it('recognizes incomplete fenced responses',()=>{
  expect(needsCodeContinuation('```python\nprint(1)')).toBe(true);
  expect(needsCodeContinuation('```python\nprint(1)\n```')).toBe(false);
 });
 it('strips a substantial repeated continuation prefix',()=>{
  const tail='    a_very_long_statement = compute_value_from_source()\n';
  expect(removeRepeatedPrefix('header\n'+tail,tail+'print(42)')).toBe('print(42)');
 });
 it('continues after the model emits partial tokens and then fails',async()=>{
  const input='Create a long Python function';
  const first='```python\ndef sample():\n    a_very_long_statement = compute_value_from_source()\n';
  const second='    a_very_long_statement = compute_value_from_source()\n    return 42\n```';
  let calls=0;const events=[];
  const sender=vi.fn(async (body,emit)=>{
   calls++;
   emit({type:'init',conversation_id:'chat-123'});
   emit({type:'token',content:calls===1?first:second});
   if(calls===1)throw new Error('Hosted token budget reached');
   emit({type:'done'});
  });
  const result=await generateLongCode({text:input,mode:'coding',speed_mode:'fast'},evt=>events.push(evt),undefined,{send:sender,maxRounds:4});
  expect(calls).toBe(2);
  expect(sender.mock.calls[1][0].text).toContain('Continue ONLY the unfinished code');
  expect(result.complete).toBe(true);
  expect(result.text).toContain('return 42');
  expect((result.text.match(/a_very_long_statement/g)||[])).toHaveLength(1);
 });
 it('stops at a bounded limit and reports incomplete rather than success',async()=>{
  const sender=vi.fn(async (body,emit)=>{
   emit({type:'token',content:'```python\n'+('x=1\n'.repeat(35))});
   throw new Error('Budget reached');
  });
  const events=[];
  const result=await generateLongCode({text:'Make a long program',mode:'coding'},evt=>events.push(evt),undefined,{send:sender,maxRounds:2});
  expect(result.complete).toBe(false);
  expect(result.reason).toBe('repeated_content');
  expect(events.at(-1)).toMatchObject({type:'long_done',complete:false});
 });
 it('does not show an unverified prose-only review as a code artifact',async()=>{
  let count=0;
  const events=[];
  const sender=vi.fn(async (body,emit)=>{
   count++;
   emit({type:'init',conversation_id:'chat-review'});
   emit({type:'token',content:count===1?'The code is correct and does not contain any errors.':'```python\nprint(42)\n```'});
   emit({type:'done'});
  });
  const result=await generateLongCode({text:'generate code for linear regression',mode:'coding',speed_mode:'pro'},e=>events.push(e),undefined,{send:sender});
  expect(count).toBe(2);
  expect(sender.mock.calls[1][0].speed_mode).toBe('fast');
  expect(result.complete).toBe(true);
  expect(result.text).not.toContain('The code is correct');
  expect(result.text).toContain('print(42)');
 });
 it('surfaces a provider error that produces no text',async()=>{
  await expect(generateLongCode({text:'Test',mode:'coding'},()=>{},undefined,{send:async()=>{throw new Error('quota exceeded');}})).rejects.toThrow('quota exceeded');
 });
});
