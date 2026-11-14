# Evidence boundary

The default adapter is `deterministic-browser-fixture`. It executes normal actions through rendered browser controls. A separate observer reads server-persisted state and evaluates expected outcomes; workers cannot call the harness endpoint. Unit contract tests do not constitute browser execution.

No upstream Runspindle code executes in this adapter. Pinned references describe intended product capabilities, not claims proved by this suite. New operator UI is a **Conceptual interface**. All accounts, amounts, employers and business records are synthetic.

## Reproduction

Python 3.11+, Node 20+, npm and Chromium are required. `python tools/demo.py bootstrap` installs exact lockfile dependencies and the pinned Playwright Chromium build. In one terminal run `python tools/demo.py up`. In another run `python tools/demo.py record bakery-prep` or `python tools/demo.py record bookkeeper-deposit --fault expired`, then `python tools/demo.py assemble`.

Recordings require a host permitting Chromium's sandbox and local IPC sockets. Do not disable the browser sandbox to work around an executor restriction. The initial cloud executor rejects Chromium's local socket creation, so local unit results must not be presented as completed browser runs.

All generated media and state remain outside Git. CI publishes artifact bundles, including blocked run manifests. `artifacts/presentation.zip` is self-contained. No live external service access is permitted by the worker's browser route policy. No persistent service is installed; `up` is an explicitly started local foreground process.

Session tokens stay in disposable browser session storage and server state, outside published evidence. Do not enable Playwright traces containing raw network bodies. Screenshots hide token values, and no real credentials are collected. Loopback listeners are development-only and are not a hosted multi-user security boundary.

## Remaining work at initial implementation

Browser verification/recording, fresh-process checkpoint resumption, scoped tenant instances, specific recovery UI for every case, fixture evaluation approval/rollback, release publication and hosted gallery remain unverified or incomplete until their evidence is added. A checklist item must not be checked merely because code exists.
