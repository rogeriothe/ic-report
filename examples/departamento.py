from collections import OrderedDict

from sqlalchemy import text

from almox.models.departamento import DepartamentoModel
from almox.models_db.departamento import query_departamentos_report
from almox.schemas.departamento import DepartamentoSchema
from db import get_dict_from_query_schema, query2jsn, formatquery
from .almox_report import AlmoxReport


class DepartamentoReport(AlmoxReport):
    def orientation(self):
        return 'L'

    def layout(self):
        return OrderedDict({
            'centrocusto': {'w': 0, 'w_type': 'S', 'caption': 'Centro de Custo', 'group': True, 'sum': ['total']},
            'departamento__id': {'w': 12, 'w_type': 'F', 'caption': 'ID',  'align': 'R'},
            'departamento__descricao': {'w': 0, 'w_type': 'S', 'caption': 'Descrição'},
            'departamento__responsavel': {'w': 60, 'w_type': 'F', 'caption': 'Responsável'},
            'total': {'w': self.LARGURA_FLOAT + 10, 'w_type': 'F', 'align': 'R', 'caption': 'Total (R$)', 'totalize': True},
        })

    def data(self):
        query = query_departamentos_report(self.params)
        return query, {'departamento': DepartamentoSchema()}
        return query2jsn(self.params, query, aplicar_limites=False, alias_schema= {'departamento': DepartamentoSchema()})

    