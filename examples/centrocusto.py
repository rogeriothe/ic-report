from collections import OrderedDict
import json
from pprint import pprint

from almox.models.tipomaterial import TipoMaterialModel
from almox.models_db.centrocusto import (query_centrocusto_classificacao_report)
from almox.schemas.classificacao import ClassificacaoSchema
from almox.schemas.material import MaterialSchema
from db import print_query_alias, query2jsn, formatquery, get_dict_from_query_schema
from .almox_report import AlmoxReport
from util import auto_formata_periodo, prrint


class CentroCustoClassificacaoReport(AlmoxReport):
    def layout(self):
        return OrderedDict({
            'centrocusto': {'w': 0, 'w_type': 'S', 'caption': 'Centro de Custo',  'align': 'L', 'group': True, 'sum': ['custo_total'], 'new_page': False},
            'departamento': {'w': 0, 'w_type': 'S', 'caption': 'Departamento', 'group': True, 'sum': ['custo_total']},
            'classificacao_descricao': {'w': 0, 'w_type': 'S', 'caption': 'Classificação', 'group': True, 'sum': ['custo_total']},
            'material': {'w': 0, 'w_type': 'S', 'caption': 'Material',  'align': 'L'},
            'unidade': {'w': 13, 'w_type': 'F', 'caption': 'Unid'},
            'qtd': {'w': 12, 'w_type': 'F', 'align': 'R', 'caption': 'Qtd'},
            'custo_total': {'w': self.LARGURA_FLOAT + 3, 'w_type': 'F', 'align': 'R', 'caption': 'Custo Total', 'totalize': True},
        })
 
    def data(self):
        # print(json.dumps(self.layout()))
        self.params['order_by'] = '5,6,7,8'#'centrocusto.id, departamento.id, classificacao.id, material.id'
        query = query_centrocusto_classificacao_report(self.params)
        # prrint(formatquery(query))
        return query, {}
        # return query2jsn(self.params, query, aplicar_limites=False)

    def titles(self):
        # tm = self.params.check_params_id_fk(TipoMaterialModel, 'id_tipomaterial', 'Tipo de material inválido')
        # prrint(self.objeto_atual)
        referencia = self.params.periodo_formatado()
        self.title = f'RELATÓRIO GERENCIAL DE CENTRO DE CUSTO'
        return [self.title, f'{referencia}']
   
