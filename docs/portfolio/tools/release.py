"""Reviewed release descriptor shared by the offline builder and validator."""
import json
import re
from pathlib import Path, PurePosixPath
REPOSITORY = 'https://github.com/newdarwindev/runspindle-demo-suite'
EXPECTED_CASES = {'bakery-prep', 'bookkeeper-deposit', 'subcontractor-invoices', 'staffing-billing', 'vintage-returns', 'produce-packing', 'consultancy-contract'}

def safe_name(name):
    if not isinstance(name, str) or not name or name in {'.', '..'} or PurePosixPath(name).name != name or '/' in name or '\\' in name:
        raise ValueError('Unsafe evidence name: ' + str(name))
    return name

def load_release(root):
    release = json.loads((Path(root) / 'release.json').read_text())
    if release.get('schemaVersion') != 1:
        raise ValueError('Unsupported release descriptor')
    for field in ('archiveSHA256', 'sourceIndexSHA256', 'sourceChecksumsSHA256'):
        if not re.fullmatch('[0-9a-f]{64}', release.get(field, '')):
            raise ValueError('Invalid release hash: ' + field)
    for field in ('recordingCommit', 'packagingCommit'):
        if not re.fullmatch('[0-9a-f]{40}', release.get(field, '')):
            raise ValueError('Invalid source commit: ' + field)
    if not re.fullmatch('demo-[0-9a-f]{12}', release.get('releaseTag', '')):
        raise ValueError('Invalid release tag')
    if set(release.get('normalRunIds', {})) != EXPECTED_CASES:
        raise ValueError('Descriptor must select seven workflow cases')
    ids = list(release['normalRunIds'].values())
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate selected run identity')
    for name in ids:
        safe_name(name)
    for field in ('sourceRunCount', 'selectedClipCount'):
        if not isinstance(release.get(field), int) or release[field] < 7:
            raise ValueError('Invalid expected count: ' + field)
    history = release['history']
    if not re.fullmatch('demo-[0-9a-f]{12}', history.get('releaseTag', '')) or not re.fullmatch('[0-9a-f]{40}', history.get('portfolioCommit', '')) or not re.fullmatch('[0-9a-f]{64}', history.get('archiveSHA256', '')):
        raise ValueError('Invalid immutable history reference')
    return release

def release_url(release):
    return REPOSITORY + '/releases/tag/' + release['releaseTag']

def download_url(release):
    return REPOSITORY + '/releases/download/' + release['releaseTag']
