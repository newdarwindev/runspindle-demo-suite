/* Bounded local QA only. No workflow runs, external requests, services or schedules. */
'use strict';
const fs = require('fs');
const path = require('path');
const http = require('http');
const assert = require('assert/strict');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '..');
const docs = path.dirname(root);
const projectPath = '/runspindle-demo-suite/';
const portfolioPath = `${projectPath}portfolio/`;
const output = path.resolve(process.env.PORTFOLIO_QA_DIR || '/tmp/runspindle-portfolio-qa');
const runs = JSON.parse(fs.readFileSync(path.join(root, 'data/runs.json')));
const release = JSON.parse(fs.readFileSync(path.join(root, 'release.json')));
const expectedClips = runs.reduce((total, run) => total + run.media.length, 0);
const types = {'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.webm':'video/webm','.png':'image/png','.jpg':'image/jpeg','.vtt':'text/vtt'};
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://localhost').pathname;
  if (pathname !== projectPath && !pathname.startsWith(portfolioPath)) {
    res.writeHead(404).end(); return;
  }
  const relative = decodeURIComponent(pathname.slice(portfolioPath.length)) || 'index.html';
  const file = pathname === projectPath ? path.join(docs, 'index.html') : path.resolve(root, relative);
  if (pathname !== projectPath && !file.startsWith(root + path.sep)) {
    res.writeHead(403).end(); return;
  }
  fs.readFile(file, (error, data) => {
    if (error) { res.writeHead(404).end(); return; }
    res.writeHead(200, {'Content-Type':types[path.extname(file)] || 'application/octet-stream'});
    res.end(data);
  });
});
const getStatus = url => new Promise((resolve, reject) => {
  http.get(url, response => { response.resume(); response.on('end', () => resolve(response.statusCode)); }).on('error', reject);
});
(async () => {
  let browser;
  try {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const origin = `http://127.0.0.1:${server.address().port}`;
    const projectURL = origin + projectPath;
    const portfolioURL = origin + portfolioPath;
    browser = await chromium.launch({headless:true, chromiumSandbox:true, ...(process.env.BROWSER_CHANNEL ? {channel:process.env.BROWSER_CHANNEL} : {})});
    let page = await browser.newPage({viewport:{width:1440,height:1100}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
    await page.goto(projectURL);
    await page.waitForURL(portfolioURL);
    await page.waitForFunction(() => document.querySelectorAll('.controls:not([hidden])').length === 7);
    assert.equal(await page.title(), 'Seven workflows, visible evidence · Runspindle demo portfolio');
    const clips = [];
    for (const run of runs) {
      const card = page.locator(`#${run.case}`);
      for (let i = 0; i < run.media.length; i++) {
        await card.locator('.clip-select').selectOption(String(i));
        const result = await card.locator('video').evaluate(async video => {
          video.load();
          await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => reject(Error('Video metadata timeout')), 10000);
            video.addEventListener('loadedmetadata', () => { clearTimeout(timeout); resolve(); }, {once:true});
            video.addEventListener('error', () => { clearTimeout(timeout); reject(Error('Video failed to load')); }, {once:true});
          });
          await video.play();
          await new Promise(resolve => setTimeout(resolve, 160));
          const result = {duration:video.duration, played:video.currentTime > 0, speed:video.playbackRate, source:video.currentSrc};
          video.pause();
          return result;
        });
        assert(result.played, `${run.case} capture ${i+1} did not play`);
        assert.equal(result.speed, .25);
        assert(Math.abs(result.duration - run.media[i].durationSeconds) < .05);
        assert.equal(result.source, new URL(`media/${run.runId}/${run.media[i].clip}`, portfolioURL).href);
        clips.push({case:run.case, capture:i+1, duration:result.duration, played:true});
      }
      // Repeated replay and speed changes must retain the selected capture.
      await card.locator('.speed-select').selectOption('0.5');
      await card.locator('.replay').click();
      await card.locator('.replay').click();
      assert.equal(await card.locator('video').evaluate(v => v.playbackRate), .5);
      await card.locator('video').evaluate(v => v.pause());
      await card.locator('.evidence summary').click();
      assert(await card.locator('.result-values').isVisible());
      await card.locator('.evidence summary').click();
      await card.locator('.speed-select').selectOption('0.25');
      const longest = run.media.reduce((a, m, i) => m.durationSeconds > run.media[a].durationSeconds ? i : a, 0);
      await card.locator('.clip-select').selectOption(String(longest));
    }
    const links = [...new Set(await page.locator('a[href]').evaluateAll(links => links.map(a => a.href)))].filter(url => new URL(url).origin === origin);
    for (const url of links) {
      assert(new URL(url).pathname.startsWith(portfolioPath), `Link escapes the project path: ${url}`);
      assert.equal(await getStatus(url), 200, `Broken link: ${url}`);
    }
    const images = await page.locator('img').evaluateAll(images => images.map(i => i.src));
    for (const url of images) assert.equal(await getStatus(url), 200);
    await page.close();
    page = await browser.newPage({viewport:{width:1440,height:1100}});
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
    await page.goto(portfolioURL);
    await page.waitForFunction(() => document.querySelectorAll('.controls:not([hidden])').length === 7);
    await page.evaluate(() => { document.documentElement.style.scrollBehavior = 'auto'; scrollTo(0, 0); });
    fs.mkdirSync(output, {recursive:true});
    await page.screenshot({path:path.join(output,'desktop.png'), fullPage:false});
    await page.locator('#bakery-prep').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(output,'desktop-workflow.png'), fullPage:false});
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({width,height:844});
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Page overflows at ${width}px`);
    }
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(() => scrollTo(0, 0));
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Mobile page overflows');
    await page.screenshot({path:path.join(output,'mobile.png'), fullPage:false});
    await page.locator('.case-nav a[href="#staffing-billing"]').click();
    assert(new URL(page.url()).hash === '#staffing-billing');
    await page.goBack();
    await page.goForward();
    assert(new URL(page.url()).hash === '#staffing-billing');
    await page.locator('#staffing-billing').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(output,'mobile-workflow.png'), fullPage:false});
    let mobileClipsPlayed = 0;
    for (const run of runs) {
      const card = page.locator(`#${run.case}`);
      for (let i = 0; i < run.media.length; i++) {
        await card.locator('.clip-select').selectOption(String(i));
        const result = await card.locator('video').evaluate(async video => {
          video.load();
          await new Promise((resolve, reject) => {
            const timer = setTimeout(() => reject(Error('Mobile metadata timeout')), 10000);
            video.addEventListener('loadedmetadata', () => { clearTimeout(timer); resolve(); }, {once:true});
            video.addEventListener('error', () => { clearTimeout(timer); reject(Error('Mobile media error')); }, {once:true});
          });
          await video.play();
          await new Promise(resolve => setTimeout(resolve, 120));
          const result = {duration:video.duration, played:video.currentTime > 0};
          video.pause();
          return result;
        });
        assert(result.played, 'Mobile capture did not play');
        assert(Math.abs(result.duration - run.media[i].durationSeconds) < .05);
        mobileClipsPlayed++;
      }
    }
    assert.equal(mobileClipsPlayed, expectedClips);
    assert.deepEqual(errors, []);
    // No-JS access retains the case content and direct video/evidence links.
    const nojs = await browser.newPage({javaScriptEnabled:false,viewport:{width:390,height:844}});
    await nojs.goto(projectURL);
    await nojs.waitForURL(portfolioURL);
    assert.equal(await nojs.locator('video[controls]').count(), 7);
    assert.equal(await nojs.locator('.download-list a').count(),expectedClips);
    await nojs.close();
    const report = {status:'passed', actualBrowser:true, sandboxEnabled:true, browserVersion:browser.version(), projectPath, entryRedirect:true, release:release.releaseTag, archiveSHA256:release.archiveSHA256, recordingCommit:release.recordingCommit, packagingCommit:release.packagingCommit, mobileClipsPlayed, desktopViewport:[1440,1100], mobileViewport:[390,844],
      clipsPlayed:clips.length, localLinksChecked:links.length, repeatedReplay:true, speedChanges:true,
      evidenceDisclosure:true, mobileNoOverflow:true, backForward:true, noJavaScriptFallback:true, pageErrors:errors, clips};
    fs.writeFileSync(path.join(output,'browser-verification.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report,null,2));
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode=1; });
