"""Verify recovery of tiny generated media after a mock canceled handoff."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave


SCRIPT = Path(__file__).resolve()
FIXTURE = SCRIPT.with_name("fixtures") / "synthetic-media-manifest.json"
CASES = {
    "recovered": "verified_fixture",
    "tampered": "digest_mismatch",
    "missing": "retained_bundle_missing",
    "malformed": "media_decode_failed",
}
MALFORMED = b"not a waveform"


def generate_wav():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setparams((1, 1, 8000, 0, "NONE", "not compressed"))
        writer.writeframes(bytes((128, 160, 192, 160, 128, 96, 64, 96)))
    return buffer.getvalue()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_playable(path, manifest):
    try:
        with wave.open(str(path), "rb") as reader:
            expected = {
                "channels": reader.getnchannels(),
                "sample_width": reader.getsampwidth(),
                "frame_rate": reader.getframerate(),
                "frames": reader.getnframes(),
                "compression": reader.getcomptype(),
            }
            frames = reader.readframes(reader.getnframes())
            return (
                expected == manifest["wav"]
                and len(frames) == expected["frames"] * expected["channels"] * expected["sample_width"]
                and list(frames) == manifest["decoded_bytes"]
            )
    except (wave.Error, EOFError):
        return False


def recover(source, destination, manifest):
    if not source.is_file():
        return "retained_bundle_missing", False
    if digest(source.read_bytes()) != manifest["bundle_sha256"]:
        return "digest_mismatch", False
    shutil.copyfile(source, destination)
    if digest(destination.read_bytes()) != manifest["bundle_sha256"]:
        return "recovered_copy_mismatch", False
    if not verify_playable(destination, manifest):
        return "media_decode_failed", False
    return "verified_fixture", True


def rehearse(scenario):
    if scenario not in CASES:
        raise ValueError("unknown scenario")
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    retained_bytes = generate_wav()
    if scenario == "tampered":
        retained_bytes += b"fixture-altered"
    elif scenario == "malformed":
        retained_bytes = MALFORMED
        fixture["bundle_sha256"] = fixture["malformed_fixture_sha256"]

    with tempfile.TemporaryDirectory(prefix="synthetic-media-") as temporary:
        root = Path(temporary)
        source = root / "retained.wav"
        partial = root / "canceled.part"
        restored = root / "recovered.wav"
        partial.write_bytes(retained_bytes[:8])
        canceled = partial.stat().st_size < len(retained_bytes)
        partial.unlink()
        if scenario != "missing":
            source.write_bytes(retained_bytes)
        outcome, decoded = recover(source, restored, fixture)
        canceled = canceled and not partial.exists()

    return {
        "synthetic_only": True,
        "published_release_verified": False,
        "scenario": scenario,
        "handoff_cancelled": canceled,
        "outcome": outcome,
        "local_decode_verified": decoded,
        "teardown_cleared": not root.exists(),
        "passed": (
            outcome == CASES[scenario] and decoded == (scenario == "recovered")
            and canceled and not root.exists()
        ),
    }


class SyntheticMediaRecoveryTests(unittest.TestCase):
    def test_cli_reproduces_success_and_all_stops(self):
        for case, outcome in CASES.items():
            with self.subTest(case=case):
                cmd = [sys.executable, str(SCRIPT), case]
                output = subprocess.check_output(cmd, text=True)
                self.assertEqual(output, subprocess.check_output(cmd, text=True))
                receipt = json.loads(output)
                self.assertTrue(receipt["passed"])
                self.assertTrue(receipt["handoff_cancelled"])
                self.assertTrue(receipt["teardown_cleared"])
                self.assertTrue(receipt["synthetic_only"])
                self.assertFalse(receipt["published_release_verified"])
                self.assertEqual(receipt["outcome"], outcome)
                self.assertEqual(receipt["local_decode_verified"], case == "recovered")

    def test_matching_digest_does_not_cure_truncated_frames(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        bad = generate_wav()[:-1]
        fixture["bundle_sha256"] = digest(bad)
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "retained.wav"
            source.write_bytes(bad)
            result = recover(source, Path(temporary) / "recovered.wav", fixture)
        self.assertEqual(result, ("media_decode_failed", False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=CASES)
    receipt = rehearse(parser.parse_args().scenario)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
