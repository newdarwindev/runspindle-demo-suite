#!/usr/bin/env python3
"""Reproduce the static portfolio from an immutable, already released ZIP.

No workflows execute, upstream code is not fetched, and original media bytes are
never transformed. Only allowlisted evidence from normal verified runs is copied.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]
from release import EXPECTED_CASES, REPOSITORY, safe_name, load_release, release_url, download_url
import shutil
import stat
import tempfile
from datetime import datetime, timezone

CASES = {
    'bakery-prep': ('Bakery prep', 'Tomorrow, ready to bake', 'Turn paid orders and the fixture operator’s pickup choice into a prep workbook.', '3 loaves · 16 rolls'),
    'bookkeeper-deposit': ('Bookkeeping', 'One deposit, one paid invoice', 'Match a deposit reference to its invoice in a fictional business ledger.', 'Invoice 107 · Paid · amount 540'),
    'subcontractor-invoices': ('Subcontractor invoices', 'Know what needs attention', 'Keep each invoice’s approval state and missing document distinct.', 'C-104: missing signed work ticket · C-112: approved'),
    'staffing-billing': ('Staffing billing', 'Bill approved hours, flag the rest', 'Separate approved and pending time before preparing the billing workbook.', '36 approved · 4 pending'),
    'vintage-returns': ('Vintage returns', 'A label is not a returned parcel', 'Use carrier evidence to distinguish an in-transit return from a pending one.', 'R1: In transit · R2: Pending'),
    'produce-packing': ('Produce packing', 'Pack confirmed orders', 'Count confirmed produce orders in the packing workbook.', 'tomatoes: 6'),
    'consultancy-contract': ('Consultancy contract', 'From contract to reviewed fix', 'Follow a fictional job, code correction, issue and review workflow.', '2 open jobs · 6 → 10 rows · issue 47 ready for review'),
}
ALLOWED = {'manifest.json', 'verification.json', 'browser-verification.json', 'events.json',
           'result.png', 'independent-observer.png', 'artifact.json', 'accepted.csv', 'delivered.csv'}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def esc(value):
    return html.escape(str(value), quote=True)


def read_source(archive, hashes, member):
    parts = PurePosixPath(member).parts
    if not parts or any(part in {'.', '..'} for part in parts) or member.startswith('/') or '\\' in member:
        raise ValueError('Unsafe archive path')
    info = archive.getinfo(member)
    if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
        raise ValueError('Archive evidence must be a regular file')
    raw = archive.read(member)
    if digest(raw) != hashes.get(member):
        raise ValueError('Release checksum mismatch: ' + member)
    return raw


def select_runs(archive, release, hashes):
    index = json.loads(read_source(archive, hashes, 'evidence-index.json'))
    if index['fixtureOnly'] is not True or index['upstreamExecuted'] is not False:
        raise ValueError('Not a standalone fixture release')
    if len(index['runs']) != release['sourceRunCount']:
        raise ValueError('Source run count differs from descriptor')
    selected = {}
    excluded = []
    seen = set()
    for run in index['runs']:
        run_id = safe_name(run['runId'])
        if run_id in seen:
            raise ValueError('Duplicate source run identity')
        seen.add(run_id)
        manifest = json.loads(read_source(archive, hashes, run_id + '/manifest.json'))
        if manifest.get('fault') != 'normal':
            continue
        case = run['case']
        if manifest['runId'] != run_id or manifest['case'] != case or manifest['outcome'] != run['outcome']:
            raise ValueError('Run identity or outcome mismatch')
        if release['normalRunIds'].get(case) != run_id:
            excluded.append({'runId': run_id, 'case': case, 'outcome': run['outcome'],
                             'reason': 'Not a verified completion' if run['outcome'] != 'verified' else 'Not selected by the reviewed release descriptor'})
            continue
        if run['outcome'] != 'verified':
            raise ValueError('Descriptor selects a nonverified normal attempt')
        verify = json.loads(read_source(archive, hashes, run_id + '/verification.json'))
        observer = json.loads(read_source(archive, hashes, run_id + '/browser-verification.json'))
        if not (run['outcome'] == 'verified' and verify['passed'] is True and verify['checks']
                and all(v is True for v in verify['checks'].values()) and observer['verified'] is True
                and observer['case'] == case and manifest['upstreamExecuted'] is False
                and manifest['parentCommit'] == run['parentCommit'] == release['recordingCommit']
                and manifest['childCommits'] == run['childCommits'] and len(run['childCommits']) == 21
                and manifest['checks'] == run['checks'] == verify['checks'] and run['media'] and not run['missing']):
            raise ValueError('Selected normal case did not meet the evidence boundary: ' + case)
        selected[case] = {**run, 'fault': 'normal', 'result': verify['result'],
                          'title': CASES[case][1], 'label': CASES[case][0],
                          'recordedAtUTC': datetime.fromtimestamp(manifest['startedAt'], timezone.utc).isoformat()}
    if set(selected) != EXPECTED_CASES:
        raise ValueError('Missing selected verified normal workflows')
    if sum(len(r['media']) for r in selected.values()) != release['selectedClipCount']:
        raise ValueError('Selected clip count differs from descriptor')
    return index, [selected[case] for case in CASES], sorted(excluded, key=lambda r: r['runId'])


def make_card(run, number, output=ROOT):
    case = run['case']
    label, title, description, _ = CASES[case]
    outcome = ' · '.join(f'{key}: {value}' for key, value in run['result'].items())
    base = 'media/' + run['runId'] + '/'
    clips = run['media']
    # Prefer a detailed original poster over a blank initial page. No frames are generated.
    chosen = max(range(len(clips)), key=lambda i: (output / base / clips[i]['poster']).stat().st_size)
    current = clips[chosen]
    options = '\n'.join(f'<option value="{i}"{(" selected" if i == chosen else "")}>Capture {i+1} · {m["durationSeconds"]:.2f}s original</option>' for i, m in enumerate(clips))
    links = ''.join(f'<li><a href="{base}{esc(m["clip"])}">Capture {i+1} ({m["durationSeconds"]:.2f}s)</a></li>' for i, m in enumerate(clips))
    result = ''.join(f'<div><dt>{esc(key)}</dt><dd>{esc(value)}</dd></div>' for key, value in run['result'].items())
    checks = ''.join(f'<li>{esc(key.replace("_", " "))}</li>' for key in run['checks'])
    workflow = f'https://github.com/newdarwindev/runspindle-demo-{case}/tree/{run["childCommits"]["workflows/"+case]}'
    return f'''<article class="case" id="{case}" data-case="{case}">
  <header class="case-header"><div><p class="eyebrow">{number:02} / {esc(label)}</p><h2>{esc(title)}</h2><p>{esc(description)}</p></div><span class="badge">Verified fixture</span></header>
  <p class="outcome">{esc(outcome)}</p>
  <div class="case-grid">
    <section class="media-panel" aria-label="{esc(label)} recordings">
      <div class="panel-heading"><h3>Recorded browser captures</h3><span>{len(clips)} raw clips</span></div>
      <video id="video-{case}" controls playsinline preload="none" muted poster="{base}{current['poster']}" aria-label="{esc(label)} raw page capture" aria-describedby="clip-note-{case}">
        <source src="{base}{current['clip']}" type="video/webm"><track kind="captions" src="{base}{current['captions']}" srclang="en" label="Fixture context">
        Your browser cannot play WebM. Open a clip below or use the MP4 reel.
      </video>
      <div class="controls" hidden>
        <label>Page capture<select class="clip-select" aria-controls="video-{case}">{options}</select></label>
        <label>Playback speed<select class="speed-select" aria-controls="video-{case}"><option value="0.25" selected>¼× slow</option><option value="0.5">½×</option><option value="1">1× original</option></select></label>
        <button class="replay" type="button" aria-controls="video-{case}">Replay</button>
      </div>
      <p class="media-note" id="clip-note-{case}">Short, separate page captures, not a complete human-paced walkthrough. Original durations shown. Slow playback changes viewing speed only.</p>
      <p class="playback-status" role="status" aria-live="polite"></p>
      <details class="download-list"><summary>Open individual clips ({len(clips)})</summary><ol>{links}</ol></details>
    </section>
    <section class="media-panel" aria-label="{esc(label)} result evidence">
      <div class="panel-heading"><h3>Saved result</h3><a href="{base}result.png">Full size ↗</a></div>
      <a class="result-image" href="{base}result.png"><img src="{base}result.png" width="1280" height="800" loading="lazy" alt="Original {esc(label)} saved workbook result screenshot. Exact result is transcribed below."></a>
      <p class="media-note">Original screenshot from this run. A separate fresh-browser readback also passed.</p>
      <a class="observer-link" href="{base}independent-observer.png">View independent observer screenshot ↗</a>
    </section>
  </div>
  <details class="evidence"><summary>Inspect exact outcome &amp; evidence <span>{len(run['checks'])} passed checks</span></summary>
    <div class="evidence-grid"><div><h3>Exact verification result</h3><dl class="result-values">{result}</dl><p class="run-id">Run: {esc(run['runId'])}</p><p class="small">Recorded {esc(run['fault'])} scenario. Results below come from the archived verification JSON, not estimates.</p></div><div><h3>Passed independent checks</h3><ul class="check-list">{checks}</ul></div></div>
    <nav class="evidence-links" aria-label="{esc(label)} source evidence"><a href="{base}verification.json">Verification JSON</a><a href="{base}browser-verification.json">Fresh-browser readback</a><a href="{base}manifest.json">Original run manifest</a><a href="{base}events.json">Event log</a><a href="{workflow}">Pinned workflow source ↗</a></nav>
  </details>
</article>'''


def build(zip_path, root=ROOT):
    root = Path(root).resolve()
    release = load_release(root)
    if digest(zip_path.read_bytes()) != release['archiveSHA256']:
        raise ValueError('Archive SHA256 differs from the reviewed release descriptor')
    # Reject symlinked destinations before replacing only the generated payload.
    for name in ('media', 'data', 'excluded', 'index.html', 'checksums.json'):
        target = root / name
        if target.is_symlink() or (target.is_dir() and any(p.is_symlink() for p in target.rglob('*'))):
            raise ValueError('Symlinked output is not allowed: ' + name)
    with tempfile.TemporaryDirectory(prefix='.portfolio-build-', dir=root) as temp:
        output = Path(temp)
        copied = {}
        with zipfile.ZipFile(zip_path) as archive:
            if len(archive.namelist()) != len(set(archive.namelist())):
                raise ValueError('Duplicate archive members')
            hashes_raw = archive.read('checksums.json')
            if digest(hashes_raw) != release['sourceChecksumsSHA256']:
                raise ValueError('Source checksum document differs from descriptor')
            hashes = json.loads(hashes_raw)
            index, runs, excluded = select_runs(archive, release, hashes)
            if digest(archive.read('evidence-index.json')) != release['sourceIndexSHA256']:
                raise ValueError('Source index differs from descriptor')
            def copy_member(member, destination):
                raw = read_source(archive, hashes, member)
                target = output / destination
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                copied[destination] = {'archivePath': member, 'sha256': digest(raw)}
            for source_run in index['runs']:
                member = safe_name(source_run['runId']) + '/manifest.json'
                copy_member(member, 'data/source-manifests/' + source_run['runId'] + '.json')
            for run in runs:
                names = {name for name in ALLOWED if run['runId'] + '/' + name in hashes}
                for media in run['media']:
                    names.update(safe_name(media[key]) for key in ('clip', 'poster', 'captions'))
                for name in sorted(names):
                    member = run['runId'] + '/' + safe_name(name)
                    copy_member(member, 'media/' + member)
            for run in excluded:
                run['evidence'] = []
                for name in ('manifest.json', 'verification.json', 'worker.json'):
                    member = run['runId'] + '/' + name
                    if member in hashes:
                        destination = 'excluded/' + member
                        copy_member(member, destination)
                        run['evidence'].append(destination)
            data = output / 'data'
            data.mkdir(exist_ok=True)
            (data / 'source-evidence-index.json').write_bytes(read_source(archive, hashes, 'evidence-index.json'))
            (data / 'source-checksums.json').write_bytes(hashes_raw)
            (data / 'fault-matrix.json').write_bytes(read_source(archive, hashes, 'fault-matrix.json'))
            (data / 'runs.json').write_text(encoded(runs))
            (data / 'excluded-normal-runs.json').write_text(encoded(excluded))
            provenance = {
                'fixtureOnly': True, 'upstreamExecuted': False, 'sourceRelease': release_url(release),
                'sourceArchiveURL': download_url(release) + '/presentation.zip', 'sourceArchiveSHA256': release['archiveSHA256'],
                'recordingCommit': release['recordingCommit'], 'packagingCommit': release['packagingCommit'],
                'selectedScenario': 'normal', 'selectionPolicy': 'Exact run IDs in reviewed release.json; all selected runs must independently verify',
                'selectedRuns': len(runs), 'sourceRuns': len(index['runs']), 'copiedFiles': copied,
                'excludedNormalRuns': excluded, 'recordingContext': release['recordingContext'], 'history': release['history'],
                'mediaTransformation': 'none; original archive bytes copied exactly',
                'sourceIndexSHA256': release['sourceIndexSHA256'], 'sourceChecksumsSHA256': release['sourceChecksumsSHA256'],
                'reel': {'url': download_url(release) + '/' + index['reel']['path'],
                         'portableURL': download_url(release) + '/' + index['reel']['portablePath'], **index['reel']},
            }
            (data / 'provenance.json').write_text(encoded(provenance))
        nav = ''.join(f'<a href="#{case}"><span>{i:02}</span>{esc(values[0])}</a>' for i, (case, values) in enumerate(CASES.items(), 1))
        excluded_html = ''.join('<li><strong>' + esc(r['runId']) + '</strong>: ' + esc(r['outcome']) + '. ' + esc(r['reason']) + '. ' + ' · '.join('<a href="'+esc(link)+'">'+esc(Path(link).name)+'</a>' for link in r['evidence']) + '</li>' for r in excluded)
        durations = [m['durationSeconds'] for r in runs for m in r['media']]
        replacements = {
            'NAV': nav, 'CASES': '\n'.join(make_card(run, i, output) for i, run in enumerate(runs, 1)),
            'RELEASE_URL': release_url(release), 'DOWNLOAD_URL': download_url(release),
            'RELEASE_TAG': release['releaseTag'], 'SOURCE_RUNS': str(len(index['runs'])),
            'CLIPS': str(len(durations)), 'DURATION_RANGE': f'{min(durations):.2f}–{max(durations):.2f}',
            'EXCLUDED': excluded_html or '<li>No normal runs excluded.</li>',
            'RECORDING_COMMIT': release['recordingCommit'], 'PACKAGING_COMMIT': release['packagingCommit'],
            'RECORDING_SHORT': release['recordingCommit'][:12], 'PACKAGING_SHORT': release['packagingCommit'][:12],
            'RECORDED_DATE': runs[0]['recordedAtUTC'][:10], 'HISTORY_TAG': release['history']['releaseTag'],
            'HISTORY_COMMIT': release['history']['portfolioCommit'], 'RECORDING_CONTEXT': esc(release['recordingContext']),
        }
        page = (root / 'tools/template.html').read_text()
        for key, value in replacements.items():
            page = page.replace('{{' + key + '}}', value)
        if '{{' in page:
            raise ValueError('Unresolved template placeholder')
        (output / 'index.html').write_text(page)
        for name in ('styles.css', 'portfolio.js', 'release.json'):
            (output / name).write_bytes((root / name).read_bytes())
        paths = sorted(p for p in output.rglob('*') if p.is_file())
        manifest = {p.relative_to(output).as_posix(): digest(p.read_bytes()) for p in paths}
        (output / 'checksums.json').write_text(encoded(manifest))
        for name in ('media', 'data', 'excluded'):
            if (root / name).exists():
                shutil.rmtree(root / name)
            if (output / name).exists():
                shutil.move(str(output / name), str(root / name))
        for name in ('index.html', 'checksums.json'):
            (root / name).write_bytes((output / name).read_bytes())
    result = {'normalRuns': len(runs), 'sourceRuns': len(index['runs']), 'excludedNormalRuns': len(excluded),
              'clips': len(durations), 'copiedEvidenceFiles': len(copied),
              'totalBytes': sum((root / path).stat().st_size for path in manifest)}
    print(encoded(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip', type=Path, help='Original presentation.zip matching the reviewed release.json')
    build(parser.parse_args().zip)
