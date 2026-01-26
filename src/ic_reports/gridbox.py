from __future__ import annotations

from collections import OrderedDict


class Box:
    def __init__(self, box_id, line_number, caption="", text="", **kwargs) -> None:
        self.id = box_id
        self.line_number = line_number
        self.caption = caption or ""
        self.text = text or ""
        self.nocaption = kwargs.get("nocaption", False)
        self.notext = kwargs.get("notext", False)
        self.w = kwargs.get("w", 0)
        self.fh = kwargs.get("fh", None)
        self.border = kwargs.get("border", None)
        self.caption_align = kwargs.get("caption_align", "L")
        self.text_align = kwargs.get("text_align", "L")
        self.rgb = kwargs.get("rgb", "")
        self.first_col = False
        self.last_col = False
        self.first_line = False
        self.last_line = False
        self.splitc = 0
        self.splitt = 0
        self.hc = 0
        self.ht = 0

    def border_calc(self):
        if self.border is not None:
            return self.border
        result = "TL"
        if self.last_col:
            result += "R"
        if self.last_line:
            result += "B"
        return result


class GridBox:
    def __init__(self, report) -> None:
        self.report = report
        self.lines = OrderedDict()
        self.line_number = 0
        self.box_number = 0

    def new_line(self):
        self.line_number += 1

    def box(self, caption="", text="", **kwargs):
        font_size = self.report.font_base_size
        self.report.set_font(self.report.font_base_name, "", font_size)
        self.report.set_font(self.report.font_base_name, "B", font_size)

        box = Box(self.box_number, self.line_number, caption, text, **kwargs)
        self.box_number += 1

        columns = self.lines.get(self.line_number, {})
        columns[len(columns.keys())] = box
        self.lines[self.line_number] = columns

    def set_font_caption(self):
        color = self.report.COR_CAB
        self.report.set_fill_color(color, color, color)
        self.report.set_font(self.report.font_base_name, "B", 9)

    def set_font_text(self):
        color = 255
        self.report.set_fill_color(color, color, color)
        self.report.set_font(self.report.font_base_name, "", 10)

    def calc_width_height(self, line):
        cols = {}
        width_fixed = {}
        width_calc = {}
        for col, box in line.items():
            if line[col].w > 0:
                width_fixed[col] = box
            if line[col].w == 0:
                width_calc[col] = box
            if line[col].w < 0:
                cols[col] = box

        usable = self.report.w - self.report.l_margin - self.report.r_margin
        total_fixed = sum([c.w for c in width_fixed.values()])
        space = usable - total_fixed
        used = 0
        for col, box in cols.items():
            box.w = space * (box.w * -1)
            used += box.w
            width_fixed[col] = box
        space -= used
        for col, box in width_calc.items():
            box.w = space / len(width_calc.keys())
            width_fixed[col] = box

        height_caption = 4.0
        height_text = 8.0
        max_splitc = 0
        max_splitt = 0
        for box in self.get_cols_list(width_fixed):
            self.set_font_caption()
            splitc = len(
                self.report.multi_cell(
                    w=box.w,
                    h=box.fh or height_caption,
                    txt=box.caption,
                    border=box.border,
                    align="L",
                    split_only=True,
                )
            )
            self.set_font_text()
            splitt = len(
                self.report.multi_cell(
                    w=box.w,
                    h=box.fh or height_text,
                    txt=box.text,
                    border=box.border,
                    align="L",
                    split_only=True,
                )
            )
            box.splitc = splitc
            box.splitt = splitt
            max_splitc = max([splitc, max_splitc]) * 1.0
            max_splitt = max([splitt, max_splitt]) * 1.0

        for _, box in width_fixed.items():
            box.hc = ((max_splitc - (max_splitc - 1) * 0.25) / box.splitc * 1.0) * (
                box.fh or height_caption
            )
            box.ht = ((max_splitt - (max_splitt - 1) * 0.50) / box.splitt * 1.0) * (
                box.fh or height_text
            )
        return width_fixed

    def calc_pos(self):
        for line_index, cols in self.lines.items():
            self.calc_width_height(cols)
            for col_index, box in cols.items():
                box.first_col = col_index == 0
                box.last_col = col_index == len(cols) - 1
                box.first_line = line_index == 0
                box.last_line = line_index == len(self.lines.items()) - 1

    def get_cols_list(self, cols):
        return [v for _, v in sorted(cols.items())]

    def prepare(self):
        self.calc_pos()
        for _, line in self.lines.items():
            self.draw(line)
        self.report.y += 4

    def draw(self, cols):
        self.report.x = self.report.l_margin
        y_pos = self.report.y
        x_pos = self.report.x
        for box in self.get_cols_list(cols):
            self.report.x = x_pos
            self.report.y = y_pos
            if not box.nocaption:
                self._draw_caption(box)
            self.report.x = x_pos
            if not box.notext:
                self._draw_text(box)
            x_pos += box.w

    def _draw_caption(self, box):
        self.set_font_caption()
        self.report.multi_cell(
            w=box.w,
            h=box.hc,
            txt=box.caption,
            border=box.border_calc(),
            fill=True,
            align=box.caption_align,
        )

    def _rgb(self, rgb):
        red = int(rgb[:2], 16)
        green = int(rgb[2:4], 16)
        blue = int(rgb[4:], 16)
        return red, green, blue

    def _draw_text(self, box):
        self.set_font_text()
        if box.rgb:
            self.report.set_fill_color(*self._rgb(box.rgb))
        self.report.multi_cell(
            w=box.w,
            h=box.ht,
            txt=box.text,
            border=box.border_calc(),
            align=box.text_align,
            fill=bool(box.rgb),
        )
