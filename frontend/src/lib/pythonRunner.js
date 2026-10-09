/* Local Python execution controller shared by web and Tauri.
   A worker never receives PACE authentication headers or access tokens. */
export const PYTHON_MAX_SOURCE = 20000;
export const PYTHON_MAX_OUTPUT = 64 * 1024;
const PYTHON_BOOT_MS = 120000;
const PYTHON_RUN_MS = 8000;

export function createPythonRun(code, {onStatus = () => {}} = {}) {
  if (typeof code !== 'string' || !code.trim() || code.length > PYTHON_MAX_SOURCE) {
    throw new Error("Enter Python source code (maximum 20,000 characters).");
  }
  const worker = new Worker('/python-runner.worker.js', {name:'pace-local-python'});
  let timer;
  let settled = false;
  let phase = "loading";
  let stdout = "";
  let stderr = "";
  let truncated = false;
  let finish;
  const promise = new Promise(resolve => { finish = resolve; });
  const stop = (status, message = "") => {
    if (settled) return;
    settled = true;
    clearTimeout(timer);
    worker.terminate();
    if (message) stderr += (stderr ? "\n" : "") + message;
    finish({status, stdout, stderr});
  };
  const clip = (value, extra) => {
    const available = PYTHON_MAX_OUTPUT - value.length;
    if (available <= 0) {
      if (!truncated) { truncated=true; stderr+="\n[Output limit reached]\n"; }
      return value;
    }
    return value + String(extra).slice(0,available);
  };
  timer = setTimeout(() => stop("timeout","Python runtime could not load in 120 seconds."), PYTHON_BOOT_MS);
  onStatus("Loading local Python runtime…");
  worker.onmessage = ({data}) => {
    if (settled) return;
    if (data?.type === 'progress') { onStatus(data.message); return; }
    if (data?.type === 'ready') {
      phase="executing";
      clearTimeout(timer);
      timer=setTimeout(() => stop("timeout","Execution exceeded 8 seconds and was stopped."), PYTHON_RUN_MS);
      onStatus("Executing Python…");
      return;
    }
    if (data?.type === 'output') {
      if (data.stream === 'stdout') stdout=clip(stdout,data.text);
      else stderr=clip(stderr,data.text);
    }
    if (data?.type === 'done') stop("success");
    if (data?.type === 'error') stop("error",data.message||"Python execution failed.");
  };
  worker.onerror = event => {
    event.preventDefault?.();
    stop("error",phase === "loading"
      ? "Local Python runtime could not load. Check that /pyodide/ assets are deployed."
      : "The Python worker stopped unexpectedly.");
  };
  try { worker.postMessage({type:'start',code}); }
  catch (error) { stop("error",String(error.message||error)); }
  return {promise, cancel:()=>stop("cancelled","Execution cancelled by user.")};
}
