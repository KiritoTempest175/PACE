/** Describe the actual provider destination, not merely a generic Local/Cloud badge. */
export function activeServiceLabel({activeCustom=null,connectionKind='local',provider='disabled'}={}){
 if(activeCustom)return 'Direct '+String(activeCustom.provider||'External').toUpperCase()+' API · '+String(activeCustom.name||activeCustom.modelId||'Custom');
 if(connectionKind==='hosted')return 'Hosted PACE API'+(provider&&provider!=='disabled'?' · '+provider:'');
 if(provider==='ollama')return 'Local · Ollama';
 if(provider==='local')return 'Local · PACE model';
 return 'Local · No model configured';
}
export function activeServiceOptions(models=[]){
 return [
  {value:'local',label:'Local — Ollama / PACE'},
  {value:'hosted',label:'Hosted — PACE API'},
  ...models.filter(model=>model.hasKey).map(model=>({value:'provider:'+model.id,label:'API — '+model.name+' ('+model.provider+')'}))
 ];
}
