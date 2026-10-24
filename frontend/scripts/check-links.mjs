import fs from 'node:fs';
import path from 'node:path';
const allowed=new Set(['/','/dashboard','/coding','/literacy','/models','/settings','/docs','/privacy']);
const files=['src/App.jsx','src/components/InfoPages.jsx','src/components/ModelsPage.jsx','index.html'];
const href=/\bhref=["']([^"']+)["']/g;
let links=0;const failures=[];
for(const f of files){const text=fs.readFileSync(path.join(process.cwd(),f),'utf8');for(const match of text.matchAll(href)){const url=match[1];links++;if(url.startsWith('/')&&!allowed.has(url)&&!fs.existsSync(path.join('public',url.slice(1))))failures.push(f+': '+url);if(url.startsWith('javascript:'))failures.push(f+': unsafe link');}}
if(failures.length){console.error('Broken literal local links:\n'+failures.join('\n'));process.exit(1);}
console.log('Checked '+links+' literal internal/external href values; remote external URL availability is not validated.');
