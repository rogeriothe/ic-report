from __future__ import annotations

from collections import OrderedDict

import pytest

from tabularium import REPORT_CSV, REPORT_EXCEL, REPORT_PDF, Report
from tabularium.errors import ReportEmptyError


class FlatReport(Report):
    def layout(self):
        return OrderedDict(
            {
                "name": {"w": 0, "w_type": "S", "caption": "Name"},
                "qty": {"w": 15, "w_type": "F", "caption": "Qty", "align": "R", "datatype": int},
                "amount": {
                    "w": 20,
                    "w_type": "F",
                    "caption": "Amount",
                    "align": "R",
                    "datatype": float,
                    "totalize": True,
                },
            }
        )

    def data(self):
        return [
            {"name": "Item A", "qty": 2, "amount": 12.5},
            {"name": "Item B", "qty": 1, "amount": 7.0},
        ]


class GroupedReport(FlatReport):
    def layout(self):
        layout = super().layout()
        layout.update(
            {
                "category": {
                    "w": 0,
                    "w_type": "S",
                    "caption": "Category",
                    "group": True,
                    "sum": ["amount"],
                }
            }
        )
        layout.move_to_end("category", last=False)
        return layout

    def data(self):
        return [
            {"category": "Hardware", "name": "Mouse", "qty": 2, "amount": 50.0},
            {"category": "Hardware", "name": "Keyboard", "qty": 1, "amount": 100.0},
            {"category": "Services", "name": "Setup", "qty": 1, "amount": 80.0},
        ]


def test_report_initializes_layout_and_caches_data() -> None:
    report = FlatReport({"format": REPORT_PDF})

    assert list(report.layout_base) == ["name", "qty", "amount"]
    assert report.data_singleton() is report.data_singleton()
    assert report.objeto_atual == {"name": "Item A", "qty": 2, "amount": 12.5}


def test_empty_data_raises_report_empty_error() -> None:
    class EmptyReport(FlatReport):
        def data(self):
            return []

    with pytest.raises(ReportEmptyError, match="No data available"):
        EmptyReport({})


def test_tuple_data_uses_first_item() -> None:
    class TupleDataReport(FlatReport):
        def data(self):
            return ([{"name": "Only", "qty": 1, "amount": 2.0}], {"ignored": True})

    report = TupleDataReport({})

    assert report.data_singleton() == [{"name": "Only", "qty": 1, "amount": 2.0}]


def test_calc_largura_assigns_fixed_and_remaining_widths() -> None:
    report = FlatReport({})

    report.calc_largura()

    usable_width = report.w - report.l_margin - report.r_margin
    assert report.layout_base["qty"]["w_calc"] == 15
    assert report.layout_base["amount"]["w_calc"] == 20
    assert report.layout_base["name"]["w_calc"] == pytest.approx(usable_width - 35)


def test_grouped_report_builds_nested_tree_and_prepared_lines() -> None:
    report = GroupedReport({})
    report.add_page(orientation=report.orientation())

    raiz = report.carga()
    report.calc_largura()
    report.transformar(raiz, 0, "")

    assert report.grupos == ["category"]
    assert list(raiz) == ["Hardware", "Services"]
    assert list(raiz["Hardware"]) == [0, 1]
    assert list(raiz["Services"]) == [2]
    assert [line_type for line_type, _, _ in report.linhas_preparadas] == ["G", "L", "L", "G", "L"]


def test_get_value_uses_layout_datatype_and_nested_lookup() -> None:
    report = FlatReport({})
    report.layout_base["customer__name"] = {"w": 0, "w_type": "S"}
    data = {"amount": 1234.5, "qty": "3", "customer": {"name": "Ada"}}

    assert report.get_value("amount", data) == "1.234,50"
    assert report.get_value("qty", data) == "3"
    assert report.get_value("customer__name", data) == "Ada"
    assert report.get_value("missing", data) == ""


def test_generate_csv_returns_download_metadata_and_cp1252_content() -> None:
    filename, mimetype, buffer = FlatReport({"format": REPORT_CSV}).generate()

    assert filename == "report.csv"
    assert mimetype == "application/csv"
    assert buffer.getvalue().decode("cp1252").splitlines() == [
        "name;qty;amount",
        "Item A;2;12,5",
        "Item B;1;7,0",
    ]


def test_generate_pdf_returns_pdf_buffer() -> None:
    filename, mimetype, buffer = FlatReport({"format": REPORT_PDF}).generate()

    assert filename == "report.pdf"
    assert mimetype == "application/pdf"
    assert buffer.getvalue().startswith(b"%PDF")


def test_generate_excel_returns_xlsx_buffer() -> None:
    filename, mimetype, buffer = FlatReport({"format": REPORT_EXCEL}).generate()

    assert filename == "report.xlsx"
    assert mimetype == "application/Excel"
    assert buffer.getvalue().startswith(b"PK")
