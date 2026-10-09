import {describe,it,expect,vi,afterEach} from 'vitest';
import {createPythonRun} from '../lib/pythonRunner.js';

const workers=[];
class FakeWorker {
  constructor(url,options) {this.url=url;this.options=options;this.events=[];this.terminated=false;workers.push(this);}
  postMessage(value) {this.events.push(value);}
  terminate() {this.terminated=true;}
  deliver(value) {this.onmessage?.({data:value});}
  crash() {this.onerror?.({preventDefault(){}});}
}
afterEach(()=>{vi.unstubAllGlobals();vi.useRealTimers();workers.length=0;});
describe('local Python runner lifecycle',()=>{
  it('executes code in an isolated worker without API calls',async()=>{
    vi.stubGlobal('Worker',FakeWorker);
    const status=[];
    const job=createPythonRun("print(42)",{onStatus:v=>status.push(v)});
    const w=workers[0];
    expect(w.url).toBe('/python-runner.worker.js');
    expect(w.events).toEqual([{type:'start',code:'print(42)'}]);
    w.deliver({type:'ready'});
    w.deliver({type:'output',stream:'stdout',text:'42\n'});
    w.deliver({type:'done',status:'success'});
    await expect(job.promise).resolves.toEqual({status:'success',stdout:'42\n',stderr:''});
    expect(status).toContain('Executing Python…');
    expect(w.terminated).toBe(true);
  });
  it('reports syntax errors without treating them as successful runs',async()=>{
    vi.stubGlobal('Worker',FakeWorker);
    const job=createPythonRun("print(");
    workers[0].deliver({type:'ready'});
    workers[0].deliver({type:'error',message:'SyntaxError: unexpected EOF'});
    expect((await job.promise).status).toBe('error');
  });
  it('stops infinite loops and terminates worker after eight seconds',async()=>{
    vi.useFakeTimers();vi.stubGlobal('Worker',FakeWorker);
    const job=createPythonRun('while True: pass');
    workers[0].deliver({type:'ready'});
    await vi.advanceTimersByTimeAsync(8001);
    const result=await job.promise;
    expect(result.status).toBe('timeout');
    expect(workers[0].terminated).toBe(true);
  });
  it('lets user cancel and avoids dangling execution',async()=>{
    vi.stubGlobal('Worker',FakeWorker);
    const job=createPythonRun('import time');
    job.cancel();
    expect((await job.promise).status).toBe('cancelled');
    expect(workers[0].terminated).toBe(true);
  });
  it('rejects empty and too-long source before making a worker',()=>{
    vi.stubGlobal('Worker',FakeWorker);
    expect(()=>createPythonRun(' ')).toThrow();
    expect(()=>createPythonRun('x'.repeat(20001))).toThrow();
    expect(workers).toHaveLength(0);
  });
  it('returns a clear error when self-hosted Python assets are absent',async()=>{
    vi.stubGlobal('Worker',FakeWorker);
    const job=createPythonRun('print("hi")');
    workers[0].crash();
    const result=await job.promise;
    expect(result.status).toBe('error');
    expect(result.stderr).toMatch(/assets are deployed/);
  });
});