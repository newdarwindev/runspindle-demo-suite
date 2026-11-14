# Commands

Start from a recursive checkout; every app/workflow remote is portable HTTPS. Public demo children require no special access. No upstream credentials or model keys are used.

```
python3 tools/demo.py bootstrap
python3 tools/demo.py doctor
python3 tools/demo.py up
# separate terminal
python3 tools/demo.py reset bakery-prep
python3 tools/demo.py run bakery-prep
python3 tools/demo.py record bookkeeper-deposit --fault expired
python3 tools/demo.py record-all
python3 tools/demo.py assemble
python3 tools/demo.py test
python3 tools/evaluate.py compare
```

`run` and `record` both capture browser video. Commands return failure if independent verification fails. Server is foreground and stops on Ctrl-C. Chromium retains its sandbox. `CHROMIUM_PATH` selects a preinstalled compatible browser, otherwise the pinned Playwright browser is used.

## Fixture evaluation

`compare` does not activate a candidate. Inspect the comparison, then an operator can explicitly approve the exact revision shown using `python3 tools/evaluate.py activate --version v2 --approved-revision SHA --operator 'fixture operator'`. This is synthetic approval only, not an upstream product configuration. `python3 tools/evaluate.py rollback` restores the previous active fixture version.

Raw browser state is not included in the package. Generated state, recordings and caches are ignored by Git. CI's artifact contains `presentation.zip` and the self-contained gallery under `package/`.
