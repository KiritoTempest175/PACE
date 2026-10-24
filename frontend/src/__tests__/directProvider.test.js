import {describe,it,expect,vi,beforeEach} from 'vitest';
import {directGenerate} from '../lib/directProvider.js';
const model={provider:'openai',baseUrl:'https://api.openai.com/v1',modelId:'example-model',key:'test-only-key'};
beforeEach(()=>{vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({choices:[{message:{content:'Answer'}}]})})));});
describe('direct provider routing',()=>{
 it('Fast performs exactly one direct call',async()=>{
  const reply=await directGenerate(model,'Explain programming','fast');
  expect(reply).toBe('Answer');expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch.mock.calls[0][0]).toBe('https://api.openai.com/v1/chat/completions');
  expect(fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer test-only-key');
 });
 it('Pro explicitly runs actor then critic review',async()=>{
  const stages=[];await directGenerate(model,'Explain programming','pro',{onStage:stage=>stages.push(stage)});
  expect(stages).toEqual(['actor','critic']);expect(fetch).toHaveBeenCalledTimes(2);
  expect(JSON.parse(fetch.mock.calls[1][1].body).messages[0].content).toContain('DRAFT:');
 });
});
