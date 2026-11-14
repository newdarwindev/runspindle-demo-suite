# Know which invoice needs attention

Fictional demo execution.

Accounts and permitted scope: {"mock-vendor-portal": "electric-company", "mock-excel": "electric"}; read source records and edit only this case’s workbook rows.

Start: reset fixture; existing workbook preserves unrelated rows/formulas.

Exception: GC-South expires after GC-North check; resume library/C-112 and retain verified C-104.

Independent expected result: {"C-104": "Missing signed work ticket", "C-112": "Approved"}

From recursive parent checkout: `python tools/demo.py reset subcontractor-invoices`, `python tools/demo.py run subcontractor-invoices`, `python tools/demo.py record subcontractor-invoices`.
