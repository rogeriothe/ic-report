# Usage

This package provides a base class `Report` that renders PDF tables (and exports to Excel/CSV). To use it, you create a subclass and implement `layout()` and `data()`.

## Params
`params` is a simple dict. Common keys:
- `format`: `pdf`, `excel`, `csv`.
- `orientation`: `P` or `L`.
- any custom data your report needs (ex: user, company, filters).

## Layout rules
`layout()` returns an `OrderedDict` where each key is a field name and each value is a dict with the rules:
- `w`: width (fixed or weight).
- `w_type`: `F` for fixed, anything else for proportional.
- `caption`: header text.
- `align`: `L`, `C`, `R`.
- `datatype`: `int`, `float` or `datetime` to format values.
- `group`: if `True`, the column becomes a group header.
- `sum`: list of fields to sum per group.
- `totalize`: include in final totals row.
- `new_page`: force page break at this group level.
- `cab_visivel`: show/hide group header.

Example:
```python
from collections import OrderedDict

return OrderedDict({
    "category": {"w": 0, "w_type": "S", "caption": "Category", "group": True, "sum": ["amount"]},
    "name": {"w": 0, "w_type": "S", "caption": "Name"},
    "amount": {"w": 20, "w_type": "F", "caption": "Amount", "align": "R", "totalize": True},
})
```

## Grouping and totals
- If a field is marked with `group=True`, the report nests rows by that field value and prints group headers.
- `sum` fields are calculated per group and printed in the group header line.
- `totalize=True` adds a final totals line.

## Excel/CSV export
Excel and CSV export rely on pandas. The output for CSV uses `;` as separator and `,` as decimal.

## Images
You can embed images in custom headers using `FPDF.image`. Use `Report.get_image_size()` to compute image dimensions if needed.
