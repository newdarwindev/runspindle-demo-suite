# Evidence boundary

The default adapter is `deterministic-browser-fixture`. It executes normal actions through rendered browser controls. A separate observer reads server-persisted state and evaluates expected outcomes; workers cannot call the harness endpoint. Unit contract tests do not constitute browser execution.

No upstream Runspindle code executes in this adapter. Pinned references describe intended product capabilities, not claims proved by this suite. New operator UI is a **Conceptual interface**. All accounts, amounts, employers and business records are synthetic.

## Reproduction

Python 3.11+, Node 20+, npm and Chromium are required. `python tools/demo.py bootstrap` installs exact lockfile dependencies and the pinned Playwright Chromium build. In one terminal run `python tools/demo.py up`. In another run `python tools/demo.py record bakery-prep` or `python tools/demo.py record bookkeeper-deposit --fault expired`, then `python tools/demo.py assemble`.

Recordings require a host permitting Chromium's sandbox and local IPC sockets. Do not disable the browser sandbox to work around an executor restriction. The initial cloud executor rejects Chromium's local socket creation, so local unit results must not be presented as completed browser runs.

All generated media and state remain outside Git. CI publishes artifact bundles, including blocked run manifests. `artifacts/presentation.zip` is self-contained. No live external service access is permitted by the worker's browser route policy. No persistent service is installed; `up` is an explicitly started local foreground process.

Session tokens stay in disposable browser session storage and server state, outside published evidence. Do not enable Playwright traces containing raw network bodies. Screenshots hide token values, and no real credentials are collected. Loopback listeners are development-only and are not a hosted multi-user security boundary.

## Current verification

GitHub Actions run [43628194461](https://github.com/newdarwindev/runspindle-demo-suite/actions/runs/43628194461) verified all seven normal browser workflows plus expired bank-session recovery, buyer-to-seller account recovery, and lost-ack reconciliation at parent commit e080edf11cd7166576d93caa67547ef1fa95f67b. The preinstalled official Chrome channel ran with its sandbox enabled. Actual clips were retained in its artifact. A fresh recursive GitHub clone verified nine exact child pins and passed 25 contract tests.

Twelve child repositories remain ordinary source directories temporarily because GitHub rejected further repository creation with a cooldown message. Their code is included so the default branch runs; completion requires creating those repositories and replacing the directories with exact gitlinks. No rate-limit bypass is used.

Full fault-matrix recordings and evaluation/presentation verification are tracked separately in the latest CI. Passing unit tests alone does not prove these paths.
