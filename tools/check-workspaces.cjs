/* Live synthetic UI checks and video: filtering is local and never mutates records. */
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),cp=require('child_process'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts','workspaces');
const apps=JSON.parse(fs.readFileSync(path.join(root,'contracts/apps.json')));
const cases=JSON.parse(fs.readFileSync(path.join(root,'contracts/cases.json')));
(async()=>{
 fs.mkdirSync(out,{recursive:true});const started=new Date(),results=[],videos=[];
 const browser=await chromium.launch({headless:true,chromiumSandbox:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:process.env.BROWSER_CHANNEL?{channel:process.env.BROWSER_CHANNEL}:{})});
 try{
  for(const app of apps){
   const caseId=cases.find(c=>JSON.parse(fs.readFileSync(path.join(root,'workflows',c,'fixtures.json'))).source===app)||'consultancy-contract';
   const fixture=JSON.parse(fs.readFileSync(path.join(root,'workflows',caseId,'fixtures.json')));
   const port=JSON.parse(fs.readFileSync(path.join(root,'apps',app,'defaults.json'))).port;
   const context=await browser.newContext({viewport:{width:1280,height:960},recordVideo:{dir:out,size:{width:1280,height:960}}});
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await context.route('**/*',r=>{const u=new URL(r.request().url());return u.hostname==='localhost'&&String(port)===u.port?r.continue():r.abort()});
   try{
    await page.goto(`http://localhost:${port}/?case=${caseId}&account=${encodeURIComponent(fixture.accounts[app])}`);
    assert.equal(await page.locator('.workspace-hero').count(),1);
    const scopes=await page.locator('#scope option').evaluateAll(xs=>xs.map(x=>x.value).filter(Boolean));if(scopes.length)await page.locator('#scope').selectOption(scopes[0]);
    async function click(id){const response=page.waitForResponse(r=>r.url().endsWith('/ui')&&r.request().method()==='POST');await page.locator('#'+id).click();return(await response).json()}
    await click('signin');const identity=await click('identity');assert.equal(identity.status,'verified');
    const before=await click('read');assert(!before.error,JSON.stringify(before));
    const rows=page.locator('#sheet-view tr').filter({has:page.locator('td')});const total=await rows.count();
    let requests=0;const count=()=>requests++;page.on('request',count);
    await page.locator('#record-filter').fill('NO-MATCH-TEST-71C9');
    if(total){assert.equal(await rows.filter({visible:true}).count(),0);assert(await page.locator('#record-empty').isVisible());}
    await page.locator('#record-filter').fill('');
    assert.equal(await rows.filter({visible:true}).count(),total);assert.equal(requests,0,'View filtering must not send requests');page.off('request',count);
    const after=await click('read');assert.deepEqual(after.rows??after.sheets??after.messages, before.rows??before.sheets??before.messages);
    await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(600);
    await page.screenshot({path:path.join(out,app+'-desktop.png'),fullPage:true});
    await page.locator('a[href="#records-panel"]').click();await page.waitForTimeout(250);
    assert.equal(await page.evaluate(()=>location.hash),'#records-panel');
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,app+' mobile overflow');
    await page.waitForTimeout(600);
    await page.screenshot({path:path.join(out,app+'-mobile.png'),fullPage:true});
    assert.deepEqual(errors,[]);results.push({app,case:caseId,rows:total,identityVerified:true,filterNoNetwork:true,sourceUnchanged:true,mobileOverflow:false});
   }finally{const video=page.video();await context.close();videos.push(await video.path())}
  }
 }finally{await browser.close()}
 const concat=path.join(out,'clips.txt');fs.writeFileSync(concat,videos.map(p=>`file '${path.basename(p)}'`).join('\n'));
 cp.execFileSync('ffmpeg',['-y','-f','concat','-safe','0','-i',concat,'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',path.join(out,'workspace-tour.mp4')],{stdio:'pipe'});
 const seconds=Number(cp.execFileSync('ffprobe',['-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',path.join(out,'workspace-tour.mp4')],{encoding:'utf8'}).trim());
 const evidence={passed:true,workingTreeClean:!cp.execFileSync('git',['status','--porcelain'],{cwd:root,encoding:'utf8'}).trim(),sourceCommit:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),runner:process.env.RUNNER_NAME||'local-preflight',runId:process.env.GITHUB_RUN_ID||null,startedAt:started.toISOString(),finishedAt:new Date().toISOString(),elapsedSeconds:(Date.now()-started)/1000,videoSeconds:seconds,results};
 fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(evidence,null,2));console.log(JSON.stringify(evidence));
})().catch(e=>{console.error(e);process.exitCode=1});
