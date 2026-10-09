/* PACE local Python execution (classic Web Worker).
 * This is a local convenience runtime, NOT a hardened hostile-code sandbox.
 * Keep all user code off the API; terminating the Worker bounds CPU time.
 */
let interpreter = null;
const RUNTIME = new URL("./pyodide/", self.location.href).href;
const MAX_OUTPUT = 64 * 1024;
let outputChars = 0;
let truncated = false;
function send(type, data={}) { self.postMessage({type, ...data}); }
function output(stream, text) {
  const chunk = String(text ?? "");
  const available = MAX_OUTPUT - outputChars;
  if (available > 0) {
    const printed = chunk.slice(0, available);
    outputChars += printed.length;
    send("output", {stream, text: printed + "\n"});
  } else if (!truncated) {
    truncated = true;
    send("output", {stream:"stderr", text:"\n[Output truncated at 64 KiB]\n"});
  }
}
self.onmessage = async ({data}) => {
  if (data?.type !== "start" || interpreter) return;
  try {
    send("progress", {message:"Loading local Python runtime…"});
    importScripts(new URL("pyodide.js", RUNTIME).href);
    interpreter = await loadPyodide({indexURL:RUNTIME});
    interpreter.setStdout({batched:(text)=>output("stdout",text)});
    interpreter.setStderr({batched:(text)=>output("stderr",text)});
    send("ready");
    // Do not keep a running Python interpreter between unrelated runs.
    // One worker, one source file, no API/session credentials sent to worker.
    const code = String(data.code || "");
    await interpreter.runPythonAsync(code);
    send("done", {status:"success"});
  } catch (error) {
    const message = typeof error?.message === "string" ? error.message : "Python execution failed";
    send("error", {message:message.slice(0,4000)});
  }
};