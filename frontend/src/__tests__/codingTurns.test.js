import {describe,it,expect} from 'vitest';
import {codingTurns,isInternalContinuation} from '../lib/codingTurns.js';

describe('coding workbench request grouping',()=>{
 it('keeps genuine requests distinct without showing continuation requests',()=>{
  const messages=[
   {role:'user',id:'1',text:'Generate linear regression in Python'},
   {role:'assistant',id:'2',text:'```python filename=main.py\nimport numpy as np\n```'},
   {role:'user',id:'3',text:'Generate logistic regression in Python'},
   {role:'assistant',id:'4',text:'```python filename=main.py\nprint("logistic")\n```'}
  ];
  const turns=codingTurns(messages);
  expect(turns).toHaveLength(2);
  expect(turns[0].request).toMatch(/linear/);
  expect(turns[1].response).toContain('logistic');
 });
 it('discards prose-only review and groups follow-up code under original task',()=>{
  const messages=[
   {role:'user',text:'generate code for linear regression'},
   {role:'assistant',text:'The code is correct and does not contain any errors.'},
   {role:'user',text:'Continue the exact same implementation, do not start over.\nORIGINAL TASK: linear regression'},
   {role:'assistant',text:'```python\nfrom sklearn.linear_model import LinearRegression\nmodel = LinearRegression()\n```'}
  ];
  const turns=codingTurns(messages);
  expect(turns).toHaveLength(1);
  expect(turns[0].request).toBe('generate code for linear regression');
  expect(turns[0].response).not.toContain('code is correct');
  expect(turns[0].response).toContain('LinearRegression');
 });
 it('recognizes manual continuation from earlier web versions',()=>{
  expect(isInternalContinuation('Continue the unfinished code from exactly where it stopped.')).toBe(true);
  expect(isInternalContinuation('Continue exactly where the preceding response ended')).toBe(true);
 });
});
