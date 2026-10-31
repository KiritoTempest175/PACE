import {describe,it,expect} from 'vitest';
import {codeOverview} from '../lib/codeOverview.js';
import {isLikelyCodeInput} from '../lib/codingTurns.js';

describe('coding explanation fallback',()=>{
 it('summarizes source without asserting AI validation',()=>{
  const text='import numpy as np\n\ndef linear_regression(X, y):\n    return np.linalg.inv(X.T @ X) @ X.T @ y\n\nprint(linear_regression(X, y))';
  const result=codeOverview([{language:'python',code:text}]);
  expect(result).toContain('linear_regression');
  expect(result).toContain('numpy');
  expect(result).toContain('matrix is singular');
  expect(result).not.toContain('tested successfully');
 });
 it('distinguishes pasted code from regular programming requests',()=>{
  expect(isLikelyCodeInput('import numpy as np\n\ndef regression(X,y):\n    return np.linalg.pinv(X) @ y')).toBe(true);
  expect(isLikelyCodeInput('Please create Python code for linear regression and explain it.')).toBe(false);
 });
});
