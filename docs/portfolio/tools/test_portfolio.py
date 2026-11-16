#!/usr/bin/env python3
"""Focused regression tests, including negative evidence-integrity cases."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from validate import ROOT, validate, sha
from release import load_release
from build import select_runs, build, read_source
import io, zipfile
from unittest.mock import patch


class PortfolioTests(unittest.TestCase):
    def test_checked_in_portfolio(self):
        self.assertEqual(validate()['clips'], load_release(ROOT)['selectedClipCount'])

    def altered(self, relative, change, rehash=False):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'portfolio'
            shutil.copytree(ROOT, root)
            target = root / relative
            target.write_text(change(target.read_text()))
            if rehash:
                checksums = json.loads((root / 'checksums.json').read_text())
                checksums[relative] = sha(target.read_bytes())
                (root / 'checksums.json').write_text(json.dumps(checksums))
            with self.assertRaises(ValueError):
                validate(root)

    def test_asset_tampering_rejected(self):
        self.altered('styles.css', lambda text: text + '\n/* tampered */')

    def test_results_cannot_disagree_with_original_evidence(self):
        def change(text):
            runs = json.loads(text)
            runs[0]['result']['loaves'] = 999
            return json.dumps(runs)
        self.altered('data/runs.json', change, rehash=True)

    def test_media_metadata_cannot_be_rewritten(self):
        def change(text):
            runs = json.loads(text)
            runs[0]['media'][0]['durationSeconds'] = 100
            return json.dumps(runs)
        self.altered('data/runs.json', change, rehash=True)

    def test_broken_links_rejected(self):
        self.altered('index.html', lambda text: text.replace('href="data/provenance.json"', 'href="missing.json"'), rehash=True)

    def test_external_runtime_assets_rejected(self):
        self.altered('index.html', lambda text: text.replace('src="portfolio.js"', 'src="https://example.com/remote.js"'), rehash=True)

    def test_false_boundary_cannot_pass(self):
        self.altered('index.html', lambda text: text.replace('No upstream Runspindle execution', 'Upstream execution'), rehash=True)

    def test_untracked_payload_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'portfolio'
            shutil.copytree(ROOT, root)
            (root / 'data/extra.json').write_text('{}')
            with self.assertRaises(ValueError):
                validate(root)




class ReleaseSelectionTests(unittest.TestCase):
    def archive(self, alter=None):
        index = json.loads((ROOT / 'data/source-evidence-index.json').read_text())
        members = {'evidence-index.json': json.dumps(index).encode()}
        for source in index['runs']:
            run_id = source['runId']
            members[run_id + '/manifest.json'] = (ROOT / 'data/source-manifests' / (run_id + '.json')).read_bytes()
        for run in json.loads((ROOT / 'data/runs.json').read_text()):
            for name in ('verification.json', 'browser-verification.json'):
                members[run['runId'] + '/' + name] = (ROOT / 'media' / run['runId'] / name).read_bytes()
        if alter:
            alter(members)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            for name, raw in members.items():
                archive.writestr(name, raw)
        stream.seek(0)
        return zipfile.ZipFile(stream), {name: sha(raw) for name, raw in members.items()}

    def test_pinned_success_retains_blocked_normal_attempt(self):
        with self.archive()[0] as archive:
            hashes = {name: sha(archive.read(name)) for name in archive.namelist()}
            _, runs, excluded = select_runs(archive, load_release(ROOT), hashes)
        self.assertEqual(len(runs), 7)
        self.assertEqual([(r['case'], r['outcome']) for r in excluded], [('bakery-prep', 'blocked')])
        self.assertTrue(all(r['outcome'] == 'verified' for r in runs))

    def test_source_order_cannot_change_selected_runs(self):
        def alter(members):
            index = json.loads(members['evidence-index.json'])
            index['runs'].reverse()
            members['evidence-index.json'] = json.dumps(index).encode()
        archive, hashes = self.archive(alter)
        with archive:
            _, runs, _ = select_runs(archive, load_release(ROOT), hashes)
        self.assertEqual({r['case']: r['runId'] for r in runs}, load_release(ROOT)['normalRunIds'])

    def test_blocked_run_cannot_be_selected_as_success(self):
        release = load_release(ROOT)
        release['normalRunIds']['bakery-prep'] = 'bakery-prep-5b58e08406c4'
        archive, hashes = self.archive()
        with archive, self.assertRaises(ValueError):
            select_runs(archive, release, hashes)

    def test_wrong_capture_commit_rejected(self):
        release = load_release(ROOT)
        release['recordingCommit'] = '0' * 40
        archive, hashes = self.archive()
        with archive, self.assertRaises(ValueError):
            select_runs(archive, release, hashes)

    def test_duplicate_source_identity_rejected(self):
        def alter(members):
            index = json.loads(members['evidence-index.json'])
            index['runs'][0] = index['runs'][1]
            members['evidence-index.json'] = json.dumps(index).encode()
        archive, hashes = self.archive(alter)
        with archive, self.assertRaises(ValueError):
            select_runs(archive, load_release(ROOT), hashes)

    def test_unsafe_run_id_rejected(self):
        def alter(members):
            index = json.loads(members['evidence-index.json'])
            index['runs'][0]['runId'] = '../escape'
            members['evidence-index.json'] = json.dumps(index).encode()
        archive, hashes = self.archive(alter)
        with archive, self.assertRaises(ValueError):
            select_runs(archive, load_release(ROOT), hashes)

    def test_unsafe_archive_path_rejected(self):
        archive, hashes = self.archive()
        with archive, self.assertRaises(ValueError):
            read_source(archive, hashes, '../outside')

    def test_bad_archive_leaves_existing_payload_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copyfile(ROOT / 'release.json', root / 'release.json')
            (root / 'index.html').write_text('previous content')
            (root / 'bad.zip').write_bytes(b'not the approved archive')
            with self.assertRaises(ValueError):
                build(root / 'bad.zip', root)
            self.assertEqual((root / 'index.html').read_text(), 'previous content')

    def test_excluded_failure_cannot_disappear(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'portfolio'
            shutil.copytree(ROOT, root)
            path = root / 'data/excluded-normal-runs.json'
            path.write_text('[]')
            provenance = json.loads((root / 'data/provenance.json').read_text())
            provenance['excludedNormalRuns'] = []
            (root / 'data/provenance.json').write_text(json.dumps(provenance))
            checksums = json.loads((root / 'checksums.json').read_text())
            for name in ('data/excluded-normal-runs.json', 'data/provenance.json'):
                checksums[name] = sha((root / name).read_bytes())
            (root / 'checksums.json').write_text(json.dumps(checksums))
            with self.assertRaisesRegex(ValueError, 'excluded normal attempt'):
                validate(root)

if __name__ == '__main__':
    unittest.main()
