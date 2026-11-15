/* Bounded offline visual milestone check. No service, remote fonts or upstream code. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), cp = require('child_process'), assert = require('assert');
const root = path.resolve(__dirname, '..');
(async () => {
  const out = path.join(root, 'artifacts', 'branding'); fs.mkdirSync(out, { recursive: true });
  const apps = JSON.parse(fs.readFileSync(path.join(root, 'contracts/apps.json')));
  const browser = await chromium.launch({ headless: true, chromiumSandbox: true,
    ...(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {}) });
  const results = [];
  try {
    for (const app of apps) {
      const brand = JSON.parse(fs.readFileSync(path.join(root, 'apps', app, 'brand.json')));
      // Render server additions too, not just the raw child file.
      const html = cp.execFileSync('python3', ['-c', 'import sys;sys.path.insert(0,"tools");from server import render_ui;print(render_ui(sys.argv[1]))', app], { cwd: root, encoding: 'utf8' });
      for (const width of [1280, 390]) {
        const page = await browser.newPage({ viewport: { width, height: 960 } });
        const errors = []; page.on('pageerror', e => errors.push(e.message));
        await page.route('**/*', route => route.request().url() === 'http://127.0.0.1/brand-preview' ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
        await page.goto('http://127.0.0.1/brand-preview');
        assert.equal(await page.locator('#title').innerText(), brand.name);
        assert.equal(await page.title(), brand.name + ' · Fictional demo');
        const computed = await page.evaluate(() => ({
          bodyFont: getComputedStyle(document.body).fontFamily,
          headingFont: getComputedStyle(document.querySelector('h1')).fontFamily,
          background: getComputedStyle(document.body).backgroundColor,
          style: document.querySelector('header').dataset.visualStyle,
          overflow: document.documentElement.scrollWidth > innerWidth,
          buttonVisible: document.querySelector('#signin').getBoundingClientRect().width > 0
        }));
        assert(!computed.overflow, `${app} overflows at ${width}px`);
        assert(computed.buttonVisible); assert.equal(computed.style, brand.style); assert.deepEqual(errors, []);
        await page.locator('#signin').focus();
        assert.equal(await page.locator('#signin').evaluate(el => getComputedStyle(el).outlineStyle), 'solid');
        await page.screenshot({ path: path.join(out, `${app}-${width}.png`), fullPage: true });
        results.push({ app, width, ...computed }); await page.close();
      }
    }
    const desktop = results.filter(x => x.width === 1280);
    assert.equal(new Set(desktop.map(x => x.background)).size, apps.length);
    assert.equal(new Set(desktop.map(x => x.style)).size, apps.length);
    fs.writeFileSync(path.join(out, 'verification.json'), JSON.stringify({ passed: true, apps: apps.length, viewports: [1280, 390], results }, null, 2));
    console.log(JSON.stringify({ branding: 'passed', apps: apps.length, screenshots: results.length }));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
