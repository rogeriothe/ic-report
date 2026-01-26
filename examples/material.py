import logging
from collections import OrderedDict
from datetime import date, datetime
from functools import reduce
from pprint import pprint

from sqlalchemy import asc, desc, text
from sqlalchemy.sql import func

from almox.models.material import MaterialModel
from almox.models_db.material import (query_material_estocagem, query_material_ficha_report,
                                      query_material_report)
from almox.schemas.classificacao import ClassificacaoSchema
from almox.schemas.material import MaterialSchema
from almox.schemas.tipomaterial import TipoMaterialSchema
from db import query2jsn, formatquery
from .almox_report import AlmoxReport
from util import lambda_to_str, prrint


class MaterialReport(AlmoxReport):
    def layout(self):
        return OrderedDict({
            'material__id': {'w': 10, 'w_type': 'F', 'caption': 'Id',  'align': 'R'},
            'material__classificacao__classificacao':  {'w': 24, 'w_type': 'F', 'caption': 'Classificação',  'align': 'C', 'new_page': False, 'group': False, 'sum': ['custo_total']},
            'material__descricao_completa': {'w': 0, 'w_type': 'S', 'caption': 'Descrição do Material'},
            'material__tipomaterial__descricao':  {'w': 30, 'w_type': 'F', 'caption': 'Tipo de Material',  'align': 'C', 'new_page': False, 'group': False},
            'material__estoque_atual': {'w': self.LARGURA_FLOAT - 2, 'w_type': 'F', 'align': 'R', 'caption': 'Estoque', 'datatype': int},
            'material__custo_medio': {'w': self.LARGURA_FLOAT, 'w_type': 'F', 'align': 'R', 'caption': 'Custo Médio'},
            'material__custo_total': {'w': self.LARGURA_FLOAT + 3, 'w_type': 'F', 'align': 'R', 'caption': 'Estoque Total', 'totalize': False},
        })

    def data(self):
        query = query_material_report(self.params)
        return query, {"material": MaterialSchema()}
        # pprint(MaterialSchema().dumps(query.first()))
        jsn = query2jsn(self.params, query, aplicar_limites=False, alias_schema={"material": MaterialSchema()})
        # pprint(jsn[0])
        return jsn

    def titles(self):
        self.title = 'RELATÓRIO DE MATERIAL - Estoque Atual'
        if self.objeto_atual:
            return ['RELATÓRIO DE MATERIAL', 'Estoque Atual']
        return ['Relatorio vazio']

class MaterialFichaReport(AlmoxReport):
    multimaterial = False

    def total_title(self):
        return 'Total de materiais'

    def layout(self):
        LARGURA_INT = self.LARGURA_FLOAT - 8
        d =  OrderedDict({
            'material': {'w': 0, 'w_type': 'S', 'caption': 'Material'
                , 'cab_visivel': False
                , 'group': True
                , 'sum': ['entradas', 'entradas_valor', 'saidas', 'saidas_valor']},
            'descricao': {'w': 0, 'w_type': 'S', 'caption': 'Histórico'},
            'entradas': {'w': LARGURA_INT + 2, 'w_type': 'F', 'align': 'R', 'caption': 'Entradas', 'datatype': int, 'totalize': True},
            'entradas_valor': {'w': self.LARGURA_FLOAT, 'w_type': 'F', 'align': 'R', 'caption': 'Valor', 'totalize': True},
            'saidas': {'w': LARGURA_INT, 'w_type': 'F', 'align': 'R', 'caption': 'Saídas', 'datatype': int, 'totalize': True},
            'saidas_valor': {'w': self.LARGURA_FLOAT, 'w_type': 'F', 'align': 'R', 'caption': 'Valor', 'totalize': True},
            'saldo': {'w': self.LARGURA_FLOAT, 'w_type': 'F', 'align': 'R', 'caption': 'Saldo', 'datatype': int, 'totalize': True},
            'saldo_valor': {'w': self.LARGURA_FLOAT, 'w_type': 'F', 'align': 'R', 'caption': 'Valor'},
            'unitario': {'w': LARGURA_INT + 2, 'w_type': 'F', 'align': 'R', 'caption': 'Unitário'},
        })
        return d
        
    def data(self):
        query = query_material_ficha_report(self.params)
        return query, {"material", MaterialSchema()}        
        # self.params['order_by'] = "material.id, subq.entrada_saida"
        data = query2jsn(self.params, query, aplicar_limites=False, alias_schema={"material", MaterialSchema()})
        return data

    def titles(self):
        if self.objeto_atual:
            id_material = self.objeto_atual['id_material']
            material = MaterialModel.find_by_id(id_material).descricao
            self.title = f"FICHA DE MATERIAL: {material}"
            
            referencia = self.params.periodo_formatado()
            return [self.title, f'{referencia}']
        return ['Relatorio vazio']

class MaterialEstocagem(AlmoxReport):
    multimaterial = False
    def layout(self):
        LARGURA_INT = 15.75
        d =  OrderedDict({
            'id': {'w': 12, 'w_type': 'F', 'caption': 'Id'},
            'descricao': {'w': 0, 'w_type': 'S', 'caption': 'Material'},
            'unidade': {'w': 14, 'w_type': 'F', 'caption': 'Unid', 'align': 'C'},
            'estoque_atual': {'w': LARGURA_INT, 'w_type': 'F', 'align': 'R', 'caption': 'Estoque\natual', 'datatype': int},
            'consumo_anual': {'w': LARGURA_INT, 'w_type': 'F', 'align': 'R', 'caption': 'Consumo\nanual', 'datatype': int},
            'media_anual': {'w': LARGURA_INT-3.5, 'w_type': 'F', 'align': 'R', 'caption': 'Media\nanual', 'datatype': int},
            'estoque_minimo': {'w': LARGURA_INT-1.8, 'w_type': 'F', 'align': 'R', 'caption': 'Estoque\nminimo', 'datatype': int},
            'estoque_maximo': {'w': LARGURA_INT-1.8, 'w_type': 'F', 'align': 'R', 'caption': 'Estoque\nmaximo', 'datatype': int},
            'ponto_pedido': {'w': LARGURA_INT, 'w_type': 'F', 'align': 'R', 'caption': 'Ponto de\npedido', 'datatype': int},
            'qtd_ressuprir': {'w': LARGURA_INT, 'w_type': 'F', 'align': 'R', 'caption': 'Qtd. a\nressuprir', 'datatype': int},
        })
        return d
        
    def data(self):
        query = query_material_estocagem(self.params)
        return query, {}        
        # data = query2jsn(self.params, query, aplicar_limites=False)
        return data

    def titles(self):
        referencia = self.params.periodo_formatado()
        self.title = 'RELATÓRIO DE ESTOCAGEM'
        return [self.title, f'{referencia}']
        
