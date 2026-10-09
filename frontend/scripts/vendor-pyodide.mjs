/* Fetch pinned Pyodide runtime assets at build/dev startup.
   Ships Python locally with the website and Windows installer: no runtime CDN.
   Apache-2.0 Pyodide license: https://github.com/pyodide/pyodide
 */
import {mkdir, readFile, rename, rm, stat, writeFile} from 'node:fs/promises';
import {join, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const ROOT=join(dirname(fileURLToPath(import.meta.url)),'..','public','pyodide');
const VERSION="0.29.5";
const BASE="https://cdn.jsdelivr.net/pyodide/v"+VERSION+"/full/";
const FILES={
  "pyodide.js":5000,
  "pyodide.asm.js":10000,
  "pyodide.asm.wasm":1000000,
  "python_stdlib.zip":1000000,
  "pyodide-lock.json":1000,
};
async function valid(name,minimum) {
  try {return (await stat(join(ROOT,name))).size >= minimum;} catch {return false;}
}
async function download(name, minimum) {
  if (await valid(name,minimum)) {console.log("Pyodide cached:",name);return;}
  const path=join(ROOT,name),tmp=path+".partial";
  for(let attempt=1;attempt<=3;attempt++){
    try {
      const response=await fetch(BASE+name,{signal:AbortSignal.timeout(120000)});
      if(!response.ok) throw Error("HTTP "+response.status+" for "+name);
      const data=Buffer.from(await response.arrayBuffer());
      if(data.length<minimum || data.length>100*1024*1024) throw Error("Unexpected asset size for "+name+": "+data.length);
      await writeFile(tmp,data);await rename(tmp,path);
      console.log("Pinned Pyodide "+VERSION+": "+name+" ("+data.length+" bytes)");
      return;
    } catch(error) {
      await rm(tmp,{force:true});
      if(attempt===3) throw error;
      await new Promise(resolve=>setTimeout(resolve,attempt*1500));
    }
  }
}
await mkdir(ROOT,{recursive:true});
await Promise.all(Object.entries(FILES).map(([name,bytes])=>download(name,bytes)));
const manifest={version:VERSION,artifacts:{}};
for(const name of Object.keys(FILES)){
  const data=await readFile(join(ROOT,name));
  manifest.artifacts[name]={bytes:data.length,sha256:createHash("sha256").update(data).digest("hex")};
}
await writeFile(join(ROOT,'manifest.json'),JSON.stringify(manifest,null,2)+"\n");
console.log("Self-hosted Python runtime assets verified.");
