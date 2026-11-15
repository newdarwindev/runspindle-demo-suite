# Original delivery milestones

All five original milestones have now been delivered. Requirement-level re-audit found gaps in the first release; those were implemented and reverified, rather than treating earlier green CI as proof of missing behavior.

| Milestone | Verified status |
| --- | --- |
| 1. Publish now | Complete. Parent and 21 real child repositories published and pinned. Workflow children own executed steps/scopes and independent assertions; app children own consumed defaults and action permissions. |
| 2. Publish the first demos | Complete. Bakery normal path and bookkeeper sign-in recovery have actual recordings and independent workbook readback. |
| 3. Complete the suite | Complete for fixture execution. Seven normal workflows, 16 fault scenarios, 65 tests, independent browser readback, manual-adapter browser contract, evaluation approval and rollback pass. |
| 4. Publish and verify the presentation package | Complete. Gallery/video/link checks pass. Durable ZIP includes executed JSON/Markdown fault matrix, actual clips, posters, cues, evidence and reel. Downloaded ZIP integrity and all 494 checksums verified for the release below. |
| 5. Finish the handoff | Complete. Scope, limits and reproduction commands are recorded here and in STATUS.md and MANUAL.md. |

## Verified checkpoint

- [Full CI 43691466189](https://github.com/newdarwindev/runspindle-demo-suite/actions/runs/43691466189) at `efcb0fdd330a75e020681df110c2405be0f3ba93`.
- [Durable presentation release](https://github.com/newdarwindev/runspindle-demo-suite/releases/tag/demo-efcb0fdd330a).
- Fresh recursive checkout of all 21 updated pins passed 65 tests.

## Scope and remaining validation limits

All execution is deterministic fixture execution against synthetic localhost apps. No upstream Runspindle integration or comparative staff-time savings is claimed. The manual adapter was exercised in a real browser using a separately labeled synthetic test driver; no attended human end-to-end session is claimed. That optional attended validation needs a graphical host and the command in MANUAL.md. The operator adapter is a software/control boundary, not OS-level isolation.

No hosted backend or persistent demo service is provisioned. The downloadable gallery and locally runnable suite are delivered; hosting requires an explicitly selected supported target and applicable authorization.

## Regeneration

From the recursive checkout, use `python3 tools/demo.py bootstrap`, start `python3 tools/demo.py up` in a separate terminal, then run:

```sh
python3 tools/demo.py test
python3 tools/demo.py record-all
python3 tools/demo.py fault-matrix
node tools/evaluation-browser.cjs
python3 tools/presentation.py --reel
node tools/verify-gallery.cjs
```

Use supported sandboxed Chromium; CI uses `BROWSER_CHANNEL=chrome`. Expected blocked/unknown behavior is distinct from business-task completion. Missing evidence is unavailable, never inferred from a green normal run.
