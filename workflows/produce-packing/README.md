# Pack confirmed orders, surface gaps

Fictional demo execution.

Accounts and permitted scope: {"mock-supplier-portal": "produce-supplier", "mock-excel": "produce"}; read source records and edit only this case’s workbook rows.

Start: reset fixture; existing workbook preserves unrelated rows/formulas.

Exception: Expired Bistro access becomes Unavailable / incomplete, not zero, until restored.

Independent expected result: {"tomatoes": 6}

From recursive parent checkout: `python tools/demo.py reset produce-packing`, `python tools/demo.py run produce-packing`, `python tools/demo.py record produce-packing`.
