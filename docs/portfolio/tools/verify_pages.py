#!/usr/bin/env python3
"""Read-only verification of the branch-published portfolio and its evidence bytes."""

import json
from http.client import HTTPException
from time import monotonic
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

from validate import ROOT, require, sha, validate

ORIGIN = "https://newdarwindev.github.io"
PROJECT_PATH = "/runspindle-demo-suite/"
PORTFOLIO_PATH = PROJECT_PATH + "portfolio/"
CONTENT_TYPES = {
    ".html": {"text/html"},
    ".css": {"text/css"},
    ".js": {"application/javascript", "text/javascript"},
    ".webm": {"video/webm"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".vtt": {"text/vtt"},
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def verify_pages(origin=ORIGIN, root=ROOT):
    local = validate(root)
    require((root.parent / ".nojekyll").is_file(), "Missing branch Pages marker")
    manifest_path = root / "checksums.json"
    manifest = json.loads(manifest_path.read_bytes())
    files = [(PROJECT_PATH, root.parent / "index.html", None)]
    files.append((PORTFOLIO_PATH + "checksums.json", manifest_path, None))
    files.extend(
        (
            PORTFOLIO_PATH + (quote(name, safe="/") if name != "index.html" else ""),
            root / name,
            digest,
        )
        for name, digest in sorted(manifest.items())
    )
    opener = build_opener(NoRedirect())
    deadline = monotonic() + 120
    for path, source, digest in files:
        remaining = deadline - monotonic()
        require(remaining > 0, "Pages verification deadline exceeded")
        request = Request(origin + path, headers={"Accept-Encoding": "identity"})
        expected_size = source.stat().st_size
        expected = digest if digest is not None else sha(source.read_bytes())
        try:
            with opener.open(request, timeout=min(8, remaining)) as response:
                require(response.status == 200, f"Unexpected HTTP status for {path}")
                supported = CONTENT_TYPES.get(source.suffix)
                require(
                    supported is None
                    or response.headers.get_content_type() in supported,
                    f"Unexpected content type for {path}",
                )
                actual = response.read(expected_size + 1)
        except HTTPError as error:
            error.close()
            raise ValueError(f"HTTP {error.code} for {path}") from None
        except (HTTPException, OSError):
            raise ValueError(f"Unable to read {path}") from None
        require(
            len(actual) == expected_size and sha(actual) == expected,
            f"Served bytes differ from the checked-out portfolio for {path}",
        )
    return {
        "status": "passed",
        "url": origin + PORTFOLIO_PATH,
        "release": local["release"],
        "responsesVerified": len(files),
        "workflows": local["normalRuns"],
        "clipsVerified": local["clips"],
    }


if __name__ == "__main__":
    try:
        print(json.dumps(verify_pages(), indent=2))
    except ValueError as error:
        raise SystemExit(f"Pages verification failed: {error}") from None
