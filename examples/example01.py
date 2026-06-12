from __future__ import annotations

from collections import OrderedDict

from tabularium import REPORT_PDF, Report


class ProductReport(Report):
    def layout(self):
        layout = OrderedDict(
            {
                "name": {"w": 0, "w_type": "S", "caption": "Product"},
                "price": {
                    "w": 30,
                    "w_type": "F",
                    "caption": "Price",
                    "align": "R",
                    "datatype": float,
                    "totalize": True,
                },
            }
        )
        return layout, {}

    def data(self):
        return self.params["rows"]

    def header(self):
        self.set_font(self.font_base_name, "B", 14)
        self.cell(0, 8, "Produtos", ln=1, align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font(self.font_base_name, "", 9)
        self.cell(0, 6, f"Pagina {self.page_no()}", align="R")


def main():
    rows = [
        {"name": "Notebook", "price": 2499.90},
        {"name": "Mouse", "price": 79.90},
        {"name": "Teclado", "price": 159.50},
        {"name": "Monitor", "price": 1099.00},
        {"name": "Headset", "price": 299.90},
        {"name": "Webcam", "price": 189.00},
        {"name": "Hub USB", "price": 89.90},
        {"name": "SSD 1TB", "price": 459.99},
        {"name": "Cadeira", "price": 899.00},
        {"name": "Mesa", "price": 699.00},
    ]

    params = {"format": REPORT_PDF, "orientation": "L", "rows": rows}
    report = ProductReport(params)
    filename, _mimetype, buffer = report.generate()

    with open(filename, "wb") as f:
        f.write(buffer.getvalue())


if __name__ == "__main__":
    main()
