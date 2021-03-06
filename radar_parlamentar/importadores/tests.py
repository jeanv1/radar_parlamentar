#!/usr/bin/python
# coding=utf8

# Copyright (C) 2012, Leonardo Leite, Diego Rabatone
#
# This file is part of Radar Parlamentar.
#
# Radar Parlamentar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Radar Parlamentar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Radar Parlamentar.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from django.test import TestCase
from importadores import camara
from importadores import convencao
from modelagem import models
import os

class ConvencaoTest(TestCase):

    @classmethod
    def setUpClass(cls):
        importer = convencao.ImportadorConvencao()
        importer.importar()

    def setUp(self):
        self.conv = models.CasaLegislativa.objects.get(nome_curto='conv')

    def test_check_len_votacoes(self):
        NUM_VOTACOES = 8
        num_votacoes = len(models.Votacao.objects.filter(proposicao__casa_legislativa=self.conv))
        self.assertEquals(num_votacoes, NUM_VOTACOES)

    def test_check_len_votos(self):
        NUM_VOTOS = 8*3*3
        num_votos = len(models.Voto.objects.filter(votacao__proposicao__casa_legislativa=self.conv))
        self.assertEquals(num_votos, NUM_VOTOS)

    def test_check_len_votos_por_votacao(self):
        NUM_VOTOS_POR_VOTACAO = 3*3
        votacoes = models.Votacao.objects.filter(proposicao__casa_legislativa=self.conv)
        for votacao in votacoes:
            num_votos = len(models.Voto.objects.filter(votacao=votacao))
            self.assertEquals(num_votos, NUM_VOTOS_POR_VOTACAO)

    def test_check_partidos(self):
        partidos = models.Partido.objects.all()
        nomes_partidos = [p.nome for p in partidos]
        self.assertTrue(convencao.GIRONDINOS in nomes_partidos)
        self.assertTrue(convencao.JACOBINOS in nomes_partidos)
        self.assertTrue(convencao.MONARQUISTAS in nomes_partidos)

    def test_check_parlamentares(self):
        NUM_PARLAMENTARES = 3*3
        parlamentares = models.Parlamentar.objects.filter(legislatura__casa_legislativa=self.conv)
        self.assertEqual(len(parlamentares), NUM_PARLAMENTARES)
        nomes_parlamentares = [p.nome for p in parlamentares]
        self.assertEquals(nomes_parlamentares.count('Pierre'), NUM_PARLAMENTARES)

# constantes relativas ao código florestal
ID = '17338'
SIGLA = 'PL'
NUM = '1876'
ANO = '1999'
NOME = 'PL 1876/1999'

class CamaraTest(TestCase):
    """Testes do módulo camara"""

    @classmethod
    def setUpClass(cls):
        # vamos importar apenas as votações das proposições em votadas_test.txt
        camara.VOTADAS_FILE_PATH = camara.RESOURCES_FOLDER + 'votadas_test.txt'
        importer = camara.ImportadorCamara()
        importer.importar()

    def test_parse_votadas(self):

        importer = camara.ImportadorCamara()
        codigo_florestal =  {'ano': ANO, 'id': ID, 'num': NUM, 'sigla': SIGLA}
        self.assertTrue(codigo_florestal in importer.votadas_ids)

    def test_obter_proposicao(self):

        camaraws = camara.Camaraws()
        codigo_florestal_xml = camaraws.obter_proposicao(ID)
        nome = codigo_florestal_xml.find('nomeProposicao').text
        self.assertEquals(nome, NOME)

    def test_obter_votacoes(self):

        camaraws = camara.Camaraws()
        codigo_florestal_xml = camaraws.obter_votacoes(SIGLA, NUM, ANO)
        data_vot_encontrada = codigo_florestal_xml.find('Votacoes').find('Votacao').get('Data')
        self.assertEquals(data_vot_encontrada, '11/5/2011')

    def test_listar_proposicoes(self):

        camaraws = camara.Camaraws()
        pecs_2011_xml = camaraws.listar_proposicoes('PEC', '2011')
        pecs_elements = pecs_2011_xml.findall('proposicao')
        self.assertEquals(len(pecs_elements), 135)
        # 135 obtido por conferência manual com:
        # http://www.camara.gov.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoes?sigla=PEC&numero=&ano=2011&datApresentacaoIni=&datApresentacaoFim=&autor=&parteNomeAutor=&siglaPartidoAutor=&siglaUFAutor=&generoAutor=&codEstado=&codOrgaoEstado=&emTramitacao=

    def test_prop_nao_existe(self):

        id_que_nao_existe = 'id_que_nao_existe'
        camaraws = camara.Camaraws()
        caught = False
        try:
            camaraws.obter_proposicao(id_que_nao_existe)
        except ValueError as e:
            self.assertEquals(e.message, 'Proposição %s não encontrada' % id_que_nao_existe)
            caught = True
        self.assertTrue(caught)

    def test_votacoes_nao_existe(self):

        sigla = 'PCC'
        num = '1500'
        ano = '1876'
        camaraws = camara.Camaraws()
        caught = False
        try:
            camaraws.obter_votacoes(sigla, num, ano)
        except ValueError as e:
            self.assertEquals(e.message, 'Votações da proposição %s %s/%s não encontrada' % (sigla, num, ano))
            caught = True
        self.assertTrue(caught)

    def test_listar_proposicoes_que_nao_existem(self):

        sigla = 'PEC'
        ano = '3013'
        camaraws = camara.Camaraws()
        try:
            camaraws.listar_proposicoes(sigla, ano)
        except ValueError as e:
            self.assertEquals(e.message, 'Proposições não encontradas para sigla=%s&ano=%s' % (sigla, ano))
            caught = True
        self.assertTrue(caught)


    def test_casa_legislativa(self):

        camara = models.CasaLegislativa.objects.get(nome_curto='cdep')
        self.assertEquals(camara.nome, 'Câmara dos Deputados')

    def test_prop_cod_florestal(self):

        importer = camara.ImportadorCamara()
        data = importer._converte_data('19/10/1999')

        prop_cod_flor = models.Proposicao.objects.get(id_prop=ID)
        self.assertEquals(prop_cod_flor.nome(), NOME)
        self.assertEquals(prop_cod_flor.situacao, 'Tranformada no(a) Lei Ordinária 12651/2012')
        self.assertEquals(prop_cod_flor.data_apresentacao.day, data.day)
        self.assertEquals(prop_cod_flor.data_apresentacao.month, data.month)
        self.assertEquals(prop_cod_flor.data_apresentacao.year, data.year)

    def test_votacoes_cod_florestal(self):

        votacoes = models.Votacao.objects.filter(proposicao__id_prop=ID)
        self.assertEquals(len(votacoes), 5)

        vot = votacoes[0]
        self.assertTrue('REQUERIMENTO DE RETIRADA DE PAUTA' in vot.descricao)

        importer = camara.ImportadorCamara()
        data = importer._converte_data('24/5/2011', '20:52')
        vot = votacoes[1]
        self.assertEquals(vot.data.day, data.day)
        self.assertEquals(vot.data.month, data.month)
        self.assertEquals(vot.data.year, data.year)
        # vot.data está sem hora e minuto
#        self.assertEquals(vot.data.hour, data.hour)
#        self.assertEquals(vot.data.minute, data.minute)

    def test_votos_cod_florestal(self):

        votacao = models.Votacao.objects.filter(proposicao__id_prop=ID)[0]
        voto1 = [ v for v in votacao.votos() if v.legislatura.parlamentar.nome == 'Mara Gabrilli' ][0]
        voto2 = [ v for v in votacao.votos() if v.legislatura.parlamentar.nome == 'Carlos Roberto' ][0]
        self.assertEquals(voto1.opcao, models.SIM)
        self.assertEquals(voto2.opcao, models.NAO)
        self.assertEquals(voto1.legislatura.partido.nome, 'PSDB')
        self.assertEquals(voto2.legislatura.localidade, 'SP')

    def test_listar_siglas(self):

        camaraws = camara.Camaraws()
        siglas = camaraws.listar_siglas()
        self.assertTrue('PL' in siglas)
        self.assertTrue('PEC' in siglas)
        self.assertTrue('MPV' in siglas)


class ProposicoesFinderTest(TestCase):

    def test_find_props_existem_brute_force(self):

        ID_MIN = 12663
        ID_MAX = 12667
        IDS_QUE_EXISTEM = ['12665', '12666', '12667']
        IDS_QUE_NAO_EXISTEM = ['12663', '12664']
        FILE_NAME = 'ids_que_existem_test.txt'

        finder = camara.ProposicoesFinder(False) # False to verbose
        finder.find_props_que_existem_brute_force(FILE_NAME, ID_MIN, ID_MAX)
        props = finder.parse_ids_que_existem(FILE_NAME)

        for prop in props:
            self.assertTrue(prop['id'] in IDS_QUE_EXISTEM, 'prop %s não encontrada em IDS_QUE_EXISTEM' % prop['id'])

        for idp in IDS_QUE_NAO_EXISTEM:
            self.assertFalse(idp in [prop['id'] for prop in props])

        os.system('rm %s' % FILE_NAME)

    def test_find_props_existem(self):

        ANO_MIN = 2012
        IDS_QUE_EXISTEM = ['564446', '564313', '564126'] # proposições de 2012
        IDS_QUE_NAO_EXISTEM = ['382651', '382650'] # proposições de 2007
        FILE_NAME = 'ids_que_existem_test.txt'

        finder = camara.ProposicoesFinder(False) # False to verbose
        finder.find_props_que_existem(FILE_NAME, ANO_MIN)
        props = finder.parse_ids_que_existem(FILE_NAME)

        for idp in IDS_QUE_EXISTEM:
            self.assertTrue(idp in [prop['id'] for prop in props])

        for idp in IDS_QUE_NAO_EXISTEM:
            self.assertFalse(idp in [prop['id'] for prop in props])

        os.system('rm %s' % FILE_NAME)
