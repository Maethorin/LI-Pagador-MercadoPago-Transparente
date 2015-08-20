# -*- coding: utf-8 -*-
import json
import os
import unittest
import mock
from pagador_mercadopago_transparente import servicos


class MPTransparenteCredenciais(unittest.TestCase):
    def test_deve_definir_propriedades(self):
        credenciador = servicos.Credenciador(configuracao=mock.MagicMock())
        credenciador.tipo.should.be.equal(credenciador.TipoAutenticacao.query_string)
        credenciador.chave.should.be.equal('access_token')

    def test_deve_retornar_credencial_baseado_no_usuario(self):
        configuracao = mock.MagicMock(token='api-key')
        credenciador = servicos.Credenciador(configuracao=configuracao)
        credenciador.obter_credenciais().should.be.equal('api-key')


class MPTransparenteSituacoesPagamento(unittest.TestCase):
    def test_deve_retornar_pago_para_approved(self):
        servicos.SituacoesDePagamento.do_tipo('approved').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO)

    def test_deve_retornar_cancelado_para_rejected(self):
        servicos.SituacoesDePagamento.do_tipo('rejected').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO)

    def test_deve_retornar_none_para_desconhecido(self):
        servicos.SituacoesDePagamento.do_tipo('zas').should.be.none


class MPTransparenteEntregaPagamento(unittest.TestCase):
    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_dizer_que_tem_malote(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.tem_malote.should.be.truthy

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_dizer_que_faz_http(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.faz_http.should.be.truthy

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_definir_resposta(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.resposta.should.be.none

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_definir_url(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.url.should.be.equal('https://api.mercadolibre.com/checkout/custom/create_payment')

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao')
    def test_deve_montar_conexao(self, obter_mock):
        conexao = mock.MagicMock()
        obter_mock.return_value = conexao
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.conexao.should.be.equal(conexao)
        obter_mock.assert_called_with()

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.servicos.Credenciador')
    def test_deve_definir_credenciais(self, credenciador_mock):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        credenciador_mock.return_value = 'credenciador'
        entregador.configuracao = 'configuracao'
        entregador.define_credenciais()
        entregador.conexao.credenciador.should.be.equal('credenciador')
        credenciador_mock.assert_called_with(configuracao='configuracao')

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador.servicos.EntregaPagamento.define_pedido_e_configuracao')
    def test_deve_definir_configuracao_e_pedido_de_servico(self, define_mock):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.configuracao = 'configuracao'
        entregador.pedido = 'pedido'
        entregador.define_pedido_e_configuracao(1234)
        define_mock.assert_called_with(1234)
        entregador.configuracao.should.be.equal('configuracao')
        entregador.pedido.should.be.equal('pedido')

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_enviar_pagamento(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = {'zas': 'malote-como-dicionario'}
        entregador.conexao = mock.MagicMock()
        entregador.pedido = mock.MagicMock(situacao_id=None)
        entregador.dados = {'next_url': 'zas'}
        resposta_mock = mock.MagicMock(nao_autorizado=False, nao_autenticado=False)
        entregador.conexao.post.return_value = resposta_mock
        entregador.envia_pagamento()
        entregador.dados_enviados.should.be.equal({'tentativa': 1, 'zas': 'malote-como-dicionario'})
        entregador.resposta.should.be.equal(resposta_mock)

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_usar_post_ao_enviar_pagamento(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = {'zas': 'malote-como-dicionario'}
        entregador.conexao = mock.MagicMock()
        entregador.pedido = mock.MagicMock(situacao_id=None)
        entregador.envia_pagamento()
        entregador.conexao.post.assert_called_with(entregador.url, {'zas': 'malote-como-dicionario'})

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_enviar_pagamento_dispara_erro_pedido_ja_realizado_e_cancelado(self):
        entregador = servicos.EntregaPagamento(8, dados={})
        entregador.pedido = mock.MagicMock(numero=1234, situacao_id=8)
        entregador.envia_pagamento.when.called_with().should.throw(
            entregador.PedidoJaRealizado, u'Já foi realizado um pedido com o número 1234 e ele está como Pedido Cancelado.\nSeu pedido foi cancelado e não pode ser mais usado. Você precisa fazer um novo pedido na loja.'
        )

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_enviar_pagamento_dispara_erro_pedido_ja_realizado_e_pago(self):
        entregador = servicos.EntregaPagamento(8, dados={})
        entregador.pedido = mock.MagicMock(numero=1234, situacao_id=4)
        entregador.envia_pagamento.when.called_with().should.throw(
            entregador.PedidoJaRealizado, u'Já foi realizado um pedido com o número 1234 e ele está como Pedido Pago.\nSeu pagamento já está pago e estamos processando o envio'
        )

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.servicos.TEMPO_MAXIMO_ESPERA_NOTIFICACAO', 1)
    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.cria_entidade_pagador')
    def test_processar_dados_de_pagamento_define_dados_pagamento(self, cria_pedido_mock):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.servico = mock.MagicMock()
        entregador.configuracao = mock.MagicMock(loja_id=8)
        entregador.pedido = mock.MagicMock(numero=123, valor_total=15.70, conteudo_json={'mptransparente': {'valor_parcela': 15.7}})
        entregador.malote = mock.MagicMock(amount=15.70, payment_method_id='visa')
        entregador.resposta = mock.MagicMock(sucesso=True, requisicao_invalida=False, conteudo={'status': 'approved', 'status_detail': 'accredited', 'payment_id': 'transacao-id', 'amount': 123.45, 'payment_method_id': 'visa'})
        cria_pedido_mock.return_value = mock.MagicMock(situacao_id=9)
        entregador.processa_dados_pagamento()
        cria_pedido_mock.assert_called_with('Pedido', numero=123, loja_id=8)
        entregador.dados_pagamento.should.be.equal({'conteudo_json': {'bandeira': 'visa', 'mensagem_retorno': u'Seu pagamento foi aprovado com sucesso.', 'numero_parcelas': 1, 'valor_parcela': 15.7}, 'transacao_id': 'transacao-id', 'valor_pago': 15.7})

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.servicos.TEMPO_MAXIMO_ESPERA_NOTIFICACAO', 1)
    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.cria_entidade_pagador')
    def test_processar_dados_de_pagamento_retorna_se_notificacao_jah_atualizou(self, cria_pedido_mock):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.servico = mock.MagicMock()
        entregador.configuracao = mock.MagicMock(loja_id=8)
        entregador.pedido = mock.MagicMock(numero=123)
        cria_pedido_mock.return_value = mock.MagicMock(situacao_id=4)
        entregador.processa_dados_pagamento()
        cria_pedido_mock.assert_called_with('Pedido', numero=123, loja_id=8)
        entregador.dados_pagamento.should.be.none
        entregador.resultado.should.be.equal({'fatal': False, 'mensagem': '', 'resultado': 'alterado_por_notificacao'})

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.servicos.TEMPO_MAXIMO_ESPERA_NOTIFICACAO', 0)
    def test_processar_dados_de_pagamento_dispara_erro_se_invalido(self):
        entregador = servicos.EntregaPagamento(8, dados={'passo': 'pre'})
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = {'card_hash': None, 'capture': 'false', 'amount': 2900, 'installments': 1, 'payment_method': 'credit_card'}
        entregador.pedido = mock.MagicMock(numero=1234)
        entregador.resposta = mock.MagicMock(sucesso=False, requisicao_invalida=True, conteudo={u'url': u'/transactions', u'errors': [{u'message': u'Nome do portador do cartão está faltando', u'type': u'invalid_parameter', u'parameter_name': u'card_holder_name'}, {u'message': u'Data de expiração do cartão está faltando', u'type': u'invalid_parameter', u'parameter_name': u'card_expiration_date'}], u'method': u'post'})
        entregador.processa_dados_pagamento.when.called_with().should.throw(
            entregador.EnvioNaoRealizado, u'Dados inválidos enviados ao MercadoPago'
        )

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.servicos.TEMPO_MAXIMO_ESPERA_NOTIFICACAO', 0)
    def test_processar_dados_de_pagamento_dispara_erro_sem_ser_parameter(self):
        entregador = servicos.EntregaPagamento(8, dados={'passo': 'pre'})
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = {'card_hash': None, 'capture': 'false', 'amount': 2900, 'installments': 1, 'payment_method': 'credit_card'}
        entregador.pedido = mock.MagicMock(numero=1234)
        entregador.resposta = mock.MagicMock(sucesso=False, requisicao_invalida=True, conteudo={u'url': u'/transactions', u'errors': [{u'message': u'Nome do portador do cartão está faltando', u'type': u'whatever'}, {u'message': u'Data de expiração do cartão está faltando', u'type': u'whatever'}], u'method': u'post'})
        entregador.processa_dados_pagamento.when.called_with().should.throw(
            entregador.EnvioNaoRealizado, u'Dados inválidos enviados ao MercadoPago'
        )

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.servicos.TEMPO_MAXIMO_ESPERA_NOTIFICACAO', 0)
    def test_processar_dados_de_pagamento_define_identificador_id(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.configuracao = mock.MagicMock(aplicacao='test')
        entregador.pedido = mock.MagicMock(numero=123, valor_total=15.70, conteudo_json={'mptransparente': {'valor_parcela': 15.7}})
        entregador.malote = mock.MagicMock(amount=15.70, payment_method_id='visa')
        entregador.servico = mock.MagicMock()
        entregador.resposta = mock.MagicMock(sucesso=True, requisicao_invalida=False, conteudo={'status': 'approved', 'status_detail': 'accredited', 'payment_id': 'transacao-id', 'amount': 123.45, 'payment_method_id': 'visa'})
        entregador.processa_dados_pagamento()
        entregador.identificacao_pagamento.should.be.equal('transacao-id')


class MPTransparenteAtualizaTransacoes(unittest.TestCase):
    @mock.patch('pagador_mercadopago_transparente.servicos.AtualizaTransacoes.obter_conexao')
    def test_monta_consulta_corretamente(self, obter_con_mock):
        atualizador = servicos.AtualizaTransacoes(1234, dados={'data_inicial': '2015-08-22', 'data_final': '2015-08-23'})
        atualizador.consulta_transacoes()
        obter_con_mock.return_value.get.assert_called_with('https://api.mercadopago.com/collections/search', dados={'sort': 'date_created', 'begin_date': '2015-08-22T00:00', 'end_date': '2015-08-23T23:59', 'range': 'date_created', 'limit': 1000, 'criteria': 'desc'})

    @mock.patch('pagador_mercadopago_transparente.servicos.AtualizaTransacoes.obter_conexao', mock.MagicMock)
    def test_resultado_com_erro(self):
        atualizador = servicos.AtualizaTransacoes(1234, dados={'data_inicial': '2015-08-22', 'data_final': '2015-08-23'})
        atualizador.resposta = mock.MagicMock(sucesso=False, conteudo={'message': 'invalid_token', 'cause': [0], 'error': 'not_found','status': 401})
        atualizador.analisa_resultado_transacoes()
        atualizador.dados_pedido.should.be.empty
        atualizador.erros.should.be.equal({'cause': [0], 'error': 'not_found', 'message': 'invalid_token', 'status': 401})

    @mock.patch('pagador_mercadopago_transparente.servicos.AtualizaTransacoes.obter_conexao', mock.MagicMock)
    def test_resultado_com_erro(self):
        atualizador = servicos.AtualizaTransacoes(1234, dados={'data_inicial': '2015-08-22', 'data_final': '2015-08-23'})
        atualizador.resposta = mock.MagicMock(sucesso=False, conteudo={'message': 'invalid_token', 'cause': [0], 'error': 'not_found','status': 401})
        atualizador.analisa_resultado_transacoes()
        atualizador.dados_pedido.should.be.empty
        atualizador.erros.should.be.equal({'cause': [0], 'error': 'not_found', 'message': 'invalid_token', 'status': 401})

    @mock.patch('pagador_mercadopago_transparente.servicos.AtualizaTransacoes.obter_conexao', mock.MagicMock)
    def test_resultado_com_dados_de_pedido(self):
        atualizador = servicos.AtualizaTransacoes(1234, dados={'data_inicial': '2015-08-22', 'data_final': '2015-08-23'})
        conteudo = json.load(open(os.path.join(os.path.abspath(os.path.curdir), 'unitarios', 'reposta_consulta_transacoes.json')))
        atualizador.resposta = mock.MagicMock(sucesso=True, conteudo=conteudo)
        atualizador.analisa_resultado_transacoes()
        atualizador.dados_pedido.should.be.equal([{'situacao_pedido': 4, 'pedido_numero': u'168'}, {'situacao_pedido': 4, 'pedido_numero': u'166'}])
