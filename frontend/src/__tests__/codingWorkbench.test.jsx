import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup,within} from '@testing-library/react';
import App from '../App.jsx';
import {ThemeProvider} from '../ThemeContext.jsx';

vi.mock('../lib/api.js',()=>({
 json:vi.fn(async path=>{
  if(path==='/conversations')return [{id:'chat-a',title:'Regression example',workspace:'coding'}];
  if(path==='/conversations/chat-a')return {
   id:'chat-a',workspace:'coding',messages:[
    {id:'u1',role:'user',text:'generate code for linear regression'},
    {id:'a1',role:'assistant',text:'The code is correct and does not contain any errors.'},
    {id:'u2',role:'user',text:'Continue the exact same implementation, do not start over.\nORIGINAL TASK: regression'},
    {id:'a2',role:'assistant',text:'```python filename=main.py\nimport numpy as np\nprint(42)\n```'}
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
  await waitFor(()=>expect(screen.getByText('Selected request')).toBeInTheDocument());
  const explanation=screen.getByRole('region',{name:'AI explanation panel'});
  const code=screen.getByRole('complementary',{name:'Generated code panel'});
  expect(screen.getAllByText('generate code for linear regression')).toHaveLength(1);
  expect(explanation).not.toHaveTextContent('The code is correct');
  expect(code).toHaveTextContent('print(42)');
  expect(code).not.toHaveTextContent('No code artifact');
  expect(document.body).not.toHaveTextContent('Continue the exact same implementation');
 });
});
