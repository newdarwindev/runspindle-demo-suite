#!/usr/bin/env python3
"""Focused regression tests, including negative evidence-integrity cases."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from validate import ROOT, validate, sha


class PortfolioTests(unittest.TestCase):
    def test_checked_in_portfolio(self):
        self.assertEqual(validate()['clips'], 31)

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


if __name__ == '__main__':
    unittest.main()
