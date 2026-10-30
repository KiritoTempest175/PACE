import {describe,it,expect} from 'vitest';
import {parseGeneratedResponse} from '../lib/parseGeneratedResponse.js';

describe('generation artifacts',()=>{
 it('separates explanation and multiple named source files',()=>{
  const raw='Here is the plan.\\n\\n```python filename=main.py\\nprint(42)\\n```\\nUse this for testing.\\n```js filename=client.js\\nconsole.log(1)\\n```';
  const parsed=parseGeneratedResponse(raw.replaceAll('\\n','\n'));
  expect(parsed.explanation).toContain('Here is the plan.');
  expect(parsed.explanation).toContain('Use this for testing.');
  expect(parsed.explanation).not.toContain('print(42)');
  expect(parsed.files).toHaveLength(2);
  expect(parsed.files[0]).toMatchObject({language:'python',filename:'main.py',code:'print(42)\n',incomplete:false});
  expect(parsed.files[1].filename).toBe('client.js');
 });
 it('preserves streamed partial code and marks it incomplete',()=>{
  const result=parseGeneratedResponse('Part one\n```python\ndef example():\n    return 1');
  expect(result.explanation).toBe('Part one');
  expect(result.files[0]).toMatchObject({code:'def example():\n    return 1',incomplete:true});
 });
 it('keeps ordinary prose in the explanation panel',()=>{
  const result=parseGeneratedResponse('A neural network learns weights from data.');
  expect(result.files).toHaveLength(0);
  expect(result.explanation).toMatch(/weights/);
 });
 it('detects stand-alone un-fenced code',()=>{
  const result=parseGeneratedResponse('import os\ndef demo():\n  x = 1\n  return x\n');
  expect(result.files).toHaveLength(1);
  expect(result.explanation).toBe('');
 });
});
