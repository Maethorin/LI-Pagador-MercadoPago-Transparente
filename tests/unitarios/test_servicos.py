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

RESULTADO_TRANSACOES = """
{
  "paging": {
    "total": 16,
    "limit": 1000,
    "offset": 0
  },
  "results": [
    {
      "collection": {
        "id": 1278823433,
        "site_id": "MLB",
        "date_created": "2015-08-20T16:18:29.000-04:00",
        "date_approved": "2015-08-20T16:18:29.000-04:00",
        "last_modified": "2015-08-20T16:18:29.000-04:00",
        "money_release_date": "2015-09-10T16:18:29.000-04:00",
        "operation_type": "regular_payment",
        "collector_id": 129324129,
        "sponsor_id": null,
        "payer": {
          "nickname": "@190628696",
          "first_name": "Camila",
          "last_name": "Barbosa",
          "phone": {
            "area_code": null,
            "number": null,
            "extension": null
          },
          "email": "camilinha.fjv4@gmail.com",
          "id": 190628696,
          "identification": {
            "type": "CPF",
            "number": "13129851780"
          }
        },
        "external_reference": "168",
        "merchant_order_id": null,
        "reason": "Pagamento do pedido 168 na Loja BrasilLaser Ateliê de Personalizados",
        "currency_id": "BRL",
        "transaction_amount": 77,
        "total_paid_amount": 79.32,
        "shipping_cost": 0,
        "account_money_amount": 0,
        "mercadopago_fee": 3.84,
        "net_received_amount": 73.16,
        "marketplace_fee": null,
        "coupon_id": null,
        "coupon_amount": null,
        "coupon_fee": null,
        "finance_fee": 0,
        "status": "approved",
        "status_detail": "accredited",
        "status_code": "00",
        "released": "no",
        "payment_type": "credit_card",
        "installments": 2,
        "installment_amount": null,
        "deferred_period": null,
        "cardholder": {
          "name": "Kamila s nascimento",
          "identification": {
            "type": "CPF",
            "number": "13129851780"
          }
        },
        "statement_descriptor": "MERCADOPAGO*",
        "transaction_order_id": null,
        "last_four_digits": "4832",
        "payment_method_id": "master",
        "marketplace": "NONE",
        "tags": [],
        "refunds": [],
        "amount_refunded": 0,
        "notification_url": "https://api.awsli.com.br/pagador/meio-pagamento/mptransparente/retorno/176321/notificacao?referencia=168"
      }
    },
    {
      "collection": {
        "id": 1278471699,
        "site_id": "MLB",
        "date_created": "2015-08-20T09:52:38.000-04:00",
        "date_approved": "2015-08-20T09:52:38.000-04:00",
        "last_modified": "2015-08-20T09:52:38.000-04:00",
        "money_release_date": "2015-09-10T09:52:38.000-04:00",
        "operation_type": "regular_payment",
        "collector_id": 129324129,
        "sponsor_id": null,
        "payer": {
          "nickname": "@190595187",
          "first_name": "Katia",
          "last_name": "Rodrigues",
          "phone": {
            "area_code": null,
            "number": null,
            "extension": null
          },
          "email": "katiar3@yahoo.com.br",
          "id": 190595187,
          "identification": {
            "type": "CPF",
            "number": "44274050106"
          }
        },
        "external_reference": "166",
        "merchant_order_id": null,
        "reason": "Pagamento do pedido 166 na Loja BrasilLaser Ateliê de Personalizados",
        "currency_id": "BRL",
        "transaction_amount": 77,
        "total_paid_amount": 77,
        "shipping_cost": 0,
        "account_money_amount": 0,
        "mercadopago_fee": 3.84,
        "net_received_amount": 73.16,
        "marketplace_fee": null,
        "coupon_id": null,
        "coupon_amount": null,
        "coupon_fee": null,
        "finance_fee": 0,
        "status": "approved",
        "status_detail": "accredited",
        "status_code": "00",
        "released": "no",
        "payment_type": "credit_card",
        "installments": 1,
        "installment_amount": null,
        "deferred_period": null,
        "cardholder": {
          "name": "Katia R R Rodrigues",
          "identification": {
            "type": "CPF",
            "number": "44274050106"
          }
        },
        "statement_descriptor": "MERCADOPAGO*",
        "transaction_order_id": null,
        "last_four_digits": "7686",
        "payment_method_id": "visa",
        "marketplace": "NONE",
        "tags": [
          "new"
        ],
        "refunds": [],
        "amount_refunded": 0,
        "notification_url": "https://api.awsli.com.br/pagador/meio-pagamento/mptransparente/retorno/176321/notificacao?referencia=166"
      }
    },
    {
      "collection": {
        "id": 1278240091,
        "site_id": "MLB",
        "date_created": "2015-08-19T21:54:38.000-04:00",
        "date_approved": "2015-08-19T21:58:26.000-04:00",
        "last_modified": "2015-08-20T04:46:23.000-04:00",
        "money_release_date": "2015-09-09T21:58:26.000-04:00",
        "operation_type": "regular_payment",
        "collector_id": 129324129,
        "sponsor_id": null,
        "payer": {
          "nickname": "OLJO8494226",
          "first_name": "Jordana",
          "last_name": "Oliveira",
          "phone": {
            "area_code": null,
            "number": "34 92409680",
            "extension": null
          },
          "email": "joor_louise@hotmail.com",
          "id": 186069720,
          "identification": {
            "type": null,
            "number": null
          }
        },
        "external_reference": "988588807",
        "merchant_order_id": null,
        "reason": "Topo Bolo Acrílico Espelhado Personalizado Casamento Noivado",
        "currency_id": "BRL",
        "transaction_amount": 61.99,
        "total_paid_amount": 76.47,
        "shipping_cost": 14.48,
        "account_money_amount": 0,
        "mercadopago_fee": 24.4,
        "net_received_amount": 52.07,
        "marketplace_fee": null,
        "coupon_id": null,
        "coupon_amount": null,
        "coupon_fee": null,
        "finance_fee": 0,
        "status": "approved",
        "status_detail": "accredited",
        "status_code": "0",
        "released": "no",
        "payment_type": "credit_card",
        "installments": 1,
        "installment_amount": null,
        "deferred_period": null,
        "cardholder": {
          "name": "Jordana S Oliveira",
          "identification": {
            "type": "CPF",
            "number": "03830601174"
          }
        },
        "statement_descriptor": "MERCADOPAGO",
        "transaction_order_id": null,
        "last_four_digits": "5593",
        "payment_method_id": "visa",
        "marketplace": "MELI",
        "tags": [
          "new"
        ],
        "refunds": [],
        "amount_refunded": 0,
        "notification_url": null
      }
    },
    {
      "collection": {
        "id": 1278173179,
        "site_id": "MLB",
        "date_created": "2015-08-19T18:31:10.000-04:00",
        "date_approved": "2015-08-20T15:38:43.000-04:00",
        "last_modified": "2015-08-20T15:38:43.000-04:00",
        "money_release_date": "2015-09-10T15:38:43.000-04:00",
        "operation_type": "regular_payment",
        "collector_id": 129324129,
        "sponsor_id": null,
        "payer": {
          "nickname": "MATHEUSSUZANA",
          "first_name": "SUZANA",
          "last_name": "MATHEUS",
          "phone": {
            "area_code": null,
            "number": "11947191844",
            "extension": null
          },
          "email": "suzy.daiane@hotmail.com",
          "id": 172432534,
          "identification": {
            "type": null,
            "number": null
          }
        },
        "external_reference": "988510510",
        "merchant_order_id": null,
        "reason": "Topo Bolo Acrílico Espelhado Personalizado Casamento Noivado",
        "currency_id": "BRL",
        "transaction_amount": 61.99,
        "total_paid_amount": 77.23,
        "shipping_cost": 15.24,
        "account_money_amount": 0,
        "mercadopago_fee": 15.24,
        "net_received_amount": 61.99,
        "marketplace_fee": null,
        "coupon_id": null,
        "coupon_amount": 0,
        "coupon_fee": 0,
        "finance_fee": 0,
        "status": "approved",
        "status_detail": "accredited",
        "status_code": null,
        "released": "no",
        "payment_type": "ticket",
        "installments": null,
        "installment_amount": null,
        "deferred_period": null,
        "cardholder": {
          "name": null,
          "identification": {
            "type": null,
            "number": null
          }
        },
        "statement_descriptor": null,
        "last_four_digits": null,
        "payment_method_id": "bolbradesco",
        "marketplace": "MELI",
        "tags": [],
        "refunds": [],
        "amount_refunded": 0,
        "notification_url": null
      }
    }
  ]
}"""


class MPTransparenteAtualizaTransacoes(unittest.TestCase):
    @mock.patch('pagador_mercadopago_transparente.servicos.AtualizaTransacoes.obter_conexao')
    def test_monta_consulta_corretamente(self, obter_con_mock):
        atualizador = servicos.AtualizaTransacoes(1234, dados={'data_inicial': '2015-08-22', 'data_final': '2015-08-23'})
        atualizador.consulta_transacoes()
        obter_con_mock.return_value.get.assert_called_with('https://api.mercadopago.com/collections/search', dados={'sort': 'date_created', 'begin_date': '2015-08-22T00:00:00Z', 'end_date': '2015-08-23T23:59:59Z', 'range': 'date_created', 'limit': 1000, 'criteria': 'desc'})

    @mock.patch('pagador_mercadopago_transparente.servicos.AtualizaTransacoes.obter_conexao', mock.MagicMock)
    def test_resultado_com_erro(self):
        atualizador = servicos.AtualizaTransacoes(1234, dados={'data_inicial': '2015-08-22', 'data_final': '2015-08-23'})
        atualizador.resposta = mock.MagicMock(sucesso=False, nao_autorizado=False, nao_autenticado=False, conteudo={'message': 'invalid_token', 'cause': [0], 'error': 'not_found','status': 401})
        atualizador.analisa_resultado_transacoes()
        atualizador.dados_pedido.should.be.empty
        atualizador.erros.should.be.equal({'cause': [0], 'error': 'not_found', 'message': 'invalid_token', 'status': 401})

    @mock.patch('pagador_mercadopago_transparente.servicos.AtualizaTransacoes.obter_conexao', mock.MagicMock)
    def test_resultado_com_erro(self):
        atualizador = servicos.AtualizaTransacoes(1234, dados={'data_inicial': '2015-08-22', 'data_final': '2015-08-23'})
        atualizador.resposta = mock.MagicMock(sucesso=False, nao_autorizado=False, nao_autenticado=False, conteudo={'message': 'invalid_token', 'cause': [0], 'error': 'not_found','status': 401})
        atualizador.analisa_resultado_transacoes()
        atualizador.dados_pedido.should.be.empty
        atualizador.erros.should.be.equal({'cause': [0], 'error': 'not_found', 'message': 'invalid_token', 'status': 401})

    @mock.patch('pagador_mercadopago_transparente.servicos.AtualizaTransacoes.obter_conexao', mock.MagicMock)
    def test_resultado_com_dados_de_pedido(self):
        atualizador = servicos.AtualizaTransacoes(1234, dados={'data_inicial': '2015-08-22', 'data_final': '2015-08-23'})
        conteudo = json.loads(RESULTADO_TRANSACOES)
        atualizador.resposta = mock.MagicMock(sucesso=True, conteudo=conteudo)
        atualizador.analisa_resultado_transacoes()
        atualizador.dados_pedido.should.be.equal([{'situacao_pedido': 4, 'pedido_numero': u'168'}, {'situacao_pedido': 4, 'pedido_numero': u'166'}])
