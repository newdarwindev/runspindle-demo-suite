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
COMMIT = '085a776b2328862f30fe6539ef41ad1a3ed52eb4'
RELEASE = 'https://github.com/newdarwindev/runspindle-demo-suite/releases/tag/demo-085a776b2328'
DOWNLOAD = RELEASE.replace('/tag/', '/download/')
ARCHIVE_SHA256 = 'dee8aebf13e0a9a48326645491ad76d754fd31b7df787ea4a1bf5bd06e78185a'
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


def select_runs(archive):
    index = json.loads(archive.read('evidence-index.json'))
    if index['fixtureOnly'] is not True or index['upstreamExecuted'] is not False:
        raise ValueError('Not a standalone fixture release')
    selected = {}
    for run in index['runs']:
        manifest = json.loads(archive.read(run['runId'] + '/manifest.json'))
        if manifest.get('fault') != 'normal':
            continue
        case = run['case']
        if case not in CASES or case in selected:
            raise ValueError('Unexpected or duplicate normal case: ' + case)
        verify = json.loads(archive.read(run['runId'] + '/verification.json'))
        observer = json.loads(archive.read(run['runId'] + '/browser-verification.json'))
        if not (run['outcome'] == manifest['outcome'] == 'verified' and verify['passed'] is True
                and all(v is True for v in verify['checks'].values()) and observer['verified'] is True
                and manifest['upstreamExecuted'] is False and manifest['parentCommit'] == COMMIT):
            raise ValueError('Normal case did not meet the evidence boundary: ' + case)
        selected[case] = {**run, 'fault': 'normal', 'result': verify['result'],
                          'title': CASES[case][1], 'label': CASES[case][0]}
    if set(selected) != set(CASES):
        raise ValueError('Incomplete normal workflow coverage')
    return index, [selected[case] for case in CASES]


def make_card(run, number):
    case = run['case']
    label, title, description, outcome = CASES[case]
    base = 'media/' + run['runId'] + '/'
    clips = run['media']
    # Prefer a detailed original poster over a blank initial page. No frames are generated.
    chosen = max(range(len(clips)), key=lambda i: (ROOT / base / clips[i]['poster']).stat().st_size)
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


def build(zip_path):
    source_bytes = zip_path.read_bytes()
    if digest(source_bytes) != ARCHIVE_SHA256:
        raise ValueError('Archive SHA256 differs from the verified release; review provenance before changing the pin')
    copied = {}
    with zipfile.ZipFile(zip_path) as archive:
        source_hashes = json.loads(archive.read('checksums.json'))
        index, runs = select_runs(archive)
        for run in runs:
            names = set(ALLOWED) & {PurePosixPath(n).name for n in archive.namelist() if n.startswith(run['runId'] + '/')}
            for media in run['media']:
                names.update(media[key] for key in ('clip', 'poster', 'captions'))
            for name in sorted(names):
                if PurePosixPath(name).name != name:
                    raise ValueError('Unsafe archive member')
                member = run['runId'] + '/' + name
                raw = archive.read(member)
                if digest(raw) != source_hashes[member]:
                    raise ValueError('Release checksum mismatch: ' + member)
                dest = ROOT / 'media' / member
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(raw)
                copied[dest.relative_to(ROOT).as_posix()] = {'archivePath': member, 'sha256': digest(raw)}
        data = ROOT / 'data'
        data.mkdir(exist_ok=True)
        (data / 'source-evidence-index.json').write_bytes(archive.read('evidence-index.json'))
        (data / 'source-checksums.json').write_bytes(archive.read('checksums.json'))
        (data / 'fault-matrix.json').write_bytes(archive.read('fault-matrix.json'))
        (data / 'runs.json').write_text(encoded(runs))
        provenance = {
            'fixtureOnly': True, 'upstreamExecuted': False, 'sourceRelease': RELEASE,
            'sourceArchiveURL': DOWNLOAD + '/presentation.zip', 'sourceArchiveSHA256': ARCHIVE_SHA256,
            'parentCommit': COMMIT, 'selectedScenario': 'normal', 'selectedRuns': len(runs),
            'sourceRuns': len(index['runs']), 'copiedFiles': copied,
            'mediaTransformation': 'none; original archive bytes copied exactly',
            'sourceIndexSHA256': digest(archive.read('evidence-index.json')),
            'sourceChecksumsSHA256': digest(archive.read('checksums.json')),
            'reel': {'url': DOWNLOAD + '/combined-reel.mp4', **index['reel']},
        }
        (data / 'provenance.json').write_text(encoded(provenance))
    template = (ROOT / 'tools' / 'template.html').read_text()
    nav = ''.join(f'<a href="#{case}"><span>{i:02}</span>{esc(values[0])}</a>' for i, (case, values) in enumerate(CASES.items(), 1))
    page = template.replace('{{NAV}}', nav).replace('{{CASES}}', '\n'.join(make_card(run, i) for i, run in enumerate(runs, 1)))
    (ROOT / 'index.html').write_text(page)
    paths = [ROOT / name for name in ('index.html', 'styles.css', 'portfolio.js')]
    paths += [p for folder in ('media', 'data') for p in (ROOT / folder).rglob('*') if p.is_file()]
    manifest = {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(paths)}
    (ROOT / 'checksums.json').write_text(encoded(manifest))
    print(encoded({'normalRuns': len(runs), 'clips': sum(len(r['media']) for r in runs), 'copiedEvidenceFiles': len(copied), 'totalBytes': sum(p.stat().st_size for p in paths)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip', type=Path, help='Downloaded original presentation.zip for demo-085a776b2328')
    build(parser.parse_args().zip)
