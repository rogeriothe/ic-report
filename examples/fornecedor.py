from collections import OrderedDict
import logging

from sqlalchemy import text
from almox.schemas.classificacao import ClassificacaoSchema
from almox.schemas.material import MaterialSchema

from fornecedor.models_db.fornecedor import query_fornecedor_cartao, query_fornecedor_total_compra_report, query_fornecedores_materiais_cartao
from fornecedor.schemas.fornecedor import FornecedorSchema
from db import formatquery, query2jsn
from .almox_report import AlmoxReport
from util import convert, prrint, ptx


class FornecedorReport(AlmoxReport):
    def layout(self):
        return OrderedDict({
            'fornecedor__id': {'w': 12, 'w_type': 'F', 'caption': 'Id',  'align': 'R'},
            'fornecedor__razao_social': {'w': 0.4, 'w_type': 'S', 'caption': 'Razão social'},
            'fornecedor__endereco_completo': {'w': 0.6, 'w_type': 'S', 'caption': 'Endereço'},
            'fornecedor__mercado_atuacao':  {'w': 24, 'w_type': 'F', 'caption': 'Mercado Atuação', 'group': False},
            'fornecedor__contato_completo':  {'w': 34, 'w_type': 'F', 'caption': 'Contato',  'align': 'C', 'new_page': False, 'group': False},
            'total_material': {'w': self.LARGURA_FLOAT + 2, 'w_type': 'F', 'align': 'R', 'caption': 'Valor Total', 'totalize': True},
        })

    def data(self):
        query = query_fornecedor_total_compra_report(self.params)
        return query, {'fornecedor': FornecedorSchema()}
        # return query2jsn(self.params, query, aplicar_limites=False, alias_schema={'fornecedor': FornecedorSchema()})

    def titles(self):
        self.title = 'RELATÓRIO DE FORNECEDORES - Total de Fornecimento'
        mercado_atuacao = self.params.get('mercado_atuacao')
        if mercado_atuacao:
            return [self.title, 'MERCADO DE ATUAÇÃO: ' + mercado_atuacao]
        return [self.title]


class FornecedorCartaoReport(AlmoxReport):
    ja_impresso = False

    def data(self):
        query = query_fornecedor_cartao(self.params)
        return query, {'fornecedor': FornecedorSchema()}

    def titles(self):
        self.title = 'FICHA DE CADASTRO DE FORNECEDOR'
        mercado_atuacao = self.params.get('mercado_atuacao')
        if mercado_atuacao:
            return [self.title, 'MERCADO DE ATUAÇÃO: ' + mercado_atuacao]
        return [self.title]

    def orientation(self):
        return 'P'

    def get_value_(self, campo: str, objeto):
        try:
            return convert(self.get_value_raw(campo, objeto))
        except TypeError as e:
            logging.error(f'Campo {campo} está nulo')
        return None
    
    def pre_cabecalho(self, pos_y):
        if self.ja_impresso:
            return pos_y
        self.ja_impresso = True
        data0 = self.data_singleton()[0]
        self.quadro(data0)
        return self.y

    def quadro(self, data0):
        id_ = self.get_value_('fornecedor__id', data0)
        cnpj_ = self.get_value_('fornecedor__cnpj', data0)
        razao_social_ = self.get_value_('fornecedor__razao_social', data0)
        nome_fantasia_ = self.get_value_('fornecedor__nome_fantasia', data0)
        endereco_ = self.get_value_('fornecedor__endereco', data0)

        numero_ = self.get_value_('fornecedor__numero', data0)
        bairro_ = self.get_value_('fornecedor__bairro', data0)
        cidade_ = self.get_value_('fornecedor__cidade', data0)
        uf_ = self.get_value_('fornecedor__uf', data0)
        cep_ = self.get_value_('fornecedor__cep', data0)
        complemento_ = self.get_value_('fornecedor__complemento', data0)
        cnpj_ = self.get_value_('fornecedor__cnpj', data0)
        inscricao_estadual_ = self.get_value_(
            'fornecedor__inscricao_estadual', data0)
        inscricao_municipal_ = self.get_value_(
            'fornecedor__inscricao_municipal', data0)
        mercado_atuacao_ = self.get_value_('fornecedor__mercado_atuacao', data0)
        telefone_comercial_ = self.get_value_(
            'fornecedor__telefone_comercial', data0)
        telefone_celular_ = self.get_value_('fornecedor__telefone_celular', data0)
        email_ = self.get_value_('fornecedor__email', data0)
        homepage_ = self.get_value_('fornecedor__homepage', data0)
        observacao_ = self.get_value_('fornecedor__observacao', data0)
        optante_simples_ = self.get_value_('fornecedor__optante_simples', data0)
        data_abertura_ = self.get_value_('fornecedor__data_abertura', data0)
        cnae_ = self.get_value_('fornecedor__cnae__descricao', data0)
        indicadorie_ = self.get_value_('fornecedor__indicadorie__descricao', data0)
        naturezajuridica_ = self.get_value_(
            'fornecedor__naturezajuridica__descricao', data0)
        data_cadastro_ = self.get_value_('fornecedor__data_cadastro', data0)
        relacionamentos_p_u = self.get_value_('relacionamentos_p_u', data0)

        with self.box() as g:
            g.box('ID', id_, w=15)
            cnpj_formatado = '{}.{}.{}/{}-{}'.format(cnpj_[:2], cnpj_[2:5], cnpj_[
                                                     5:8], cnpj_[8:12], cnpj_[12:])
            g.box('CNPJ', cnpj_formatado, w=40)
            g.box('Nome de Fantasia', nome_fantasia_)
            g.new_line()
            g.box('Email principal', email_, w=80)
            g.box('Telefone comercial', telefone_comercial_)
            g.box('Telefone celular', telefone_celular_)
            g.box('Abertura da Empresa', data_abertura_)
            g.new_line()
            g.box('Mercado de atuação', mercado_atuacao_, w=80)
            g.box('Natureza Jurídica', naturezajuridica_)
            g.new_line()
            g.box('CNAE Primário', cnae_, w=100)
            g.box('Data de Cadastro ', data_cadastro_, w=26)
            g.box('Relacionamentos (1º/Ult.)', relacionamentos_p_u)
            g.new_line()
            g.box('Razão Social', razao_social_, rgb='fff3b3')
            g.box('Optante pelo Simples',
                  'Sim' if optante_simples_ else 'Não', w=34)
            g.new_line()
            g.box('Indicador de Inscrição Estadual', indicadorie_)
            g.box('Inscrição Estadual', inscricao_estadual_)
            g.box('Inscrição Municipal', inscricao_municipal_)
            g.new_line()
            g.box('CEP', cep_, w=20)
            g.box('Endereço', endereco_)
            g.box('Número', numero_, w=20)
            g.new_line()
            g.box('UF', uf_, w=10)
            g.box('Cidade', cidade_)
            g.box('Bairro', bairro_)
            g.box('Complemento', complemento_)
            g.new_line()
            g.box('Pessoa de Contato', notext=True, border='LTBR')
            g.box('Email', notext=True, border='LTBR')
            g.box('Fone comercial', notext=True, border='LTBR', w=30)
            g.box('Fone Celular ', notext=True, border='LTBR', w=30)
            g.box('Cargo', notext=True, border='LTBR', w=22)

            contatos = self.get_value_raw('fornecedor__contatos', data0)
            if not contatos:
                contatos.append(dict())
            for contato in contatos:
                g.new_line()
                g.box(text=contato.get('nome'), nocaption=True, border='LR')
                g.box(text=contato.get('email'), nocaption=True, border='LR')
                g.box(text=contato.get('telefone_comercial'),
                      nocaption=True, border='LR', w=30)
                g.box(text=contato.get('telefone_celular'),
                      nocaption=True, border='LR', w=30)
                g.box(text=contato.get('cargo'),
                      nocaption=True, border='LR', w=22)

            g.new_line()
            # observacao_ = """A empresa tem sede na cidade do Rio de Janeiro e conta com uma equipe de funcionários dedicados a oferecer um atendimento personalizado e eficiente aos clientes. Além disso, a Zerk Aparelhos investe em tecnologia para garantir a segurança das transações online e a rapidez na entrega dos produtos."""
            g.box('Observação', observacao_, text_align='J')

            g.new_line()
            g.box('Home page', homepage_)

class FornecedorCartaoGiroReport(FornecedorCartaoReport):
    def layout(self):
        return OrderedDict({
            'material__classificacao__classificacao': {'w': 21, 'w_type': 'F', 'caption': 'Classificação'},
            'material__id': {'w': 12, 'w_type': 'F', 'caption': 'ID'},
            'material__descricao': {'w': 0, 'w_type': 'S', 'caption': 'Material'},
            'material__unidade': {'w': 15, 'w_type': 'F', 'caption': 'Unidade'},
            'quant_material':  {'w': 12, 'w_type': 'F', 'caption': 'Qtd', 'datatype':int, 'align': 'R'},
            'custo_medio_material':  {'w': 24, 'w_type': 'F', 'caption': 'Custo Médio', 'align': 'R'},
            'custo_total_material':  {'w': 24, 'w_type': 'F', 'caption': 'Custo Total', 'totalize': True, 'align': 'R'},
        })
    
    def get_value_raw(self, campo, objeto):
        try:
            value = super().get_value_raw(campo, objeto)
        except Exception as e:
            return ''
        return value
        
    def titles(self):
        self.title = 'FICHA DE CADASTRO DE FORNECEDOR'
        referencia = self.params.periodo_formatado()
        return [self.title, f'{referencia}']

    
    def data(self):
        query = query_fornecedores_materiais_cartao(self.params)
        return query, {'material': MaterialSchema()}

    def pre_cabecalho(self, pos_y):
        if self.ja_impresso:
            return pos_y
        self.ja_impresso = True
        data0 = self.data_singleton()[0]
        # prrint(self.data_singleton())

        id_ = self.get_value_('id_fornecedor', data0)
        params = dict(self.params)
        params['order_by'] = 'fornecedor__id'
        params['fields'] = [{'fornecedor__id': id_}]

        query = query_fornecedor_cartao(params)
        data1 = query2jsn(params, query, aplicar_limites=False, alias_schema={'fornecedor': FornecedorSchema()})[0]

        # prrint(data1)
        self.quadro(data1)

        
        return self.y
