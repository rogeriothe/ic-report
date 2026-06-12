# tabularium

Reusable PDF/Excel/CSV reporting helpers based on FPDF. The package provides a simple base class (`Report`) with grouping, totals, and layout rules.

## Install (uv)
```bash
uv pip install tabularium
```

For local development:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Quick start
```python
from collections import OrderedDict
from tabularium import Report, REPORT_PDF

class SimpleReport(Report):
    def layout(self):
        return OrderedDict({
            "name": {"w": 0, "w_type": "S", "caption": "Name"},
            "qty": {"w": 20, "w_type": "F", "caption": "Qty", "align": "R", "datatype": int},
            "price": {"w": 30, "w_type": "F", "caption": "Price", "align": "R"},
        })

    def data(self):
        return [
            {"name": "Item A", "qty": 2, "price": 12.5},
            {"name": "Item B", "qty": 1, "price": 7.0},
        ]

params = {"format": REPORT_PDF, "orientation": "L"}
report = SimpleReport(params)
filename, mimetype, buffer = report.generate()

with open(filename, "wb") as f:
    f.write(buffer.getvalue())
```

## Documentation
- `docs/USAGE.md`
- `docs/REFERENCE.md`

## Build and publish (uv)
```bash
uv build
uv publish
```

## Examples
See `examples/` for report classes adapted from the original application. These examples depend on the original app models and queries and are not standalone.

## License
MIT
