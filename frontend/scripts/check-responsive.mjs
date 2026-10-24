import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const origin=process.env.PACE_TEST_ORIGIN || 'http://127.0.0.1:4173';
const routes=['/','/coding','/literacy','/models','/settings','/docs','/privacy','/not-a-real-page'];
const widths=[320,375,768,1024,1440];
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const failures=[];
await fs.mkdir('artifacts/responsive',{recursive:true});
try{
 for(const width of widths){
  const page=await browser.newPage({viewport:{width,height:850},deviceScaleFactor:1});
  const runtimeErrors=[];
  page.on('pageerror',error=>runtimeErrors.push(error.message));
  page.on('console',msg=>{if(msg.type()==='error')runtimeErrors.push(msg.text());});
  for(const route of routes){
   await page.goto(origin+route,{waitUntil:'domcontentloaded'});
   try{await page.locator('#root > *').first().waitFor({state:'attached',timeout:12000});}
   catch(error){failures.push(width+': '+route+' React root did not render: '+runtimeErrors.slice(-3).join(' | '));continue;}
   await page.waitForTimeout(350);
   const result=await page.evaluate(()=>({
    root:document.documentElement.scrollWidth,
    body:document.body.scrollWidth,
    viewport:innerWidth,
    title:document.title,
    horizontal:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)>innerWidth+1
   }));
   if(result.horizontal)failures.push(width+': '+route+' overflow '+result.root+'/'+result.body+' > '+result.viewport);
   if(!result.title.includes(' | PACE'))failures.push(width+': '+route+' missing route title');
   const filename=(route==='/'?'dashboard':route.slice(1).replaceAll('/','-'))+'-'+width+'.png';
   await page.screenshot({path:path.join('artifacts/responsive',filename),fullPage:true});
  }
  await page.goto(origin+'/',{waitUntil:'domcontentloaded'});
  await page.locator('#root > *').first().waitFor({state:'attached',timeout:12000});
  if(width<=700){
   const open=page.getByRole('button',{name:'Open navigation'});
   await open.click();
   const expanded=await open.getAttribute('aria-expanded');
   if(expanded!=='true')failures.push(width+': drawer did not open');
   await page.keyboard.press('Escape');
   if(await open.getAttribute('aria-expanded')!=='false')failures.push(width+': Escape did not close drawer');
  }
  await page.close();
 }
}finally{await browser.close();}
if(failures.length){console.error(failures.join('\n'));process.exitCode=1;}
else console.log('Responsive navigation and overflow checks passed on '+widths.join(', ')+' px.');
