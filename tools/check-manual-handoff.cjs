/* Browser contract test. A separate synthetic test driver supplies manual UI actions;
   this is NOT an attended human session or a staff-time measurement. */
const {chromium}=require('playwright');
const {createOperator}=require('./fixture-operator.cjs');
const fs=require('fs'),path=require('path'),assert=require('assert');
(async()=>{
 const events=[];let browser;
 try{
  browser=await chromium.launch({headless:true,chromiumSandbox:true,...(process.env.BROWSER_CHANNEL?{channel:process.env.BROWSER_CHANNEL}:{}),...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
  const context=await browser.newContext();const page=await context.newPage();
  await context.route('**/*',r=>{const u=new URL(r.request().url());return u.hostname==='localhost'&&u.port==='4309'&&u.pathname!=='/harness'?r.continue():r.abort()});
  await page.goto('http://localhost:4309/?case=bookkeeper-deposit&account=ledger-business&operator=manual');
  await page.locator('#scope').selectOption('invoice-107');
  const operator=createOperator('manual',(kind,data)=>events.push({kind,...data}));
  const signIn=operator.perform(page,'signin');
  await page.waitForTimeout(100);assert.equal(events.filter(e=>e.responseObserved).length,0);
  await page.locator('#signin').click();assert.equal((await signIn).status,'challenge');
  const challenge=operator.perform(page,'challenge');
  await page.waitForTimeout(100);assert.equal(events.filter(e=>e.responseObserved).length,1);
  await page.locator('#challenge').click();await challenge;
  const identityResponse=page.waitForResponse(r=>r.url().endsWith('/ui')&&r.request().postDataJSON()?.action==='identity');
  await page.locator('#identity').click();const identity=await (await identityResponse).json();
  assert.equal(identity.status,'verified');assert.equal(identity.account,'ledger-business');assert.equal(identity.scope,'invoice-107');
  assert.equal(events.filter(e=>e.kind==='manual-operator-duration'&&e.responseObserved).length,2);
  const out=path.resolve(__dirname,'../artifacts');fs.mkdirSync(out,{recursive:true});await page.screenshot({path:path.join(out,'manual-handoff-contract.png')});
  fs.writeFileSync(path.join(out,'manual-handoff-contract.json'),JSON.stringify({verified:true,mode:'manual adapter with separate synthetic test driver',attendedHuman:false,checks:['waits before sign-in','waits before challenge','fresh authorized identity after handback'],events},null,2));
  console.log('Manual handoff browser contract passed; no attended human session claimed.');await context.close();
 }finally{if(browser)await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
