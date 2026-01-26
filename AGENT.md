# AGENT.md - ic-reports (PDF/Excel/CSV)

## Visao geral
O pacote `ic-reports` em `src/ic_reports` fornece uma classe base `Report` para gerar tabelas em PDF (FPDF) e exportar para Excel/CSV (pandas). O fluxo padrao e: criar uma subclasse, implementar `layout()` e `data()`, e chamar `generate()`.

## Arquivos principais
- `src/ic_reports/report.py`: classe base `Report` (renderizacao, layout, agrupamento, PDF/Excel/CSV).
- `src/ic_reports/gridbox.py`: utilitario `GridBox` para quadros/cartoes.
- `src/ic_reports/utils.py`: helpers de formatacao e leitura de campos.
- `src/ic_reports/constants.py`: `REPORT_PDF`, `REPORT_EXCEL`, `REPORT_CSV`.
- `src/ic_reports/errors.py`: `ReportError`, `ReportEmptyError`.
- `src/ic_reports/fonts/*`: fontes Calibri embarcadas no PDF.

## Fluxo basico de uso
1) Defina `params` como dict simples (ex: format, orientation).
2) Instancie a classe do relatorio.
3) Chame `generate()` para obter `(download_name, mimetype, buffer)`.

Exemplo:
```python
from collections import OrderedDict
from ic_reports import Report, REPORT_PDF

class SimpleReport(Report):
    def layout(self):
        return OrderedDict({
            "name": {"w": 0, "w_type": "S", "caption": "Name"},
            "qty": {"w": 20, "w_type": "F", "caption": "Qty", "align": "R", "datatype": int},
        })

    def data(self):
        return [{"name": "Item A", "qty": 2}]

params = {"format": REPORT_PDF, "orientation": "L"}
report = SimpleReport(params)
filename, mimetype, buffer = report.generate()
```

## Params esperados
`params` e um dict simples. Chaves comuns:
- `format`: `pdf`, `excel`, `csv` (ver constants).
- `orientation`: `P` ou `L`.
- qualquer dado extra usado pelo relatorio.

## Layout do relatorio
`layout()` retorna um `OrderedDict` com regras por coluna:
```python
OrderedDict({
    "campo": {
        "w": 20,          # largura ou peso
        "w_type": "F",    # F = fixa; outros = proporcional
        "caption": "Titulo",
        "align": "L",     # L/C/R
        "datatype": int,  # formatacao
        "group": False,
        "sum": ["campo"],
        "totalize": True,
        "new_page": False,
        "cab_visivel": True,
    }
})
```

Regras importantes:
- `w_type`:
  - `F`: largura fixa (mm).
  - outros valores: largura proporcional pelo peso `w`.
  - `w = 0` divide o espaco restante igualmente.
- `group=True`: o campo vira agrupador (gera cabecalho de grupo).
- `sum=["campo"]`: soma valores por grupo (cabecalho de grupo).
- `totalize=True`: soma no total final (`totalize()`).
- `new_page=True`: forca nova pagina quando o grupo muda naquele nivel.
- `cab_visivel=False`: esconde cabecalho de grupo (continua agrupando).
- `datatype`: influencia formatacao (`int`, `float`, `date`/`datetime`).

## Hooks e pontos de extensao
- `layout()` **obrigatorio**.
- `data()` **obrigatorio**: retorna `list[dict]`. Se retornar tupla, apenas o primeiro item e usado.
- `orientation()` opcional: default via `params` (padrao `L`).
- `pre_cabecalho(pos_y)` opcional: imprime bloco antes do cabecalho de colunas.
- `pos_tudo()` opcional: imprime rodape customizado apos as linhas.
- `total_title()` opcional: titulo do bloco de totalizacao.

Helpers:
- `p(caption, txt, ...)`: imprime rotulo + valor na mesma linha.
- `box()` (context manager): cria quadros via `GridBox`.

## Exportacao (PDF/Excel/CSV)
- PDF: FPDF + fontes Calibri (`src/ic_reports/fonts`).
- Excel: `pandas.ExcelWriter`, largura de coluna baseada em `w_calc`.
- CSV: separador `;`, decimal `,`, encoding `cp1252`.

`Report.generate()`:
- Monta layout, calcula larguras e renderiza.
- Retorna `BytesIO` pronto para download (PDF/Excel/CSV).

## Imagens
- `Report.get_image_size()` calcula dimensoes de PNG por bytes.
- `utils.get_image_size()` tambem esta disponivel.

## Erros
- `ReportEmptyError`: lancado quando `data()` nao retorna linhas.
- `ReportError`: erro generico (ex: pandas ausente).

## Exemplos
Os exemplos em `examples/` sao adaptados da aplicacao original e podem depender de modelos/queries externos.

## Build/empacotamento
- Configuracao em `pyproject.toml`.
- Fontes TTF sao incluidas no wheel/sdist.
