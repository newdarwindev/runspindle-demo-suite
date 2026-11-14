# Bill approved hours, flag the rest

Fictional demo execution.

Accounts and permitted scope: {"mock-timesheet-portal": "coordinator", "mock-excel": "staffing"}; read source records and edit only this case’s workbook rows.

Start: reset fixture; existing workbook preserves unrelated rows/formulas.

Exception: Client sign-in prompt requires fresh client/worker/week verification.

Independent expected result: {"approved": 36, "pending": 4}

From recursive parent checkout: `python tools/demo.py reset staffing-billing`, `python tools/demo.py run staffing-billing`, `python tools/demo.py record staffing-billing`.
