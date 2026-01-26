# Reference

## Report
Base class for building reports. Subclass and implement:
- `layout()` -> `OrderedDict` with layout rules
- `data()` -> list of dicts (each dict is a row)

### Hooks
- `orientation()` -> default page orientation (`P` or `L`).
- `pre_cabecalho(pos_y)` -> write custom header before column header.
- `pos_tudo()` -> called after all rows are rendered.
- `titles()` -> optional helper for custom title output.
- `total_title()` -> text for totals row.

### Helpers
- `p(caption, txt, ...)` -> prints a label and value in the same line.
- `box()` -> context manager for `GridBox` (layouted card/box sections).

## GridBox
Utility to render a block of labeled fields.

Example:
```python
with self.box() as g:
    g.box("ID", "123", w=15)
    g.box("Name", "Example", w=0)
    g.new_line()
    g.box("Notes", "...", text_align="J")
```

## Constants
- `REPORT_PDF`
- `REPORT_EXCEL`
- `REPORT_CSV`

## Errors
- `ReportEmptyError` -> raised when `data()` returns no rows.
