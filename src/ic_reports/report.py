from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
from io import BytesIO
import os
import struct
from typing import Any

from fpdf import FPDF

from .constants import REPORT_CSV, REPORT_EXCEL, REPORT_PDF
from .errors import ReportEmptyError, ReportError
from .gridbox import GridBox
from .utils import convert, get_value_raw as util_get_value_raw


class Report(FPDF):
    def __init__(self, params: dict) -> None:
        super().__init__(unit="mm", format="A4")
        self.FPDF_CACHE_MODE = 1
        self.add_fonts()
        self.params = params
        self.largura_grupo = 2.5
        self.raiz: OrderedDict[str, Any] = OrderedDict()
        self.imagens: dict[str, bytes] = {}
        self._temp_images_files: dict[str, Any] = {}
        self._data_raw: list[dict] | None = None
        self.acrescimento_fonte_grande = 1
        self.altura_linha = 4.5
        self.altura_linha_box = 10
        self.border_cabecalho = "B"
        self.border_cab_grupo = "B"
        self.border_rodape = "TB"
        self.border_linha = "RLBT"
        self.linhas_preparadas: list = []
        self.grupos: list[str] = []
        self.COR_LINHA = 240
        self.COR_ROD_GRUPO = 230
        self.COR_CAB_GRUPO = 220
        self.COR_BRANCA = 255
        self.COR_CAB = 210
        self.LARGURA_FLOAT = 22
        self.LARGURA_DATE = 18
        self.font_base_name = "calibri"
        self.font_base_size = 10
        self.alias_nb_pages()

        self.set_fill_color(self.COR_BRANCA, self.COR_BRANCA, self.COR_BRANCA)
        self.objeto_atual = None
        self.data_singleton()

        try:
            self.layout_base, self.functions = self.layout()
        except ValueError:
            self.layout_base = self.layout()
            self.functions = {}

    def generate(self):
        format_ = self.params.get("format", REPORT_PDF)
        if format_ == REPORT_PDF:
            download_name = "report.pdf"
            mimetype = "application/pdf"
        elif format_ == REPORT_EXCEL:
            download_name = "report.xlsx"
            mimetype = "application/Excel"
        else:
            download_name = "report.csv"
            mimetype = "application/csv"

        self.add_page(orientation=self.orientation())
        self.raiz = self.carga()
        self.calc_largura()
        self.transformar(self.raiz, 0, "")

        if format_ == REPORT_PDF:
            self.imprimir_tudo()
            data_bytes = self.to_bytes()
            self.delete_temp_files()
        else:
            data_bytes = self.generate_excel_csv(self.raiz, format_)

        return download_name, mimetype, data_bytes

    def pre_cabecalho(self, pos_y):
        return pos_y

    def pos_tudo(self):
        return self.y

    def layout(self) -> OrderedDict:
        raise NotImplementedError

    def data(self) -> list[dict]:
        raise NotImplementedError

    def orientation(self):
        return self.params.get("orientation", "L")

    def _normalize_data(self, data):
        if isinstance(data, tuple) and data:
            return data[0]
        return data

    def data_singleton(self):
        if self._data_raw is None:
            data = self._normalize_data(self.data())
            self._data_raw = list(data) if data is not None else []
        if not self._data_raw:
            raise ReportEmptyError()
        self.objeto_atual = self._data_raw[0]
        return self._data_raw

    def add_fonts(self):
        def root_dir():
            return os.path.abspath(os.path.dirname(__file__))

        fonts_folder = "fonts"
        fonts_list = [("", "calibri.ttf"), ("B", "calibrib.ttf"), ("I", "calibrii.ttf")]
        for style, file_name in fonts_list:
            self.add_font(
                "calibri",
                style,
                os.path.join(root_dir(), fonts_folder, file_name),
                uni=True,
            )

    def to_bytes(self):
        return BytesIO(bytes(self.output(dest="S"), encoding="latin1"))

    def pdf_to_file(self, filename="report.pdf"):
        self.output(filename, "F")

    def delete_temp_files(self):
        for _, file in self._temp_images_files.items():
            file.close()
            os.unlink(file.name)
        self._temp_images_files.clear()
        self.imagens.clear()

    def get_image_size(self, buffer):
        width, height = struct.unpack(">LL", buffer[16:24])
        return int(width), int(height)

    def set_font_cabecalho(self):
        self.set_font(self.font_base_name, "B", 10)

    def set_font_cab_grupo(self):
        self.set_font(self.font_base_name, "B", 10)

    def set_font_rodape(self, style=""):
        self.set_font(self.font_base_name, style, 10)

    def set_font_linha(self):
        self.set_font(self.font_base_name, "", 11)

    def carga(self):
        self.grupos = [key for key, value in self.layout_base.items() if value.get("group", False)]
        raiz: OrderedDict[str, Any] = OrderedDict()
        for index, objeto in enumerate(self.data_singleton()):
            d = raiz
            for campo in self.grupos:
                grupo_key = self.get_value(campo, objeto)
                if grupo_key not in d.keys():
                    d[grupo_key] = OrderedDict()
                d = d[grupo_key]
            d[index] = objeto
        self.y_apos_cabecalho = self.y
        return raiz

    def soma_h_cab_1a_linha(self, i):
        h = 0
        while i < len(self.linhas_preparadas):
            tipo, linha, _ = self.linhas_preparadas[i]
            if tipo == "G":
                h += self.altura_linhas([linha])
            if tipo == "L":
                h += self.altura_linhas([linha])
                break
            i += 1
        return h

    def altura_linhas(self, linhas):
        h = 0
        for linha in linhas:
            h += max([c["h"] for c in linha])
        return h

    def somar(self, objeto, grupo_soma):
        for key, fields in grupo_soma.items():
            for field in fields:
                value = self.get_value(field, objeto)
                if not value:
                    value = "0"
                value = float(str(value).replace(".", "").replace(",", "."))
                grupo_soma[key][field] = grupo_soma[key][field] + value
        return grupo_soma

    def count_grupos(self):
        return len([campo for campo, regra in self.layout_base.items() if regra.get("group", False)])

    def count_grupos_invisiveis(self):
        return len(
            [
                campo
                for campo, regra in self.layout_base.items()
                if regra.get("group", False) and not regra.get("cab_visivel", True)
            ]
        )

    def is_group(self, value):
        return value.get("group", False)

    def x_from_field(self, field):
        x = self.l_margin
        for key2, value2 in self.layout_base.items():
            if key2 == field:
                break
            if not self.is_group(value2):
                x += value2["w_calc"]
        return x

    def somante_grupo_nivel(self, nivel):
        campos_soma = []
        i = 0
        for _, value in self.layout_base.items():
            if self.is_group(value):
                campos_soma = value.get("sum", [])
                if i == nivel:
                    break
                i += 1
        return campos_soma

    def grupo_e_visivel(self, nivel):
        i = 0
        cab_visivel = True
        for _, value in self.layout_base.items():
            if value.get("group", False):
                cab_visivel = value.get("cab_visivel", True)
                if i == nivel:
                    break
                i += 1
        return cab_visivel

    def transformar(self, raiz, nivel, chave):
        for key, value in raiz.items():
            if not isinstance(key, int):
                nchave = (chave + "|" if chave else "") + str(key)
                self.linhas_preparadas.append(
                    ("G", self.preparar_linha_cab_grupo(nivel, nchave, key), nivel)
                )
                self.transformar(value, nivel + 1, nchave)
            else:
                self.linhas_preparadas.append(("L", self.preparar_linha(value, nivel), value))

    def new_page_at_nivel(self, nivel):
        grupos = [(campo, regra) for campo, regra in self.layout_base.items() if self.is_group(regra)]
        i = 0
        for _, regra in grupos:
            if regra.get("new_page", False) and i == nivel:
                return True
            i += 1
        return False

    def preparar_linha_cab_grupo(self, nivel, nchave, key):
        grupo_sum = self.somante_grupo_nivel(nivel)
        acres = self.largura_grupo * (nivel - self.count_grupos_invisiveis())
        larg = self.w - self.l_margin - self.r_margin - acres
        self.set_font_cab_grupo()
        txt = str(key)
        split = self.multi_cell(
            w=larg,
            h=self.altura_linha,
            txt=txt,
            border=self.border_cab_grupo,
            align="L",
            split_only=True,
        )
        return [
            dict(
                nivel=nivel,
                key=nchave,
                sum=grupo_sum,
                w=larg,
                x=self.l_margin + acres,
                h=self.altura_linha * len(split) * self.acrescimento_fonte_grande,
                txt=txt,
                border=self.border_rodape,
            )
        ]

    def get_value_raw(self, campo, objeto):
        return util_get_value_raw(campo, objeto)

    def get_value(self, campo, objeto):
        regra = self.layout_base.get(campo, "")
        if not regra:
            return convert(self.get_value_raw(campo, objeto))
        datatype = regra.get("datatype", None)
        valor_campo = self.get_value_raw(campo, objeto)
        valor = convert(valor_campo, datatype=datatype)
        return valor if valor and valor != "None" else ""

    def preparar_linha(self, values, nivel):
        max_split = 1
        pos_x = self.l_margin + self.largura_grupo * (nivel - self.count_grupos_invisiveis())
        linha = []
        self.set_font_linha()
        for campo, regra in self.layout_base.items():
            if regra.get("group", False):
                continue
            align = regra.get("align", None)
            valor = self.get_value(campo, values)
            valor_campo = self.get_value_raw(campo, values)
            if not align:
                align = "R" if isinstance(valor_campo, float) else "L"
            align = "L" if not align else align
            larg = regra.get("w_calc", regra.get("w"))
            split = self.multi_cell(
                w=larg,
                h=self.altura_linha,
                txt=valor,
                border=self.border_linha,
                align=align,
                split_only=True,
            )
            if len(split) > max_split:
                max_split = len(split)
            coluna = {
                "x": pos_x,
                "w": larg,
                "txt": valor,
                "border": self.border_linha,
                "align": align,
                "len_split": len(split),
            }
            linha.append(coluna)
            pos_x += larg
        linha_preparada = []
        for coluna in linha:
            h = self.altura_linha * (max_split / coluna["len_split"])
            linha_preparada.append(
                dict(
                    nivel=nivel,
                    x=coluna["x"],
                    w=coluna["w"],
                    h=h,
                    txt=coluna["txt"],
                    border=coluna["border"],
                    align=coluna["align"],
                )
            )
        return linha_preparada

    def calc_largura(self):
        grupos_count = self.count_grupos() - self.count_grupos_invisiveis()
        nao_grupos = {campo: regra for campo, regra in self.layout_base.items() if not regra.get("group", False)}
        largura_fixa = {campo: regra for campo, regra in nao_grupos.items() if regra["w_type"] == "F"}
        largura_calculada = {
            campo: regra for campo, regra in nao_grupos.items() if regra["w_type"] != "F"
        }

        espaco_util = self.w - self.l_margin - self.r_margin - grupos_count * self.largura_grupo

        for campo, regra in largura_fixa.items():
            self.layout_base[campo]["w_calc"] = regra["w"]
        largura_total_fixa = sum([regra["w"] for _, regra in largura_fixa.items()])
        espaco_util -= largura_total_fixa

        q0 = 0
        ac = 0
        for campo, regra in largura_calculada.items():
            w = regra["w"]
            if w != 0:
                w_calc = espaco_util * w
                ac += w_calc
                self.layout_base[campo]["w_calc"] = w_calc
            else:
                q0 += 1
        espaco_util -= ac
        for campo, regra in largura_calculada.items():
            w = regra["w"]
            if w == 0:
                w_calc = espaco_util / q0
                self.layout_base[campo]["w_calc"] = w_calc

    def get_cab_completo(self, i):
        nivel = self.linhas_preparadas[i][1][0]["nivel"] - 1
        index = i - 1
        lista = []
        while index >= 0:
            tipo, linha, _ = self.linhas_preparadas[index]
            if tipo == "G" and linha[0]["nivel"] == nivel:
                lista.insert(0, linha)
                break
            index -= 1
        return lista

    def calcular(self, field, nchave=""):
        groups = [k for k, d in self.layout_base.items() if d.get("group", False)]
        chaves = nchave.split("|") if nchave else []
        soma = 0
        for r in self.data_singleton():
            eprasomar = True
            if chaves:
                for valor, field_name in zip(chaves, groups):
                    eprasomar = eprasomar and r[field_name] == valor
            if eprasomar:
                soma += r.get(field) or 0
        return soma

    def quant_group(self):
        return len([key for key, value in self.layout_base.items() if self.is_group(value)])

    def imprimir_cab_grupo(self, pos_y, cab_grupo, grupo_soma):
        if not cab_grupo:
            return pos_y
        self.set_font_cab_grupo()
        cor = 255

        quant_g = self.quant_group() - self.count_grupos_invisiveis()
        for linha in cab_grupo:
            c = linha[0]
            acres = self.largura_grupo * quant_g
            txt = c["txt"]
            if not self.grupo_e_visivel(c["nivel"]):
                continue
            self.set_fill_color(cor, cor, cor)
            self.x = c["x"]
            self.y = pos_y
            menor = c["w"]

            self.multi_cell(w=menor, h=c["h"], txt=txt, border="", align="L")
            for key, _ in grupo_soma[c["key"]].items():
                x = self.x_from_field(key)
                if x < menor:
                    menor = x

            for key, _ in grupo_soma[c["key"]].items():
                value = self.calcular(key, c["key"])
                col = self.layout_base[key]
                self.x = self.x_from_field(key)
                self.y = pos_y
                self.multi_cell(
                    w=acres + col["w_calc"],
                    h=c["h"],
                    txt=convert(value, datatype=col.get("datatype", None)),
                    border="",
                    align="R",
                )
            pos_y += c["h"]
        return pos_y

    def imprimir_cabecalho(self, pos_y):
        pos_y = self.pre_cabecalho(pos_y)
        self.set_font_cabecalho()
        linha = []
        max_split = 1
        cor = self.COR_CAB
        q = self.quant_group() - self.count_grupos_invisiveis()
        acres = (q) * self.largura_grupo
        pos_x = self.l_margin + acres
        for campo, regra in self.layout_base.items():
            if regra.get("group", False):
                continue
            txt = regra.get("caption", campo)
            align = regra.get("align", None)
            align = "L" if not align else align
            larg = regra.get("w_calc", regra.get("w"))
            split = self.multi_cell(
                w=larg,
                h=self.altura_linha,
                txt=txt,
                border=self.border_cabecalho,
                align=align,
                split_only=True,
            )
            if len(split) > max_split:
                max_split = len(split)
            coluna = dict(x=pos_x, w=larg, txt=txt, border=self.border_cabecalho, align=align, len_split=len(split))
            linha.append(coluna)
            pos_x += larg

        self.set_fill_color(cor, cor, cor)
        for c in linha:
            self.x = c["x"]
            self.y = pos_y
            self.multi_cell(
                w=c["w"],
                h=self.altura_linha * (max_split / c["len_split"]),
                txt=c["txt"],
                align=c["align"],
                fill=True,
            )
            if acres:
                self.y = pos_y
                self.x = self.l_margin
                self.multi_cell(acres, h=self.altura_linha * (max_split / c["len_split"]), border="", fill=True)
        pos_y += max_split * self.altura_linha
        return pos_y

    def p(self, caption="", txt="", **kwargs):
        caption = f"{caption} "
        ln = kwargs.get("ln", 0)
        h = kwargs.get("h", 0)
        w = kwargs.get("w", 0)

        kwargs["ln"] = 0
        font_size = self.font_base_size
        self.set_font(self.font_base_name, "", font_size)
        tam_txt = self.get_string_width(txt) + self.get_string_width("M")
        self.set_font(self.font_base_name, "B", font_size)
        tam_caption = self.get_string_width(caption)

        self.set_font(self.font_base_name, "B", self.font_base_size)
        kwargs["h"] = self.altura_linha if not h else h
        kwargs["txt"] = caption
        kwargs["w"] = tam_caption
        if w < 0:
            self.x = self.w - self.r_margin + w

        self.cell(**kwargs)

        self.set_font(self.font_base_name, "", self.font_base_size)
        kwargs["h"] = h or self.altura_linha
        kwargs["txt"] = txt
        if w < 0:
            self.x = self.w - self.r_margin + w + tam_caption
            w = -w - tam_caption
        kwargs["w"] = w if w > 0 else tam_txt
        self.cell(**kwargs)

        self.y += self.altura_linha - 0.5 if ln else 0
        self.x = self.l_margin if ln else self.x
        return kwargs

    def total_title(self):
        return "Total"

    def totalize(self):
        if not any([campo for campo, regra in self.layout_base.items() if regra.get("totalize", False)]):
            return self.y

        pos_y = self.y
        self.set_font_cabecalho()
        linha = []
        max_split = 1
        cor = self.COR_CAB
        q = self.quant_group() - self.count_grupos_invisiveis()
        acres = (q) * self.largura_grupo
        pos_x = self.l_margin + acres
        total_label = {
            "w": self.w - self.l_margin - self.r_margin,
            "x": self.l_margin,
            "txt": self.total_title(),
            "len_split": 1,
            "align": "L",
        }
        linha.append(total_label)
        for campo, regra in self.layout_base.items():
            if regra.get("group", False):
                continue
            larg = regra.get("w_calc", regra.get("w"))
            if regra.get("totalize", False):
                align = regra.get("align", "L")
                txt = convert(self.calcular(campo), datatype=regra.get("datatype"))

                split = self.multi_cell(
                    w=larg,
                    h=self.altura_linha,
                    txt=txt,
                    border=self.border_cabecalho,
                    align=align,
                    split_only=True,
                )
                if len(split) > max_split:
                    max_split = len(split)
                coluna = dict(x=pos_x, w=larg, txt=txt, border=self.border_cabecalho, align="R", len_split=len(split))
                linha.append(coluna)
            pos_x += larg

        self.set_fill_color(cor, cor, cor)
        for c in linha:
            self.x = c["x"]
            self.y = pos_y
            self.multi_cell(
                w=c["w"],
                h=self.altura_linha * (max_split / c["len_split"]),
                txt=c["txt"],
                align=c["align"],
                fill=True,
            )
        pos_y += max_split * self.altura_linha
        return pos_y

    def imprimir_tudo(self):
        pos_y = self.y
        pos_y = self.imprimir_cabecalho(pos_y)

        i = 0
        grupo_soma = OrderedDict()
        new_page = False
        force_new_page = False
        linha_contador = 0
        linha_cab = None
        while i < len(self.linhas_preparadas):
            tipo, linha, objeto = self.linhas_preparadas[i]
            if not linha:
                break
            primeiro_campo = linha[0]
            h_linha = self.altura_linhas([linha])
            acrescimento = 0
            if tipo == "G":
                key = primeiro_campo["key"]
                grupo_soma[key] = OrderedDict()
                for key_campo_soma in primeiro_campo.get("sum", []):
                    grupo_soma[key][key_campo_soma] = 0
                acrescimento = self.soma_h_cab_1a_linha(i)

            if pos_y >= self.h - self.b_margin - h_linha - acrescimento or (
                force_new_page and i < len(self.linhas_preparadas) - 1
            ):
                j = i + 1
                while j < len(self.linhas_preparadas):
                    _tipo, _, _objeto = self.linhas_preparadas[j]
                    if _tipo == "L":
                        self.objeto_atual = _objeto
                        break
                    j += 1
                new_page = True
                self.add_page(orientation=self.orientation())
                pos_y = self.y
                pos_y = self.imprimir_cabecalho(pos_y)
                linha_contador = 0
                if force_new_page and linha_cab and i > 1:
                    pos_y = self.imprimir_cab_grupo(pos_y, linha_cab, grupo_soma)
                force_new_page = False

            if tipo == "L":
                if new_page:
                    pos_y = self.imprimir_cab_grupo(pos_y, self.get_cab_completo(i), grupo_soma)
                    new_page = False
                grupo_soma = self.somar(objeto, grupo_soma)
                cor = self.COR_BRANCA if linha_contador % 2 == 0 else self.COR_LINHA
                linha_contador += 1
                self.set_fill_color(cor, cor, cor)
                for c in linha:
                    self.x = c["x"]
                    self.y = pos_y
                    self.set_font_linha()
                    value = c["txt"]
                    self.multi_cell(
                        w=c["w"],
                        h=c["h"],
                        txt=value,
                        align=c.get("align", "L"),
                        fill=cor != self.COR_BRANCA,
                    )
                pos_y += h_linha
            if tipo == "G":
                if not new_page:
                    if self.new_page_at_nivel(primeiro_campo["nivel"] - 1):
                        force_new_page = True
                        linha_cab = [linha]
                    else:
                        linha_contador = 0
                        pos_y = self.imprimir_cab_grupo(pos_y, [linha], grupo_soma)

            i += 1
            if objeto:
                self.objeto_atual = objeto
        self.auto_page_break = True
        self.totalize()
        self.pos_tudo()

    def generate_excel_csv(self, raiz, format_):
        output = BytesIO()
        result = []
        largura = {}
        for _, objeto in raiz.items():
            field = {}
            for campo, regra in self.layout_base.items():
                valor = self.get_value(campo, objeto)
                valor_campo = self.get_value_raw(campo, objeto)
                if isinstance(valor_campo, float):
                    valor = float(str(valor).replace(".", "").replace(",", "."))
                elif isinstance(valor_campo, int):
                    valor = int(valor)
                key = campo if format_ == REPORT_CSV else regra.get("caption", campo)
                field[key] = valor
                largura[key] = regra.get("w_calc", regra.get("w", 0))
            result.append(field)

        try:
            import pandas as pd
        except Exception as exc:
            raise ReportError("pandas is required for Excel/CSV export") from exc

        df = pd.DataFrame(result)
        if format_ == REPORT_EXCEL:
            writer = pd.ExcelWriter(output)
            cols = iter("A B C D E F G H I J K L M N O P Q R S T U V W X Y".split())
            df.to_excel(writer, index=False, sheet_name="Report")
            for column in df:
                column_length = largura[column]
                sheet = writer.sheets["Report"]
                sheet.column_dimensions[next(cols)].width = column_length
            writer.close()
        if format_ == REPORT_CSV:
            df.to_csv(output, index=False, sep=";", decimal=",", encoding="cp1252")
        output.seek(0)
        return output

    @contextmanager
    def box(self):
        g = GridBox(self)
        yield g
        g.prepare()
