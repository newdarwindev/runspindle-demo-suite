# From a small contract to a reviewed fix

Fictional demo execution.

Accounts and permitted scope: {"mock-job-board": "consultant", "mock-applicant-portal": "consultant", "mock-mail": "consultant", "mock-interview-room": "consultant", "mock-coderpad": "consultant", "mock-issue-tracker": "customer-maintenance", "mock-code-workspace": "customer-maintenance", "mock-excel": "consultant"}; read source records and edit only this case’s workbook rows.

Start: reset fixture; existing workbook preserves unrelated rows/formulas.

Exception: Separate assessment forbids assistance and must remain a human step.

Independent expected result: {"openJobs": 2, "originalRows": 6, "correctedRows": 10, "issue": "47", "status": "Ready for review"}

From recursive parent checkout: `python tools/demo.py reset consultancy-contract`, `python tools/demo.py run consultancy-contract`, `python tools/demo.py record consultancy-contract`.
