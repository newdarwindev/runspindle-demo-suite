# Workflow video portfolio

A self-contained static, GitHub Pages-ready portfolio of seven normal fixture runs. It contains 31 original WebM page captures, 14 original result/readback screenshots, source manifests, exact verification results and hashes. It has no upstream Runspindle dependency, no backend, no analytics and no runtime CDN assets. Total checked-in payload is about 5 MB. The 122.84-second full-release MP4 reel remains a direct release link rather than another large checked-in file.

The captures are very short (0.28–3.44 seconds), often under one second. They are raw per-page captures, not complete human-paced walkthroughs. Slow playback and still screenshots aid inspection; they do not add evidence. Result labels come from the original verification JSON. This page does not claim real accounts, upstream integration, human productivity savings, or local-runner execution.

## View locally

From the repository root, run this temporary static-file server, then open `http://127.0.0.1:4340/portfolio/`:

```sh
python3 -m http.server 4340 --bind 127.0.0.1 --directory docs
```

Stop it with Ctrl-C when finished. The page also exposes all clips and result links without JavaScript. Under `file://`, browsers may block the JSON fetch, so native video and direct links remain available while the enhanced speed/capture selectors stay hidden.

## Verify locally

No upstream code, model service, credentials or application startup is required.

```sh
python3 docs/portfolio/tools/validate.py
python3 docs/portfolio/tools/validate.py --probe # optional: requires ffprobe
python3 -m unittest discover -s docs/portfolio/tools -p 'test_*.py' -v
node docs/portfolio/tools/check-browser.cjs # repository's locked Playwright, supported sandboxed Chromium
```

Browser QA starts a bounded localhost-only file server, plays all 31 clips, checks links, speed/replay controls, evidence disclosures, mobile overflow, history navigation and no-JS fallback, then closes the server/browser. Reports and review screenshots go to `/tmp/runspindle-portfolio-qa` by default (`PORTFOLIO_QA_DIR` can override). Set `PLAYWRIGHT_BROWSERS_PATH` or `BROWSER_CHANNEL` only for an already supported installed browser. Do not disable the browser sandbox.

The checked-in [QA report](QA.json) records bounded cloud-browser review of this static page, not a new execution of the source fixture workflows.

## Reproduce the copied evidence

Source: [release demo-085a776b2328](https://github.com/newdarwindev/runspindle-demo-suite/releases/tag/demo-085a776b2328), source commit `085a776b2328862f30fe6539ef41ad1a3ed52eb4`.

Download its `presentation.zip`, then:

```sh
python3 docs/portfolio/tools/build.py /path/to/presentation.zip
python3 docs/portfolio/tools/validate.py --probe
```

The builder requires archive SHA256 `dee8aebf13e0a9a48326645491ad76d754fd31b7df787ea4a1bf5bd06e78185a`, checks copied bytes against the release hashes, selects exactly seven `fault: normal` verified runs, and copies only allowlisted evidence. It does not execute the workflows or generate/transform any media. Any future source release requires deliberate provenance review and pin updates. `data/provenance.json` maps each copied file to its original archive entry and SHA256. `checksums.json` covers every browser payload file. `tools/template.html` is the editable source for generated `index.html`.

## Hosting requires the owner

No Pages configuration, deployment workflow, persistent runner, schedule or service is created by these files. The repository owner must activate hosting manually:

1. Open this repository's **Settings → Pages**.
2. Choose **Deploy from a branch**, branch **main**, folder **/docs**, and save.
3. Wait for GitHub's Pages publication to complete.
4. Open the resulting Pages URL and its `/portfolio/` path, then confirm media playback and provenance links.

`docs/index.html` redirects to `portfolio/`, with a visible fallback link. `docs/.nojekyll` keeps this static payload out of Jekyll processing. The expected URL after owner activation is `https://newdarwindev.github.io/runspindle-demo-suite/portfolio/`; it is not claimed live until checked. Keep the hosting issue open until the live portfolio is independently reachable and verified. The built-in GitHub Pages publication process, when enabled by the owner, is separate from the demo's fixture CI and does not run a business workflow.
