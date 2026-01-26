# -*- coding: utf-8 -*-
from io import BytesIO
import logging
from collections import OrderedDict
from datetime import date, datetime
from tempfile import NamedTemporaryFile

from almox.models.departamento import DepartamentoModel
from consts import TD_LOGOTIPO
from db import formatquery, get_order_by_query
from ged.models_db.documento import query_documentos
from ged.util.S3 import s3_get_documento
from ic_reports.report import Report
from ic_reports.utils import get_image_size
from util import Params, prrint, ptx
from ymago.models import usuario
from ymago.models.usuario import EmpresaModel, UsuarioModel


class AlmoxReport(Report):
    def __init__(self, params) -> None:
        super().__init__(params)
        if 'title' in params:
            self.title = params['title']
        self.usuario: UsuarioModel = params['usuario']
        self.empresa = params['empresa']
        self.departamento = DepartamentoModel.find_by_id(self.usuario.departamentos[0].id_departamento)

    def layout(self) -> OrderedDict:
        return OrderedDict({})

    def data(self):
        ...

        

    def titles(self):
        return self.params['title'] if isinstance(self.params['title'], list) else [self.params['title']]

    def logotipo_tempfile(self, nome: str, logo: bytes) -> str:
        if not nome in self._temp_images_files.keys():
            with NamedTemporaryFile(suffix='.png', delete=False) as file:
                file.write(logo)
                file.flush()
                self._temp_images_files[nome] = file

        return self._temp_images_files[nome].name


    def ler_logotipo(self, empresa, key):
        if not key in self.imagens:
            _params = Params(self.usuario, empresa, {"per_page": 1, "order_by": "update_date", "descending": True, "fields": [{"id_tipodocumento":TD_LOGOTIPO}]})
            _params.add_filtro_empresa_documento()
            query = query_documentos(_params)
            query = get_order_by_query(_params, query)
            docs = query.all()
            if docs:
                documento_data = docs[0]
                doc_s3 = s3_get_documento(documento_data.cnpj_cpf, documento_data.nome_arquivo)
                self.imagens[key] = doc_s3
        return self.logotipo_tempfile(key, self.imagens[key])

    def logotipo_ymago(self, ):
        key='logotipo_ymago'
        return self.ler_logotipo(self.empresa_ymago, key)

    def logotipo_empresa(self):
        '''baixa o logotipo e adiciona no cache de imagens'''
        # prrint(title=str(self.imagens.keys()))
        key = 'logotipo_empresa'
        if not key in self.imagens:
            # breakpoint()
            logo = self.ler_logotipo(self.empresa, key)
            if logo:
                return logo
            else:
                return self.logotipo_ymago()
        return self.logotipo_tempfile(key, self.imagens[key])
        # se não tiver logo, retorna a do YMAGO

    def header(self):
        texto_esquema = {
            4:  {
                "altura_linha": [4, 4, 4, 3],
                "tamanho_fonte": [10, 9, 9, 9],
                "style": ['B', 'B', '', ''],
                },
            3: {
                "altura_linha": [5, 5, 5],
                "tamanho_fonte": [11, 10, 10],
                "style": ['B', 'B', ''],
                },
        }
        # linhas_cabecalho.append(self.empresa.razao_social)
        departamento_base = self.departamento.id
        dep = DepartamentoModel.find_by_id(departamento_base)
        linhas_cabecalho = [self.empresa.razao_social, dep.centrocusto.descricao]
        len_atual = len(linhas_cabecalho)
        
        while True:
            linhas_cabecalho.insert(len_atual, dep.descricao)
            dep = dep.departamento_pai
            if not dep:
                break
        #no máximo 4 linhas, excluir sempre a penultima quando estrapolar
        while len(linhas_cabecalho) > 4:
            del linhas_cabecalho[-2]
        while len(linhas_cabecalho) < 3:
            linhas_cabecalho.append('LINHA ADICIONADA AUTOMATICAMENTE PARA SUPRIR UM MINIMO DE 3')

        #LOGOTIPO EMPRESA
        new_h_img = 15
        tmp_file_logotipo_empresa = self.logotipo_empresa() # chama para inicilizar o dict self.imgaens
        img_width, img_height = get_image_size(self.imagens['logotipo_empresa'])
        new_w_img = new_h_img * (img_width/img_height)
        self.image(tmp_file_logotipo_empresa , self.l_margin, self.t_margin, h=new_h_img, w=new_w_img, type='png')
        
        #LOGOTIPO YMAGO
        new_h_img = 11
        tmp_file_logotipo_ymago = self.logotipo_ymago() # chama para inicilizar o dict self.imgaens
        img_width_ymago, img_height_ymago = get_image_size(self.imagens['logotipo_ymago'])
        new_w_img_ymago = new_h_img * (img_width_ymago/img_height_ymago)
        # self.image(tmp_file_logotipo_ymago, self.w - self.r_margin - new_w_img_ymago, self.t_margin, type='png', h=0, w=0)
        self.image(tmp_file_logotipo_ymago, self.w - self.r_margin - new_w_img_ymago, self.t_margin, type='png', h=new_h_img, w=new_w_img_ymago)

        distancia_logo= 1
        tem_borda = 0
        offset_img = new_w_img + distancia_logo + self.l_margin

        self.set_fill_color(255, 255, 255)
        te = texto_esquema[len(linhas_cabecalho)]
        altura_linha = 0
        for index_linha, texto_to_print in enumerate(linhas_cabecalho):
            self.x = offset_img
            altura_linha = te['altura_linha'][index_linha]
            font_size = te['tamanho_fonte'][index_linha]
            font_style = te['style'][index_linha]
            self.set_font(self.font_base_name, font_style, font_size)
            self.cell(w=self.w - self.l_margin - self.r_margin - new_w_img - new_w_img_ymago - distancia_logo * 2, h=altura_linha, txt=texto_to_print, border=tem_borda, ln=0)
            self.ln(altura_linha)
        
        self.y -= altura_linha
        altura_linha = 3.5
        self.ln(altura_linha * 2)
        self.set_font(self.font_base_name, 'B', 10)
        for title in self.titles():
            self.x = offset_img
            self.cell(w=0, h=altura_linha, txt=title, border=tem_borda, ln=0, align='C')
            self.y += (altura_linha)
        # self.y -= altura_linha / 2
        self.ln(altura_linha)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font(self.font_base_name, 'I', 8)
        # Page number
        data = datetime.strftime(datetime.today(), '%d/%m/%Y %Hh%Mmin')
        pag_no = 'página ' + str(self.page_no()) + '/{nb}'
        # w = self.w - self.l_margin - self.r_margin - self.get_string_width(pag_no)
        # self.x = self.w - self.r_margin - self.get_string_width(pag_no)
        self.cell(w=0, h=3, txt=pag_no, border=0, ln=0, align='L')    
        self.cell(w=0, h=3, txt=f'{self.usuario.login} em: {data}', border=0, ln=0, align='R')    

    def localidade_data(self):
        data_formatada = datetime.strftime(date.today(), '%d de %B de %Y')
        self.cell(0, 16, f'{self.empresa.localidade}, {data_formatada}', 0, 0, 'C')

    def assinatura(self, *nomes_adicionais):
        '''imprime assinaturas para o usuario e nomes adicionais'''
        self.set_font(self.font_base_name, 'I', 10)
        nomes = [self.usuario.nome]
        nomes.extend(nomes_adicionais)
        w = self.w
        self.y += 10
        comprimento_linha_ass = 60
        nome_len = len(nomes)
        comprimento_separacao = [0,10,5][nome_len-1]

        w_util = nome_len * comprimento_linha_ass + (nome_len - 1) * comprimento_separacao
        x_inicial = (w - w_util) / 2
        self.x = x_inicial
        old_y = self.y

        for nome in nomes:
            old_x = self.x
            self.y = old_y + 1
            h = self.multi_cell(comprimento_linha_ass, 3, f'{nome}' , 0, 'C', split_only=True)
            self.multi_cell(comprimento_linha_ass, 3, f'{nome}' , 0, 'C')
            self.y = old_y
            self.x = old_x
            self.cell(comprimento_linha_ass, 1, '', 'T', 0, 'C')
            self.x += comprimento_separacao

    
    def simples_pos_tudo(self, *nomes_adicionais):
        TAMANHO = 26
        if (self.y + TAMANHO) > (self.h - self.b_margin):
            self.add_page(orientation=self.orientation())
            self.imprimir_cabecalho(self.y)

        self.localidade_data()
        self.y += 10
        self.assinatura(*nomes_adicionais)
        self.p(ln=1)
        return self.y

    def pos_tudo(self):
        return self.simples_pos_tudo()        
