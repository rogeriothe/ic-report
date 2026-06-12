from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
import struct

from tabularium.utils import convert, get_image_size, get_value_raw


def test_convert_formats_common_values() -> None:
    assert convert(None) == ""
    assert convert(date(2026, 6, 12)) == "12/06/2026"
    assert convert(datetime(2026, 6, 12, 10, 30)) == "12/06/2026"
    assert convert(1234.5) == "1.234,50"
    assert convert(Decimal("12.3"), Decimal) == "12,30"
    assert convert("7", int) == "7"
    assert convert("not-a-number", int) == "0"


def test_get_value_raw_reads_nested_dicts_and_objects() -> None:
    data = {
        "customer": SimpleNamespace(name="Ada", address={"city": "Fortaleza"}),
        "item": {"name": "Notebook"},
    }

    assert get_value_raw("customer__name", data) == "Ada"
    assert get_value_raw("customer__address__city", data) == "Fortaleza"
    assert get_value_raw("item__name", data) == "Notebook"
    assert get_value_raw("missing__field", data) is None
    assert get_value_raw("customer__missing", data) is None


def test_get_image_size_reads_png_dimensions_from_header_bytes() -> None:
    buffer = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + struct.pack(">LL", 320, 180)

    assert get_image_size(buffer) == (320, 180)
