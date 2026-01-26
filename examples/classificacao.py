from collections import OrderedDict

from almox.models.tipomaterial import TipoMaterialModel
from almox.models_db.classificacao import (
    query_classificacao_gerencial_report, query_classificacao_report)
from almox.schemas.classificacao import ClassificacaoSchema
from almox.schemas.material import MaterialSchema
from db import query2jsn, formatquery, get_dict_from_query_schema
from .almox_report import AlmoxReport
from util import auto_formata_periodo


class ClassificacaoReport(AlmoxReport):
    def layout(self):
        return OrderedDict({
            'classificacao__classificacao': {'w': 24, 'w_type': 'F', 'caption': 'Classificação',  'align': 'C'},
            'classificacao__descricao': {'w': 0, 'w_type': 'S', 'caption': 'Descrição'},
            'estoque_atual': {'w': self.LARGURA_FLOAT + 10, 'w_type': 'F', 'align': 'R', 'caption': 'Estoque Atual (R$)', 'totalize': True},
        })

    def data(self):
        query = query_classificacao_report(self.params)
        return query, {"classificacao": ClassificacaoSchema()}

class ClassificacaoGerencialReport(AlmoxReport):
    def layout(self):
        return OrderedDict({
            'classificacao__classificacao': {'w': 21, 'w_type': 'F', 'caption': 'Classificação',  'align': 'C'},
            'classificacao__descricao': {'w': 0, 'w_type': 'S', 'caption': 'Descrição'},
            'saldo_anterior': {'w': self.LARGURA_FLOAT + 10, 'w_type': 'F', 'align': 'R', 'caption': 'Saldo Anterior', 'totalize': True},
            'entradas': {'w': self.LARGURA_FLOAT + 10, 'w_type': 'F', 'align': 'R', 'caption': 'Entradas', 'totalize': True},
            'total': {'w': self.LARGURA_FLOAT + 10, 'w_type': 'F', 'align': 'R', 'caption': 'Total', 'totalize': True},
            'saidas': {'w': self.LARGURA_FLOAT + 10, 'w_type': 'F', 'align': 'R', 'caption': 'Saidas', 'totalize': True},
            'saldo': {'w': self.LARGURA_FLOAT + 10, 'w_type': 'F', 'align': 'R', 'caption': 'Saldo', 'totalize': True},
        })
 
    def data(self):
        query = query_classificacao_gerencial_report(self.params)
        return query, {"classificacao": ClassificacaoSchema()}

    def titles(self):
        tm = self.params.check_params_id_fk(TipoMaterialModel, 'id_tipomaterial', 'Tipo de material inválido')
        referencia = self.params.periodo_formatado()
        self.title = f'RELATÓRIO GERENCIAL DE CLASSIFICAÇÃO - {tm.descricao.upper()}'
        return [self.title, f'{referencia}']