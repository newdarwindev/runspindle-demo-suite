# Presentation and evaluation recording

All media must originate from executed browser runs. No synthetic screenshots or narrated mock clips are substituted for missing recordings. The gallery lists blocked/failed cases and missing media explicitly. It labels the operator UI conceptual, executions fixture-only, and comparative savings untested.

## Regenerate

From the recursive parent checkout, install the locked dependencies and start the fixture app server using the root instructions. Record the business workflows, then:

```sh
node tools/evaluation-browser.cjs
python3 tools/presentation.py --reel
```

For a CI image with a supported preinstalled Chrome sandbox, set `BROWSER_CHANNEL=chrome`. Chromium's sandbox stays enabled. Never disable it to work around an environment restriction.

The evaluation command runs a bounded localhost-only evaluation server, then closes it. It compares the two locked bakery versions on the same held-out grouped cases, demonstrates blocked unapproved activation, approves feedback tied to the exact comparison output, explicitly approves the candidate revision, activates it, and rolls back. All approvals are visibly performed by a **scripted fixture operator**, not attributed to the real user. A separate persisted-state readback verifies the activation history. Comparison alone never changes the active version.

`tools/presentation.py` builds `artifacts/presentation-package/index.html`, cue-sheet Markdown, per-clip WebVTT labels, optional poster extraction when ffmpeg exists, and a source/evidence index. Every retained run includes its provenance and actual verdict. The assembler copies only allowlisted evidence files, excludes browser state, verifies all local HTML links, produces `artifacts/presentation.zip`, and reopens the ZIP to check every file hash. Generated media and archives remain outside Git.

Event timecodes in the cue sheet are run-relative; they are not falsely presented as frame-accurate offsets for each independently recorded page clip. Per-clip labels identify fixture execution, case, run and outcome. Individual clips are usable without a combined reel. `--reel` uses available ffmpeg to render title cards and combine actual clips. The evidence index reports rendered, unavailable or failed status; no reel is claimed on failure.

## Manual evaluation

```sh
python3 tools/evaluate.py serve
```

Open `http://localhost:4320`, compare versions, approve feedback for the displayed output hash, then copy the displayed v2 revision into the explicit approval field. Activation is rejected without that approval. Rollback restores the prior version. State defaults to `.state/evaluation.json`; the recording command uses a separate run-specific state file.

Timings are fixture elapsed time. Human operator minutes remain unknown unless actually measured. Future competitive cost comparisons must include setup, maintenance, review and recovery per verified completion against supported alternatives.

The package includes executed `fault-matrix.json` and `fault-matrix.md`, linked from the gallery and evidence index. Each row must match an exported run identity, case, fault and final verdict. Missing matrix input is visibly unavailable. Expected blocked or unknown behavior is not reported as a completed business task.

The combined reel includes VP8 WebM and H.264 MP4 versions. The gallery offers WebM first so pinned Chromium builds without proprietary H.264 codecs can play it; downloadable MP4 remains available. Both versions derive from the same actual fixture clips. This packaging change does not turn short page captures into complete product execution.

## Task-local encoder override

For an approved isolated FFmpeg installation, set `DEMO_FFMPEG_PATH` to its absolute regular executable path and `DEMO_FFMPEG_SHA256` to the independently verified binary digest. The assembler rejects missing, malformed or mismatched pins, symlinks and non-executable files before exporting artifacts. With no override it retains the existing PATH lookup. The encoder must support drawtext, H.264 and VP8; both MP4 and portable WebM reels remain required. This does not install software, modify global tools, enroll runners or prove Actions qualification. Preserve the source/version/license and verified digest alongside run evidence.
