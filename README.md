# Runspindle demo suite

Teach it a real job. Run it again. Measure the difference.

Fictional small-business browser apps, synthetic data and deterministic fixture workflows. New operator screens are conceptual interfaces. Fixture success does not prove upstream Runspindle integration or competitive savings.

## Start

```sh
git clone --recurse-submodules https://github.com/newdarwindev/runspindle-demo-suite.git
cd runspindle-demo-suite
```

All seven workflows have browser recordings and independent verification. All 21 child repositories are published and pinned. See [verified presentation release](https://github.com/newdarwindev/runspindle-demo-suite/releases/tag/demo-b6479f31c50e) for the self-contained gallery, clips and evidence.

```sh
python3 tools/demo.py bootstrap
python3 tools/demo.py up
# In another terminal:
python3 tools/demo.py record bakery-prep
python3 tools/demo.py record bookkeeper-deposit --fault expired
python3 tools/demo.py assemble
python3 tools/demo.py test
```

See [commands](docs/COMMANDS.md), [evidence boundary](docs/EVIDENCE.md), and [pinned sources](docs/SOURCES.md).

## Intended layout

- `apps/`: 14 separately versioned mock web apps, pinned as Git submodules.
- `workflows/`: seven independently versioned business workflows, pinned as Git submodules.
- `contracts/`: session scope, checkpoint, evidence and adapter contracts.
- `tools/`: bootstrap, doctor, run, recording and package assembly.
- `tests/`: independent verification and fault coverage.
- `docs/`: presenter cues, evidence boundary and source index.
- `.github/workflows/`: bounded fixture-only CI and artifact publication.

## Progress

- [x] Publish initial parent repository.
- [x] Publish app/workflow repositories and exact submodule pins.
- [x] Bakery normal run and bookkeeper sign-in recovery with actual recordings.
- [x] Seven independently verified normal workflows.
- [x] Session, authorization, missing-data, recovery, lost-ack and exact-artifact fault matrix.
- [x] Locked-version bakery evaluation, approval and rollback demo.
- [x] Gallery, clips, cues and evidence package.
- [x] Fresh recursive checkout, final CI and published package verification.

No persistent demo services, schedules or agents are provisioned by this project. All accounts are fictional; worker access is limited to controlled fixture apps.

See [current status and remaining blockers](docs/STATUS.md).
