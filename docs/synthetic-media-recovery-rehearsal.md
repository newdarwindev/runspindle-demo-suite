# Offline synthetic media recovery rehearsal

From the repository root:

```sh
for case in recovered tampered missing malformed; do
  python3 tests/test_synthetic_media_recovery.py "$case" || exit
done
python3 -m unittest discover -s tests -p 'test_synthetic_media_recovery.py' -v
```

A generated eight-frame PCM waveform is pinned to an expected digest, format
and decoded bytes. The fixture cancels a simulated partial handoff, then
recovers independently retained bytes in a temporary directory. Both the
retained and recovered files must match the manifest, and a separate standard
library decoder checks the full frames. Missing, changed and malformed media
are distinguished; a pinned malformed file still cannot pass the decoder.

No player, live publishing site, release, artifact upload, network, other
repository, or real demo footage is used. The temporary directory is removed.
This rehearsal cannot establish that the exact actual artifact was retained,
that its release handoff resumed, or that the public playback link works.
