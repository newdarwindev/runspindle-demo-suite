# mock-issue-tracker

Fictional browser app in the Runspindle demo suite. Synthetic accounts only.

The parent serves this app at http://localhost:4307. Sessions use origin-local storage and server-side origin/account binding; no cookies shared across ports. Use the visible account selector and sign-in controls for manual presentations. Run from the parent with `python tools/demo.py up`.
