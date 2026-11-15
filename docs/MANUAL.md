# Manual operator and presenter path

From a recursive checkout, install dependencies with `python tools/demo.py bootstrap`, then start `python tools/demo.py up` in one terminal. The server uses synthetic local fixtures only. Stop it with Ctrl-C.

In a second terminal with a graphical desktop, run:

```
DEMO_OPERATOR_MODE=manual python tools/demo.py record bookkeeper-deposit --fault expired
```

The browser opens visibly. The terminal announces each requested operator control. Sign in on the requested page, complete the labeled fixture challenge when requested, and wait for identity verification before the worker resumes. Each handoff allows five minutes. This uses synthetic buttons, not real credentials or real MFA. Never enter real credentials.

The manual mode does not click operator controls. The separate operator adapter waits for the presenter's matching UI response. Normal record reads and workbook writes still run through the workflow worker. `DEMO_OPERATOR_MODE=scripted` (the default) delegates those same operator controls to a separately labeled fixture operator for CI. Neither mode grants worker access to the reset/observe harness. Timing measures handoff wall time or scripted button duration, not active human labor or competitive savings.

For other cases use `record bakery-prep --fault ambiguous`, `record vintage-returns --fault wrong-account`, `record staffing-billing --fault tenant-expired`, or `record consultancy-contract`. At a wrong-account stop, switch the Account field to the authorized fixture account before clicking sign-in. For bakery choose November 15 or November 21 in **Owner pickup date**, then confirm. For consultancy choose the listing; complete the written-screening review, live-interview advance and exact assessment revision approval only when prompted. The worker saves a draft before application submission. A forbidden assessment remains blocked and explicitly hands control to a human; it never auto-submits an answer.

A fully manual walkthrough is also possible without the runner: reset the case, open each app's localhost URL from its README with `?case=CASE&account=ACCOUNT&operator=manual`, select authorized scope, sign in and use the visible controls. Source records, inbox threads, draft replies, application answers, code edits/tests and workbook payloads are editable through those controls. Scoped source links preselect the tenant and requested record. Use `python tools/demo.py verify CASE` for persisted-state assertions; that command alone is not a browser recording or independent browser verification.

Resetting a case replaces its previous live state. Use `python tools/demo.py resume CASE --run-id RUN_ID` only while that run still owns the case state; use the same `DEMO_OPERATOR_MODE=manual` environment for continued human handoffs. Never reset a case while a run is waiting.

## Verification boundary

The headed manual mode is implemented and covered by adapter/control and server contract checks. CI also exercises its waiting and fresh-identity handback in a real browser using a separately labeled synthetic test driver. No attended end-to-end manual browser run has been recorded during this implementation. Existing automated browser recordings establish the scripted fixture paths only. Run the command above on a graphical host to validate the attended path.
