from __future__ import annotations

from collections import OrderedDict
from datetime import date
from pathlib import Path

from tabularium import REPORT_PDF, Report
from tabularium.utils import get_image_size


class AcmeServiceFichaReport(Report):
    def layout(self):
        layout = OrderedDict(
            {
                "service": {"w": 0, "w_type": "S", "caption": "Service"},
                "hours": {
                    "w": 18,
                    "w_type": "F",
                    "caption": "Hours",
                    "align": "R",
                    "datatype": float,
                    "totalize": True,
                },
                "rate": {
                    "w": 22,
                    "w_type": "F",
                    "caption": "Rate",
                    "align": "R",
                    "datatype": float,
                },
                "total": {
                    "w": 26,
                    "w_type": "F",
                    "caption": "Total",
                    "align": "R",
                    "datatype": float,
                    "totalize": True,
                },
            }
        )
        return layout

    def data(self):
        return self.params["rows"]

    def pre_cabecalho(self, pos_y):
        asset_path = Path(__file__).resolve().parent / "assets" / "acme_header.png"
        banner_bytes = asset_path.read_bytes()
        img_w, img_h = get_image_size(banner_bytes)
        usable_w = self.w - self.l_margin - self.r_margin
        banner_h = usable_w * (img_h / img_w)

        self.image(str(asset_path), x=self.l_margin, y=pos_y, w=usable_w, h=banner_h)
        self.y = pos_y + banner_h + 4

        ficha = self.params["ficha"]
        with self.box() as box:
            box.box("Client", ficha["client"], w=0)
            box.box("Report ID", ficha["report_id"], w=0)
            box.box("Date", ficha["date"], w=0)
            box.new_line()
            box.box("Contact", ficha["contact"], w=0)
            box.box("Location", ficha["location"], w=0)
            box.box("Status", ficha["status"], w=0)
            box.new_line()
            box.box("Scope", ficha["scope"], w=0)

        self.set_font(self.font_base_name, "B", 11)
        self.cell(0, 6, "Services", ln=1)
        return self.y


def main():
    rows = [
        {"service": "On-site inspection", "hours": 3.5, "rate": 120.0, "total": 420.0},
        {"service": "Equipment calibration", "hours": 2.0, "rate": 140.0, "total": 280.0},
        {"service": "Preventive maintenance", "hours": 4.0, "rate": 110.0, "total": 440.0},
        {"service": "Compliance documentation", "hours": 1.5, "rate": 95.0, "total": 142.5},
        {"service": "Final walkthrough", "hours": 1.0, "rate": 120.0, "total": 120.0},
    ]

    ficha = {
        "client": "ACME Corp",
        "report_id": "SR-2048",
        "date": date.today().strftime("%d/%m/%Y"),
        "contact": "Jordan Smith",
        "location": "Phoenix, AZ",
        "status": "Completed",
        "scope": "Quarterly service visit for plant maintenance and compliance checks.",
    }

    params = {
        "format": REPORT_PDF,
        "orientation": "P",
        "rows": rows,
        "ficha": ficha,
    }

    report = AcmeServiceFichaReport(params)
    filename, _mimetype, buffer = report.generate()

    with open(filename, "wb") as f:
        f.write(buffer.getvalue())


if __name__ == "__main__":
    main()
