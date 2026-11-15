# Milestone 6: independent fictional product identities

Every mock software product must have its own branding, visual style, color scheme and typography. This is an additional milestone, not a retrospective claim about the original release.

## Acceptance gates

- Each child owns `brand.json` and its rendered `ui.html`: distinct name, mark, tagline, palette, type pairing/treatment and layout motif.
- No shared placeholder identity; automation IDs and synthetic-fixture safety disclosures remain intact.
- Ordinary text and button text meet 4.5:1 contrast; keyboard focus is visible; narrow screens do not overflow.
- Rendering uses offline system fonts and no remote font/image service or upstream code. Font availability varies by host; fallback families are intentional.
- Sandboxed Chromium renders every actual server-composed app at 1280px and 390px. Review the 28 screenshots for visual distinction, hierarchy and responsive usability, then regenerate workflow recordings before presenting them as the new design.

## Product directions

| Mock software | Fictional brand | Visual direction |
| --- | --- | --- |
| Workbook | Gridwell | Forest-green ledger, serif display, square cells |
| Mail | Postlane | Cobalt inbox, humanist headings, soft panels |
| Counter orders | Crumb & Counter | Warm bakery paper, editorial serif, dashed cards |
| Job board | Northstar Jobs | Violet directory, compact geometric headings |
| Applicant portal | Sprout Apply | Leaf-green journey, pill controls, welcoming type |
| Interview room | Gather Room | Rose conversation space, centered serif masthead |
| Coding assessment | Bytebench | Mint-on-slate terminal, monospace, sharp panels |
| Issue tracker | Signal Desk | Amber triage board, uppercase condensed hierarchy |
| Code workspace | Forge Workspace | Plum workbench, lavender accents, monospace |
| Bank | Stonebridge | Slate banking ledger, classical serif, double rules |
| Vendor portal | Dockside Supply | Teal logistics console, strong horizontal rules |
| Timesheets | Tempo Hours | Coral scheduling space, tight sans-serif display |
| Marketplace | Second Story | Berry boutique, editorial italic headings |
| Supplier portal | Fieldnote Produce | Olive packing ledger, bookish headings, inset rules |

## Verification and limits

2026-11-15: all 68 Python suite tests passed, including three new branding tests across all 14 apps. These enforce identity uniqueness, implementation wiring, preserved selectors, offline assets, responsive/focus rules and palette contrast. They are not visual approval.

`node tools/check-branding.cjs` is the bounded browser gate. It writes screenshots and `artifacts/branding/verification.json`. Use the installed Playwright browser, `BROWSER_CHANNEL=chrome`, or a supported `BROWSER_EXECUTABLE`. Chromium sandboxing stays enabled.

2026-11-15: a fresh recursive checkout of `fb916a855fca470454d88a3d363d74ba695e8e5b` on the connected Linux qualification host passed all 68 tests and the sandboxed Chrome desktop/mobile gate: 14 apps, 28 screenshots, no horizontal overflow, no JavaScript errors, visible keyboard focus and correct displayed identities. Desktop/mobile contact sheets were visually reviewed for distinct palettes, mastheads, typography treatments and card motifs. [Desktop contact sheet](branding/desktop.png), [mobile contact sheet](branding/mobile.png), [machine-readable evidence](branding/verification.json).

The initial cloud host could not create Chromium process sockets; qualification instead used a supported connected host without disabling sandboxing. This verifies the initial signed-out layouts, not every populated or interrupted workflow state. Refreshed full workflow recordings/package verification remain a separate gate.

The original release recordings and static portfolio remain historical evidence of the prior interface. No new recordings, full browser workflow pass or visual acceptance is claimed by this change. No persistent jobs, services or agents are installed.

```sh
python3 tools/demo.py test
node tools/check-branding.cjs
# After visual review, rerun the documented workflow recording/package checks.
```
