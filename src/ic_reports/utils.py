from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from struct import unpack
from typing import Any


def get_image_size(buffer: bytes) -> tuple[int, int]:
    width, height = unpack(">LL", buffer[16:24])
    return int(width), int(height)


def get_value_raw(field: str, data: Any, sep: str = "__") -> Any:
    current = data
    for key in field.split(sep):
        if current is None:
            return None
        if hasattr(current, key):
            current = getattr(current, key)
            continue
        if isinstance(current, dict):
            current = current.get(key)
            continue
        try:
            current = current[key]
            continue
        except Exception:
            return None
    return current


def convert(value: Any, datatype: type | None = None) -> str:
    if value is None:
        return ""
    if datatype in (int, float, Decimal):
        return _format_number(value, datatype)
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, (int, float, Decimal)):
        return _format_number(value, float)
    return str(value)


def _format_number(value: Any, datatype: type | None) -> str:
    if value is None:
        return "0"
    if datatype is int:
        try:
            return str(int(value))
        except Exception:
            return "0"
    try:
        number = float(value)
    except Exception:
        return str(value)
    formatted = format(number, ",.2f")
    return formatted.replace(",", "%").replace(".", ",").replace("%", ".")
