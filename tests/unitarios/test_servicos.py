# -*- coding: utf-8 -*-
import unittest
import mock
from pagador_mercadopago_transparente import servicos


class MPTransparenteCredenciais(unittest.TestCase):
    def test_deve_definir_propriedades(self):
        credenciador = servicos.Credenciador(configuracao=mock.MagicMock())
        credenciador.tipo.should.be.equal(credenciador.TipoAutenticacao.form_urlencode)
        credenciador.chave.should.be.equal('api_key')

    def test_deve_retornar_credencial_baseado_no_usuario(self):
        configuracao = mock.MagicMock(token='api-key')
        credenciador = servicos.Credenciador(configuracao=configuracao)
        credenciador.obter_credenciais().should.be.equal('api-key')


class MPTransparenteSituacoesPagamento(unittest.TestCase):
    def test_deve_retornar_pago_para_paid(self):
        servicos.SituacoesDePagamento.do_tipo('paid').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO)

    def test_deve_retornar_cancelado_para_refused(self):
        servicos.SituacoesDePagamento.do_tipo('refused').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO)

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
        obter_mock.return_value = 'conexao'
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.conexao.should.be.equal('conexao')
        obter_mock.assert_called_with(formato_envio='application/x-www-form-urlencoded')

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
        entregador.envia_pagamento()
        entregador.conexao.post.assert_called_with(entregador.url, {'zas': 'malote-como-dicionario'})

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_pre_envio_nao_tem_parcelas_sem_cartao_parcelas_em_dados(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.tem_parcelas.should.be.falsy

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_pre_envio_nao_tem_parcelas_com_cartao_parcelas_igual_a_um(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre', 'cartao_parcelas': 1})

        entregador.tem_parcelas.should.be.falsy

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_pre_envio_tem_parcelas_comm_cartao_parcelas_maior_que_um(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre', 'cartao_parcelas': 3})
        entregador.tem_parcelas.should.be.truthy

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_processar_dados_de_pagamento_define_dados_pagamento(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.pedido = mock.MagicMock(valor_total=15.70)
        entregador.servico = mock.MagicMock()
        entregador.resposta = mock.MagicMock(sucesso=True, requisicao_invalida=False, conteudo={'id': 'identificacao-id', 'tid': 'transacao-id', 'card_brand': 'visa'})
        entregador.processa_dados_pagamento()
        entregador.dados_pagamento.should.be.equal({'transacao_id': 'transacao-id', 'valor_pago': 15.7})

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_processar_dados_de_pagamento_dispara_erro_se_invalido(self):
        entregador = servicos.EntregaPagamento(8, dados={'passo': 'pre'})
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = {'card_hash': None, 'capture': 'false', 'amount': 2900, 'installments': 1, 'payment_method': 'credit_card'}
        entregador.pedido = mock.MagicMock(numero=1234)
        entregador.resposta = mock.MagicMock(sucesso=False, requisicao_invalida=True, conteudo={u'url': u'/transactions', u'errors': [{u'message': u'Nome do portador do cartão está faltando', u'type': u'invalid_parameter', u'parameter_name': u'card_holder_name'}, {u'message': u'Data de expiração do cartão está faltando', u'type': u'invalid_parameter', u'parameter_name': u'card_expiration_date'}], u'method': u'post'})
        entregador.processa_dados_pagamento.when.called_with().should.throw(
            entregador.EnvioNaoRealizado,
            '\n'.join([
                'Pedido 1234 na Loja Id 8',
                u'Dados inválidos enviados ao MercadoPago:',
                u'\tcard_holder_name: Nome do portador do cartão está faltando',
                u'\tcard_expiration_date: Data de expiração do cartão está faltando',
                'Tentou enviar com os seguintes dados:',
                "{'card_hash': None, 'capture': 'false', 'amount': 2900, 'installments': 1, 'payment_method': 'credit_card'}"
            ])
        )

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_processar_dados_de_pagamento_dispara_erro_sem_ser_parameter(self):
        entregador = servicos.EntregaPagamento(8, dados={'passo': 'pre'})
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = {'card_hash': None, 'capture': 'false', 'amount': 2900, 'installments': 1, 'payment_method': 'credit_card'}
        entregador.pedido = mock.MagicMock(numero=1234)
        entregador.resposta = mock.MagicMock(sucesso=False, requisicao_invalida=True, conteudo={u'url': u'/transactions', u'errors': [{u'message': u'Nome do portador do cartão está faltando', u'type': u'whatever'}, {u'message': u'Data de expiração do cartão está faltando', u'type': u'whatever'}], u'method': u'post'})
        entregador.processa_dados_pagamento.when.called_with().should.throw(
            entregador.EnvioNaoRealizado,
            '\n'.join([
                'Pedido 1234 na Loja Id 8',
                u'Dados inválidos enviados ao MercadoPago:',
                u'\tNome do portador do cartão está faltando',
                u'\tData de expiração do cartão está faltando',
                'Tentou enviar com os seguintes dados:',
                "{'card_hash': None, 'capture': 'false', 'amount': 2900, 'installments': 1, 'payment_method': 'credit_card'}"
            ])
        )

    @mock.patch('pagador_mercadopago_transparente.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_processar_dados_de_pagamento_define_identificador_id(self):
        entregador = servicos.EntregaPagamento(1234, dados={'passo': 'pre'})
        entregador.configuracao = mock.MagicMock(aplicacao='test')
        entregador.pedido = mock.MagicMock(valor_total=15.70)
        entregador.servico = mock.MagicMock()
        entregador.resposta = mock.MagicMock(sucesso=True, requisicao_invalida=False, conteudo={'id': 'identificacao-id', 'tid': 'transacao-id', 'card_brand': 'visa'})
        entregador.processa_dados_pagamento()
        entregador.identificacao_pagamento.should.be.equal('identificacao-id')
