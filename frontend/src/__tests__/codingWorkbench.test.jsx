import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import App from '../App.jsx';
import {ThemeProvider} from '../ThemeContext.jsx';

vi.mock('../lib/api.js',()=>({
 json:vi.fn(async path=>{
  if(path==='/conversations')return [{id:'chat-a',title:'Regression example',workspace:'coding'},{id:'chat-b',title:'Pasted source example',workspace:'coding'}];
  if(path==='/conversations/chat-a')return {
   id:'chat-a',workspace:'coding',messages:[
    {id:'u1',role:'user',text:'generate code for linear regression'},
    {id:'a1',role:'assistant',text:'The code is correct and does not contain any errors.'},
    {id:'u2',role:'user',text:'Continue the exact same implementation, do not start over.\nORIGINAL TASK: regression'},
    {id:'a2',role:'assistant',text:'```python filename=main.py\nimport numpy as np\nprint(42)\n```'}
   ]};
  if(path==='/conversations/chat-b')return {
   id:'chat-b',workspace:'coding',messages:[
    {id:'u3',role:'user',text:'Generate linear regression source'},
    {id:'a3',role:'assistant',text:'```python\\nprint(42)\\n```'},
    {id:'u4',role:'user',text:'import numpy as np\\n\\ndef linear_regression(X, y):\\n    return np.linalg.pinv(X) @ y'},
    {id:'a4',role:'assistant',text:'```python\\nimport numpy as np\\ndef linear_regression(X, y):\\n    return np.linalg.pinv(X) @ y\\n```'}
   ]};
  return [];
 }),
 wakeServer:vi.fn().mockResolvedValue({status:'healthy',ai_provider:'huggingface'}),
 streamAnswer:vi.fn()
}));

afterEach(()=>{cleanup();window.history.replaceState(null,'','/');});

describe('coding view regression',()=>{
 it('renders one real request and its code, hiding internal retries and false reviews',async()=>{
  window.history.replaceState(null,'','/coding');
  render(<ThemeProvider><App/></ThemeProvider>);
  fireEvent.click(await screen.findByRole('button',{name:'Regression example'}));
  await waitFor(()=>expect(screen.getByText('Your request')).toBeInTheDocument());
  const explanation=screen.getByRole('region',{name:'AI explanation panel'});
  const code=screen.getByRole('complementary',{name:'Generated code panel'});
  expect(screen.getAllByText('generate code for linear regression')).toHaveLength(1);
  expect(explanation).not.toHaveTextContent('The code is correct');
  expect(explanation).toHaveTextContent('Code overview');
  expect(explanation).not.toHaveTextContent('Code is displayed in the Generated code panel.');
  expect(code).toHaveTextContent('print(42)');
  expect(code).not.toHaveTextContent('No code artifact');
  expect(document.body).not.toHaveTextContent('Continue the exact same implementation');
 });
 it('collapses source pasted as input rather than showing duplicate code inline',async()=>{
  window.history.replaceState(null,'','/coding');
  render(<ThemeProvider><App/></ThemeProvider>);
  fireEvent.click(await screen.findByRole('button',{name:'Pasted source example'}));
  const select=await screen.findByLabelText('View request');
  expect(select).toHaveValue('0');
  const source=screen.getByText(/Submitted source code/);
  expect(source).toBeInTheDocument();
  expect(screen.getByText('View original input')).toBeInTheDocument();
  expect(screen.getByRole('complementary',{name:'Generated code panel'})).toHaveTextContent('np.linalg.pinv');
  fireEvent.change(select,{target:{value:'1'}});
  expect(screen.getByText('Generate linear regression source')).toBeInTheDocument();
  expect(screen.queryByText('View original input')).not.toBeInTheDocument();
 });
});
