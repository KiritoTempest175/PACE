import {describe,it,expect} from 'vitest';
import {activeServiceLabel,activeServiceOptions} from '../lib/activeService.js';
describe('desktop active provider selector',()=>{
 it('distinguishes local and hosted providers',()=>{
  expect(activeServiceLabel({provider:'ollama'})).toBe('Local · Ollama');
  expect(activeServiceLabel({provider:'local'})).toBe('Local · PACE model');
  expect(activeServiceLabel({connectionKind:'hosted',provider:'huggingface'})).toContain('Hosted PACE API');
 });
 it('shows selected API without leaking its credential',()=>{
  const model={id:'123',provider:'openrouter',name:'Fast Model',hasKey:true,key:'SECRET'};
  expect(activeServiceLabel({activeCustom:model})).toContain('OPENROUTER API · Fast Model');
  const options=activeServiceOptions([model,{id:'456',provider:'openai',name:'No key',hasKey:false}]);
  expect(options).toHaveLength(3);
  expect(options[2].value).toBe('provider:123');
  expect(JSON.stringify(options)).not.toContain('SECRET');
 });
});
