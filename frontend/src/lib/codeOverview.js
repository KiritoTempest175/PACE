// Factual, rule-based summary for historic model responses containing code but
// no explanation. This is NOT a second AI response or a claim of validation.
const languageNames={python:'Python',py:'Python',js:'JavaScript',javascript:'JavaScript',ts:'TypeScript',typescript:'TypeScript',cpp:'C++',c:'C',java:'Java',go:'Go',rust:'Rust',sql:'SQL',bash:'shell'};
const uniq=values=>[...new Set(values)];
export function codeOverview(files=[]){
 const complete=files.filter(f=>f.code?.trim());
 if(!complete.length)return null;
 const names=uniq(complete.map(f=>languageNames[f.language?.toLowerCase()]||f.language||'source code'));
 const functions=uniq(complete.flatMap(f=>[...f.code.matchAll(/(?:^|\n)\s*(?:async\s+def|def|function|func|fn)\s+([\w]+)\s*\(/g)].map(x=>x[1]))).slice(0,5);
 const imports=uniq(complete.flatMap(f=>[...f.code.matchAll(/(?:^|\n)\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))/g)].map(m=>(m[1]||m[2]).split('.')[0]))).slice(0,5);
 const descriptions=[];
 descriptions.push(complete.length===1?`The generated file contains ${names.join(', ')} source code.`:`The response contains ${complete.length} source-code blocks in ${names.join(', ')}.`);
 if(functions.length)descriptions.push(`It defines ${functions.map(f=>'`'+f+'`').join(', ')}.`);
 if(imports.length)descriptions.push(`It imports ${imports.map(f=>'`'+f+'`').join(', ')}.`);
 const all=complete.map(f=>f.code).join('\n');
 if(/np\.linalg\.inv\s*\(/.test(all))descriptions.push('It uses a matrix inverse; this can fail when the matrix is singular.');
 else if(/np\.linalg\.(?:pinv|lstsq)\s*\(/.test(all))descriptions.push('It uses a NumPy linear-algebra solver.');
 if(/(?:LinearRegression\s*\(|linear_regression\s*\()/i.test(all))descriptions.push('It includes a linear-regression implementation or example.');
 if(/(?:print\s*\(|console\.log\s*\()/i.test(all))descriptions.push('It prints output or an example result.');
 return descriptions.join(' ');
}
