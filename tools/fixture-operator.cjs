/* Separate fixture operator adapter. Worker supplies a requested UI handoff, never a challenge response. */
const controls=new Set(['signin','challenge','decide','advance','choose-job','review-assessment']);
const actions={signin:'signin',challenge:'signin',decide:'decide-pickup',advance:'advance','choose-job':'choose-job','review-assessment':'review-assessment'};
function createOperator(mode,event){
 if(!['scripted','manual'].includes(mode))throw new Error('Operator mode must be scripted or manual');
 async function perform(page,id){
  if(!controls.has(id))throw new Error('Control outside operator scope');
  const started=performance.now();let completed=false;
  event('operator-handoff-requested',{control:id,actor:mode==='manual'?'human operator':'fixture operator'});
  try{
   const pending=page.waitForResponse(r=>r.url().endsWith('/ui')&&r.request().method()==='POST'&&r.request().postDataJSON().action===actions[id],{timeout:mode==='manual'?300000:30000});
   if(mode==='scripted')await page.locator('#'+id).click();
   else console.log('MANUAL HANDOFF: use '+id+' in '+page.url());
   const response=await pending;const result=await response.json();completed=true;return result;
  }finally{event(mode==='manual'?'manual-operator-duration':'scripted-operator-duration',{actor:mode==='manual'?'human operator':'fixture operator',control:id,durationMilliseconds:performance.now()-started,responseObserved:completed,measurement:mode==='manual'?'handoff wall time, not active staff time':'browser click through response parsing; excludes human decision time'});}
 }
 async function account(page,value){if(mode==='scripted')await page.locator('#account').fill(value);else console.log('MANUAL HANDOFF: switch account to '+value+' before signing in.');}
 return {mode,controls,perform,account};
}
module.exports={createOperator};
