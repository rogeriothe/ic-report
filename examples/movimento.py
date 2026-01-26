import logging
from collections import OrderedDict
from datetime import date, datetime

from almox.models.material import MaterialModel
from almox.models.movimento import MovimentoItensModel, MovimentoModel
from almox.models_db.movimento import query_aquisicao_report, query_movimento_report
from db import db, query2jsn, formatquery
from .almox_report import AlmoxReport
from util import lambda_to_str, prrint


class MovimentoAquisicaoReport(AlmoxReport):
    def layout(self): 
        return OrderedDict({
            'id': {'w':13, 'w_type': 'F', 'caption': 'Id Mov', 'align': 'L'},
            'classificacao': {'w': 20, 'w_type': 'F', 'caption': 'Classif'},
            'material': {'w': 0, 'w_type': 'S', 'caption': 'Descrição do Material'},
            'unidade': {'w': 12, 'w_type': 'F', 'caption': 'Unid'},
            'valor_unitario': {'w': 24, 'w_type': 'F', 'caption': 'Valor Unitário', 'align': 'R'},
            'quant': {'w':12, 'w_type': 'F', 'caption': 'Quant', 'align': 'R'},
            'custo': {'w':25, 'w_type': 'F', 'caption': 'Custo Total', 'align': 'R', "totalize": True},
            'processo': {'w': 30, 'w_type': 'F', 'caption': 'Processo', 'align': 'L'},
            'nota_fiscal': {'w': 40, 'w_type': 'F', 'caption': 'Nota Fiscal', 'align': 'L'},
            'ne': {'w': 10, 'w_type': 'F', 'caption': 'NE', 'align': 'C'},
            'rm': {'w': 10, 'w_type': 'F', 'caption': 'RM', 'align': 'C'},
            'data': {'w': 21, 'w_type': 'F', 'caption': 'Dt Entrada', 'align': 'R'},
        })

    def data(self):        
        query = query_aquisicao_report(self.params)
        return query, {}
    
    def titles(self):
        data0 = self.data_singleton()[0]
        referencia = self.params.periodo_formatado()
        self.title = f"RELATÓRIO DE AQUISIÇÕES DE MATERIAIS: {self.get_value_raw('tipo_material', data0).upper()}"
        return [self.title, f'{referencia}']    

    def orientation(self):
        return 'L'


class MovimentoReport(AlmoxReport):
    def layout(self): 
        return OrderedDict({
            'id_material': {'w':10, 'w_type': 'F', 'caption': 'Id', 'align': 'L'},
            'classificacao_material_descricao': {'w': 0, 'w_type': 'S', 'caption': 'Descrição do Material'},
            'qtd': {'w':15, 'w_type': 'F', 'caption': 'Qtd.', 'align': 'R'},
            'unidade': {'w': 12, 'w_type': 'F', 'caption': 'Unid.', 'align': 'C', 'group': False, 'sum': ['custo_total']},
            'custo_medio': {'w': 25, 'w_type': 'F', 'caption': 'Unitário', 'align': 'R', "totalize":False},
            'custo_total': {'w': 25, 'w_type': 'F', 'caption': 'Valor Total','align': 'R', "totalize":True},
            
        })

    def data(self):        
        query = query_movimento_report(self.params)
        return query, {}
        data = query2jsn(self.params, query, aplicar_limites=False)
        return data

    def titles(self):
        data0 = self.data_singleton()[0]
        tits = \
            {
                1: f"NOTA DE ENTRADA",
                2: f"FORNECIMENTO DE MATERIAL",
                3: f"REQUISIÇÃO DE MATERIAL",
                4: f"AUTORIZAÇÃO DE MATERIAL",
            }
        id_ = self.get_value_raw('id', data0)
        ne_ = '/NE ' + self.get_value_raw('ne', data0) if self.get_value_raw('fornecedor_id', data0) else ''
        rm_ = '/RM ' + self.get_value_raw('rm', data0) if self.get_value_raw('departamento_id', data0) else ''
        c4td_ = self.get_value_raw('classificacao4_tipomaterial_descricao', data0)
        tm_ = tits[self.get_value_raw('id_tipomovimento', data0)]
        self.title = f"{tm_} (Id {id_}{ne_}{rm_}): {c4td_}"
        return [self.title]

    def orientation(self):
        return 'P'

    def pre_cabecalho(self, pos_y):
        data0 = self.data_singleton()[0]
        # print('*' * 80)
        # print(data0)
        # print('*' * 80)
        id_tipomovimento = self.get_value_raw('id_tipomovimento', data0)
        # salto = 160
        self.y = pos_y
        self.x = self.l_margin
        uso_generico = self.get_value_raw('uso_generico', data0)
        cnpj = str(self.get_value_raw('fornecedor_cnpj', data0))
        cnpj = f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}'
        fornecedor = f"{self.get_value('fornecedor_id', data0)} - {self.get_value('fornecedor', data0)} ({cnpj})"
        departamento = f"{self.get_value_raw('departamento_id', data0)} - {self.get_value('departamento', data0)}"
        departamento_destino = f"{self.get_value_raw('departamento_destino_id', data0)} - {self.get_value('departamento_destino', data0)}"
        emissao = self.get_value_raw('emissao', data0)
        entrada_saida = self.get_value_raw('entrada_saida', data0)
        emissao_dtnota = emissao if emissao else ''
        documento = self.get_value_raw('documento', data0)
        processo = self.get_value_raw('processo', data0)
        empenho = self.get_value('empenho', data0)
        obs = self.get_value('observacao', data0)

        pedido_nota_fiscal = f"{documento} ({emissao_dtnota})"
        # logging.debug(data0)
        # logging.debug(f'{processo=}')
        data_entrada = entrada_saida if entrada_saida else ''
        # print(f'{id_tipomovimento=} {uso_generico=}')
        # self.font_base_size = 10
        if id_tipomovimento == 1 or id_tipomovimento == 2 and uso_generico:
            if self.get_value_raw('fornecedor_id', data0):
                self.p('Fornecedor:', fornecedor, ln=1)
            self.p('Nota Fiscal Nº:', pedido_nota_fiscal, w=75)
            if processo:
                self.p('Processo:', processo)
            self.p('Empenho:', empenho, w=-38, ln=1)
            if self.get_value_raw('departamento_destino_id', data0):
                self.p('Dep. Destino:', departamento_destino)
                self.p('Dt. Entrada:', data_entrada, w=-38, ln=1)
                self.p('Observação:', obs, ln=1)
            else:
                self.p('Observação:', self.get_value('observacao', data0))
                self.p('Dt. Entrada:', data_entrada, w=-38, ln=1)
        else:
            self.p('Requisitante:', departamento)
            self.p('Pedido:', pedido_nota_fiscal, w=-55, ln=1)
            self.p('Dep. Destino:', departamento_destino)
            self.p('Dt. Req:', emissao_dtnota, w=-55, ln=1)
            self.p('Observação:', obs, ln=1)
        self.font_base_size = 8
        self.p(ln = 1)
        return self.y

    
        