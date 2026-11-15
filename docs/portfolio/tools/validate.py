#!/usr/bin/env python3
"""Offline portfolio integrity, provenance, link and evidence validator."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CASES = {'bakery-prep', 'bookkeeper-deposit', 'subcontractor-invoices', 'staffing-billing',
                  'vintage-returns', 'produce-packing', 'consultancy-contract'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.local = []
        self.fragments = []
        self.ids = []
        self.videos = 0
        self.external_assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'video':
            self.videos += 1
            require('controls' in attrs, 'Video must retain native controls')
            require('autoplay' not in attrs, 'Autoplay not allowed')
        if tag == 'img':
            require(bool(attrs.get('alt')), 'Image missing descriptive alt text')
        for key in ('href', 'src', 'poster'):
            if key not in attrs:
                continue
            parsed = urlsplit(attrs[key])
            if parsed.scheme or parsed.netloc:
                if tag != 'a':
                    self.external_assets.append(attrs[key])
            elif parsed.path:
                self.local.append(unquote(parsed.path))
            elif parsed.fragment:
                self.fragments.append(parsed.fragment)


def validate(root=ROOT, probe=False):
    manifest = json.loads((root / 'checksums.json').read_text())
    actual = {'index.html', 'styles.css', 'portfolio.js'} | {
        p.relative_to(root).as_posix() for folder in ('data', 'media')
        for p in (root / folder).rglob('*') if p.is_file()
    }
    require(set(manifest) == actual, 'Untracked or missing portfolio payload')
    for name, expected in manifest.items():
        path = (root / name).resolve()
        require(path.is_relative_to(root.resolve()), 'Unsafe manifest path')
        require(path.is_file() and sha(path.read_bytes()) == expected, 'Hash mismatch: ' + name)
    parser = Links()
    html = (root / 'index.html').read_text()
    parser.feed(html)
    require(not parser.external_assets, 'Portfolio assets must be self-contained')
    require(parser.videos == 7, 'Expected seven native video players')
    require(len(parser.ids) == len(set(parser.ids)), 'Duplicate HTML IDs')
    require(set(parser.fragments) <= set(parser.ids), 'Broken in-page anchor')
    for path in parser.local:
        require((root / path).is_file(), 'Broken local link: ' + path)
    for disclosure in ('No upstream Runspindle execution', 'not a complete human-paced walkthrough',
                       'No claim that these archived runs used a local runner', 'No real accounts or payments'):
        require(disclosure in html, 'Missing evidence disclosure: ' + disclosure)
    provenance = json.loads((root / 'data/provenance.json').read_text())
    source_hashes = json.loads((root / 'data/source-checksums.json').read_text())
    source_index = json.loads((root / 'data/source-evidence-index.json').read_text())
    require(provenance['fixtureOnly'] is True and provenance['upstreamExecuted'] is False, 'Invalid fixture boundary')
    require(provenance['sourceRuns'] == len(source_index['runs']) == 24, 'Source run count differs')
    require(sha((root / 'data/source-evidence-index.json').read_bytes()) == provenance['sourceIndexSHA256'], 'Source index changed')
    require(sha((root / 'data/source-checksums.json').read_bytes()) == provenance['sourceChecksumsSHA256'], 'Source checksums changed')
    require(source_hashes['evidence-index.json'] == provenance['sourceIndexSHA256'], 'Index differs from original release checksums')
    require(sha((root / 'data/fault-matrix.json').read_bytes()) == source_hashes['fault-matrix.json'], 'Fault matrix changed')
    originals = {r['runId']: r for r in source_index['runs']}
    runs = json.loads((root / 'data/runs.json').read_text())
    require({r['case'] for r in runs} == EXPECTED_CASES and len(runs) == 7, 'Normal workflow coverage differs')
    copied = provenance['copiedFiles']
    require(set(copied) == {p for p in manifest if p.startswith('media/')}, 'Media provenance incomplete')
    for name, source in copied.items():
        require(manifest[name] == source['sha256'] == source_hashes[source['archivePath']], 'Original byte provenance mismatch: ' + name)
    clips = []
    for run in runs:
        base = root / 'media' / run['runId']
        original = originals[run['runId']]
        run_manifest = json.loads((base / 'manifest.json').read_text())
        verification = json.loads((base / 'verification.json').read_text())
        browser = json.loads((base / 'browser-verification.json').read_text())
        require(run_manifest['fault'] == run['fault'] == 'normal', 'Not a normal scenario')
        require(run['outcome'] == run_manifest['outcome'] == original['outcome'] == 'verified', 'Nonverified normal run')
        require(verification['passed'] is True and browser['verified'] is True, 'Missing passing independent verification')
        require(all(v is True for v in verification['checks'].values()), 'A check did not pass')
        require(run['result'] == verification['result'], 'Result differs from exact verification')
        require(run['checks'] == verification['checks'] == original['checks'], 'Displayed checks differ')
        require(run['parentCommit'] == run_manifest['parentCommit'] == provenance['parentCommit'], 'Source commit differs')
        require(run['media'] == original['media'], 'Original clip metadata differs')
        require(run['childCommits'] == run_manifest['childCommits'], 'Child source provenance differs')
        require(run_manifest['upstreamExecuted'] is False, 'Upstream integration cannot be claimed')
        for media in run['media']:
            for key in ('clip', 'poster', 'captions'):
                require((base / media[key]).is_file(), 'Missing media: ' + media[key])
            require(media['durationSeconds'] > 0, 'Missing original duration')
            if probe:
                result = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(base / media['clip'])])
                actual_duration = float(json.loads(result)['format']['duration'])
                require(abs(actual_duration - media['durationSeconds']) < .05, 'Media duration differs')
            clips.append(media)
    require(len(clips) == 31, 'Expected 31 original clips')
    return {'status': 'passed', 'normalRuns': len(runs), 'clips': len(clips), 'sourceMatchedFiles': len(copied),
            'hashedFiles': len(manifest), 'localLinksChecked': len(parser.local), 'durationProbe': probe,
            'payloadBytes': sum((root / p).stat().st_size for p in manifest)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', action='store_true', help='Also inspect all 31 clips with ffprobe')
    args = parser.parse_args()
    print(json.dumps(validate(probe=args.probe), indent=2))
