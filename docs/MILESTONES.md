# Original delivery milestones

The original five milestones are retained below. Historical green CI verifies the scope it executed, not requirements absent from that implementation.

| Milestone | Evidence and current status |
| --- | --- |
| 1. Publish now | Complete: parent README/checklist and all 14 app plus seven workflow repositories are published with exact submodule pins. |
| 2. Publish the first demos | Complete: bakery and bookkeeper sign-in recovery have actual browser recordings and independent checks in published releases. |
| 3. Complete the suite | Reopened on review: seven normal paths and 14 historical fault scenarios passed, but manual operator handoff, application draft/screening, navigable issue evidence, staffing recovery coverage and source-link verification need the follow-up implementation. |
| 4. Publish and verify the presentation package | Historical package verified; refresh required after milestone 3 corrections. The follow-up package must include the executed fault matrix in JSON and a human-readable table. |
| 5. Finish the handoff | Pending refreshed CI/release evidence and explicit disclosure of any remaining gaps. |

## Scope

All execution is deterministic fixture execution against synthetic localhost apps. No upstream Runspindle integration or comparative staff-time savings is claimed. No hosted backend or persistent demo service is provisioned.

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

Use a supported sandboxed Chromium installation; CI uses `BROWSER_CHANNEL=chrome`. The generated matrix records expected blocked/unknown outcomes separately from business-task completion. Missing matrix evidence is explicitly unavailable, never inferred from a green normal run.
