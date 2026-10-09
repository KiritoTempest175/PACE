import {describe,it,expect,vi} from 'vitest';
import {render,screen,fireEvent} from '@testing-library/react';
import {Button,Tabs,Modal} from '../components/ui.jsx';

describe('UI building blocks',()=>{
  it('button follows disabled semantics',()=>{render(<Button disabled>Run</Button>);expect(screen.getByRole('button',{name:'Run'})).toBeDisabled();});
  it('tabs expose aria selection',()=>{const onChange=vi.fn();render(<Tabs label="Mode" value="fast" onChange={onChange} items={[{value:'fast',label:'Fast'},{value:'pro',label:'Review'}]}/>);fireEvent.click(screen.getByRole('tab',{name:'Review'}));expect(onChange).toHaveBeenCalledWith('pro');});
  it('modal supports Escape dismissal',()=>{const close=vi.fn();render(<Modal open title="Options" onClose={close}><p>Options body</p></Modal>);expect(screen.getByRole('dialog',{name:'Options'})).toBeVisible();fireEvent.keyDown(document,{key:'Escape'});expect(close).toHaveBeenCalled();});
});
