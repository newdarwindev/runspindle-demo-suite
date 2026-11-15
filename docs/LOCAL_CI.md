# Local CI routing and prerequisites

Both verification and release publication route to the existing labels:
`[self-hosted, linux, x64, runspindle-isolated, strix]`.

Only main-branch pushes and explicit dispatch trigger this workflow. Public pull-request code is not automatically executed on the trusted local lane. A single workflow concurrency group prevents this repository's fixture-port collisions. Release assets and historical releases remain unchanged; a new release requires successful verification.

## Required owner setup before local execution

The inspected fleet configuration did not include `runspindle-demo-suite`. The owner must enroll it using the fleet's approved process. The agent must not enable a persistent demo controller/service itself.

The disposable Ubuntu 24.04 guest must provide Python3, Node/npm, Git, curl, ffmpeg/ffprobe, the pinned Playwright Chromium's system libraries, and GitHub CLI for the separate release job. Current guest preparation sources only establish the basic language/Git tools; they do not prove media/browser prerequisites. Ordinary job users have no sudo. Provision dependencies through the owner's approved guest-image process, not by modifying the physical host from CI.

Approved guest egress must support the locked npm dependencies, Playwright browser distribution, GitHub checkout/submodules, artifact operations and release publication. The inspected egress policy did not establish npm registry or Playwright CDN access. Network/security changes need their own applicable approval. Do not bypass the egress policy or disable browser sandboxing.

## Verification and limitations

Workflow routing is not evidence that a runner accepted or passed a job. Check the actual Actions job runner identity and result after owner setup. The job fails visibly on missing tools or browser prerequisites and uses per-job npm/browser caches. Existing verified hosted releases remain available as historical evidence, not evidence of local execution.

No new persistent runner service, scheduled job, controller, credentials or network rule is created by this repository change. Pending local jobs require owner provisioning; do not repeatedly enqueue replacements to work around missing enrollment.
