"""Exercise publication verification against a real HTTP server at the project path."""

import json
import tempfile
import unittest
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from verify_pages import PORTFOLIO_PATH, PROJECT_PATH, ROOT, verify_pages


@contextmanager
def hosted_portfolio(overrides=None):
    overrides = overrides or {}
    observed = []
    with tempfile.TemporaryDirectory() as directory:
        (Path(directory) / PROJECT_PATH.strip("/")).symlink_to(ROOT.parent)

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

            def do_GET(self):
                observed.append(self.path)
                if self.path in overrides:
                    status, headers, body = overrides[self.path]
                    self.send_response(status)
                    for name, value in headers.items():
                        self.send_header(name, value)
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    super().do_GET()

            def log_message(self, format, *args):
                pass

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
            thread.start()
            try:
                yield f"http://127.0.0.1:{server.server_port}", observed
            finally:
                server.shutdown()
                thread.join(timeout=5)


class PagesTests(unittest.TestCase):
    def test_whole_portfolio_and_entry_page_match_at_the_project_path(self):
        with hosted_portfolio() as (origin, paths):
            report = verify_pages(origin)
        self.assertEqual(report["workflows"], 7)
        self.assertEqual(report["clipsVerified"], 31)
        self.assertEqual(report["responsesVerified"], 178)
        self.assertEqual(len(set(paths)), report["responsesVerified"])
        self.assertIn(PROJECT_PATH, paths)
        self.assertIn(PORTFOLIO_PATH, paths)
        self.assertTrue(all(path.startswith(PROJECT_PATH) for path in paths))

    def test_unpublished_and_redirected_entry_points_cannot_pass(self):
        for status, headers in [(404, {}), (302, {"Location": "/unexpected/"})]:
            with (
                self.subTest(status=status),
                hosted_portfolio({PROJECT_PATH: (status, headers, b"")}) as (
                    origin,
                    paths,
                ),
            ):
                with self.assertRaisesRegex(ValueError, f"HTTP {status}"):
                    verify_pages(origin)
                self.assertEqual(paths, [PROJECT_PATH])

    def test_changed_served_bytes_fail_even_with_a_valid_checked_out_manifest(self):
        with hosted_portfolio(
            {
                PORTFOLIO_PATH + "data/runs.json": (
                    200,
                    {"Content-Type": "application/json"},
                    b"[]",
                )
            }
        ) as (origin, _):
            with self.assertRaisesRegex(
                ValueError, "Served bytes differ.+data/runs.json"
            ):
                verify_pages(origin)

    def test_webm_must_be_served_as_video(self):
        run = json.loads((ROOT / "data/runs.json").read_text())[0]
        raw_path = f"media/{run['runId']}/{run['media'][0]['clip']}"
        with hosted_portfolio(
            {
                PORTFOLIO_PATH + raw_path: (
                    200,
                    {"Content-Type": "text/plain"},
                    (ROOT / raw_path).read_bytes(),
                )
            }
        ) as (origin, _):
            with self.assertRaisesRegex(ValueError, "Unexpected content type.+webm"):
                verify_pages(origin)
