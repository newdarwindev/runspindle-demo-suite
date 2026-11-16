# Workflow video portfolio

A self-contained static, GitHub Pages-ready portfolio of seven normal fixture runs. It contains 31 original WebM page captures, 14 original result/readback screenshots, source manifests, exact verification results and hashes. It has no upstream Runspindle dependency, no backend, no analytics and no runtime CDN assets. The hashed browser payload is about 4.5 MB. The 116.84-second full-release reel remains a direct release link, with portable WebM and MP4 alternatives, rather than another large checked-in file.

The captures are very short (0.24–2.84 seconds), often under one second. They are raw per-page captures, not complete human-paced walkthroughs. Slow playback and still screenshots aid inspection; they do not add evidence. Result labels come from the original verification JSON. The source recordings are bounded Strix fixture rehearsals, not GitHub Actions runner qualification. This page does not claim real accounts, upstream integration, or human productivity savings.

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

Browser QA starts a bounded localhost-only file server, plays all 31 clips on desktop and again at a mobile viewport, checks links, speed/replay controls, evidence disclosures, mobile overflow, history navigation and no-JS fallback, then closes the server/browser. Reports and review screenshots go to `/tmp/runspindle-portfolio-qa` by default (`PORTFOLIO_QA_DIR` can override). Set `PLAYWRIGHT_BROWSERS_PATH` or `BROWSER_CHANNEL` only for an already supported installed browser. Do not disable the browser sandbox.

The checked-in [QA report](QA.json) records bounded sandboxed Strix browser review of this static page, not a new execution of the source fixture workflows.

## Reproduce the copied evidence

Source: [release demo-193b07c4eae8](https://github.com/newdarwindev/runspindle-demo-suite/releases/tag/demo-193b07c4eae8). The recordings came from commit `1c6e0745549f7f66621999267fcc14de930ca90e`; the packaging fixes came from `193b07c4eae87c0d5ecf9db4d0de053d047b8399`. The two identities are intentionally separate.

Download its `presentation.zip`, then:

```sh
python3 docs/portfolio/tools/build.py /path/to/presentation.zip
python3 docs/portfolio/tools/validate.py --probe
```

The reviewed [release descriptor](release.json) pins the archive SHA256 `8146bc89cfcc2744a77296e8ffa0c1d4db65a1b0b0c7d992bee9af116e069326`, original index/checksum hashes, recording and packaging commits, and the seven selected verified normal run IDs. The builder checks the archive before changing output, verifies the original hashes and recording identity, and stages allowlisted evidence. It does not execute workflows or generate/transform any media. A future release needs deliberate descriptor and provenance review, not just a new download URL.

The source has 25 records: seven verified normal runs, sixteen fault cases, one bakery evaluation case, and one earlier normal bakery attempt blocked before capture by a missing Playwright FFmpeg executable. The blocked attempt is not a success and is not silently dropped: [excluded-normal-runs.json](data/excluded-normal-runs.json), the visible page disclosure, and original manifest/verification/worker evidence retain it. The complete original index, checksum document and all 25 source manifests remain available. Selection is deterministic even if the source index order changes.

[data/provenance.json](data/provenance.json) maps 166 copied files to their original archive entries and SHA256 values. [checksums.json](checksums.json) covers 176 browser payload files, including the descriptor. `tools/template.html` is the editable source for generated `index.html`. The tests reject hash tampering, mismatched capture commits, duplicate identities, path escapes, result drift, and removal of the blocked attempt.

## Historical evidence

The earlier portfolio and its original bytes remain at the immutable [pre-refresh repository snapshot](https://github.com/newdarwindev/runspindle-demo-suite/tree/e95c9e2b165dad93dac45846de0181b54dfe5cfb/docs/portfolio), with its [demo-085a776b2328 source release](https://github.com/newdarwindev/runspindle-demo-suite/releases/tag/demo-085a776b2328). The page and descriptor link both. Older recordings have not been relabeled as branded recordings or as a later run.

## Hosting requires the owner

No Pages configuration, deployment workflow, persistent runner, schedule or service is created by these files. The repository owner must activate hosting manually:

1. Open this repository's **Settings → Pages**.
2. Choose **Deploy from a branch**, branch **main**, folder **/docs**, and save.
3. Wait for GitHub's Pages publication to complete.
4. Open the resulting Pages URL and its `/portfolio/` path, then confirm media playback and provenance links.

`docs/index.html` redirects to `portfolio/`, with a visible fallback link. `docs/.nojekyll` keeps this static payload out of Jekyll processing. The expected URL after owner activation is `https://newdarwindev.github.io/runspindle-demo-suite/portfolio/`; it is not claimed live until checked. Keep the hosting issue open until the live portfolio is independently reachable and verified. The built-in GitHub Pages publication process, when enabled by the owner, is separate from the demo's fixture CI and does not run a business workflow.
