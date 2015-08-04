# -*- coding: utf-8 -*-
import unittest
from decimal import Decimal
from datetime import datetime

import mock

from pagador_mercadopago_transparente import entidades


def parametros_mock(par1, par2):
    return {'public_key': 'public_key'}


class MPTransparenteConfiguracaoMeioPagamento(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MPTransparenteConfiguracaoMeioPagamento, self).__init__(*args, **kwargs)
        self.campos = ['usuario', 'token', 'token_expiracao', 'codigo_autorizacao', 'ativo', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'maximo_parcelas', 'parcelas_sem_juros']
        self.codigo_gateway = 14

    @mock.patch('pagador_mercadopago_transparente.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.entidades.entidades.ParametrosDeContrato.obter_para', parametros_mock)
    def test_deve_ter_os_campos_especificos_na_classe(self):
        entidades.ConfiguracaoMeioPagamento(234).campos.should.be.equal(self.campos)

    @mock.patch('pagador_mercadopago_transparente.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.entidades.entidades.ParametrosDeContrato.obter_para', parametros_mock)
    def test_deve_ter_codigo_gateway(self):
        entidades.ConfiguracaoMeioPagamento(234).codigo_gateway.should.be.equal(self.codigo_gateway)

    @mock.patch('pagador_mercadopago_transparente.entidades.entidades.ParametrosDeContrato.obter_para', parametros_mock)
    @mock.patch('pagador_mercadopago_transparente.entidades.ConfiguracaoMeioPagamento.preencher_gateway', autospec=True)
    def test_deve_preencher_gateway_na_inicializacao(self, preencher_mock):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        preencher_mock.assert_called_with(configuracao, self.codigo_gateway, self.campos)

    @mock.patch('pagador_mercadopago_transparente.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.entidades.entidades.ParametrosDeContrato.obter_para', parametros_mock)
    def test_deve_definir_formulario_na_inicializacao(self):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.formulario.should.be.a('pagador_mercadopago_transparente.cadastro.FormularioMercadoPagoTransparente')

    @mock.patch('pagador_mercadopago_transparente.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    @mock.patch('pagador_mercadopago_transparente.entidades.entidades.ParametrosDeContrato.obter_para', parametros_mock)
    def test_deve_ser_aplicacao(self):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.eh_aplicacao.should.be.truthy


class MPTransparenteMontandoMalote(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(MPTransparenteMontandoMalote, self).__init__(methodName)
        self.pedido = mock.MagicMock(
            numero=123,
            valor_total=Decimal('14.00'),
            cliente={
                'nome': 'Cliente Teste',
                'email': 'email@cliente.com',
                'data_criacao': datetime(2013, 5, 1, 10, 20)
            },
            cliente_documento='12345678901',
            cliente_telefone=('11', '23456789'),
            endereco_cliente={
                'endereco': 'Rua Teste',
                'numero': 123,
                'complemento': 'Apt 101',
                'bairro': 'Teste',
                'cep': '10234000',
                'tipo': 'CPF'
            },
            itens=[
                entidades.entidades.ItemDePedido(nome='Produto 1', sku='PROD01', quantidade=1, preco_venda=Decimal('40.00')),
                entidades.entidades.ItemDePedido(nome='Produto 2', sku='PROD02', quantidade=1, preco_venda=Decimal('50.00')),
            ],
            conteudo_json={
                'mptransparente': {
                    'nome_loja': 'Loja ZAS',
                    'bandeira': 'visa',
                    'cartao': 'zas'
                }
            }
        )

    def test_malote_deve_ter_propriedades(self):
        entidades.Malote('configuracao').to_dict().should.be.equal({'amount': 0, 'card_token_id': None, 'currency_id': 'BRL', 'customer': None, 'external_reference': None, 'installments': 1, 'items': None, 'notification_url': None, 'payer_email': None, 'payment_method_id': None, 'reason': None, 'shipments': None})

    def test_deve_montar_conteudo_sem_parcelas(self):
        malote = entidades.Malote(mock.MagicMock(loja_id=8))
        dados = {'passo': 'pre', 'cartao_hash': 'cartao-hash', 'cartao_parcelas': 1}
        parametros = {}
        malote.monta_conteudo(self.pedido, parametros, dados)
        malote.to_dict().should.be.equal({'amount': 14.0, 'card_token_id': 'zas', 'currency_id': 'BRL', 'customer': {'address': {'street_name': 'Rua Teste', 'street_number': 123, 'zip_code': '10234000'}, 'email': 'email@cliente.com', 'identification': {'number': '12345678901', 'type': 'CNPJ'}, 'phone': {'area_code': '11', 'number': '23456789'}, 'registration_date': '2013-05-01T10:20:00'}, 'external_reference': 123, 'installments': 1, 'items': [{'category_id': 'others', 'description': None, 'id': 'PROD01', 'picture_url': '', 'quantity': 1.0, 'title': 'Produto 1', 'unit_price': 40.0}, {'category_id': 'others', 'description': None, 'id': 'PROD02', 'picture_url': '', 'quantity': 1.0, 'title': 'Produto 2', 'unit_price': 50.0}], 'notification_url': 'http://localhost:5000/pagador/meio-pagamento/mptransparente/retorno/8/notificacao?referencia=123', 'payer_email': 'email@cliente.com', 'payment_method_id': 'visa', 'reason': 'Pagamento do pedido 123 na Loja Loja ZAS', 'shipments': {'cost': None, 'receiver_address': {'floor': None}}})

    def test_deve_montar_conteudo_com_parcelas_sem_juros(self):
        malote = entidades.Malote(mock.MagicMock(loja_id=8))
        dados = {'passo': 'pre', 'cartao_hash': 'cartao-hash', 'cartao_parcelas': 3, 'cartao_parcelas_sem_juros': 'true'}
        parametros = {}
        malote.monta_conteudo(self.pedido, parametros, dados)
        malote.to_dict().should.be.equal({'amount': 14.0, 'card_token_id': 'zas', 'currency_id': 'BRL', 'customer': {'address': {'street_name': 'Rua Teste', 'street_number': 123, 'zip_code': '10234000'}, 'email': 'email@cliente.com', 'identification': {'number': '12345678901', 'type': 'CNPJ'}, 'phone': {'area_code': '11', 'number': '23456789'}, 'registration_date': '2013-05-01T10:20:00'}, 'external_reference': 123, 'installments': 1, 'items': [{'category_id': 'others', 'description': None, 'id': 'PROD01', 'picture_url': '', 'quantity': 1.0, 'title': 'Produto 1', 'unit_price': 40.0}, {'category_id': 'others', 'description': None, 'id': 'PROD02', 'picture_url': '', 'quantity': 1.0, 'title': 'Produto 2', 'unit_price': 50.0}], 'notification_url': 'http://localhost:5000/pagador/meio-pagamento/mptransparente/retorno/8/notificacao?referencia=123', 'payer_email': 'email@cliente.com', 'payment_method_id': 'visa', 'reason': 'Pagamento do pedido 123 na Loja Loja ZAS', 'shipments': {'cost': None, 'receiver_address': {'floor': None}}})

    def test_deve_montar_conteudo_com_parcelas_com_juros(self):
        malote = entidades.Malote(mock.MagicMock(loja_id=8))
        dados = {'passo': 'pre', 'cartao_hash': 'cartao-hash', 'customer': {'address': {'complementary': 'Apt 101', 'neighborhood': 'Teste', 'street': 'Rua Teste', 'street_number': 123, 'zipcode': '10234000'}, 'document_number': '12345678901', 'email': 'email@cliente.com', 'name': 'Cliente Teste', 'phone': {'ddd': '11', 'number': '23456789'}}, 'cartao_parcelas': 3, 'cartao_parcelas_sem_juros': 'false', 'metadata': {'carrinho': [{'nome': 'Produto 1', 'preco_venda': 40.0, 'quantidade': 1, 'sku': 'PROD01'}, {'nome': 'Produto 2', 'preco_venda': 50.0, 'quantidade': 1, 'sku': 'PROD02'}], 'pedido_numero': 123}}
        parametros = {}
        malote.monta_conteudo(self.pedido, parametros, dados)
        malote.to_dict().should.be.equal({'amount': 14.0, 'card_token_id': 'zas', 'currency_id': 'BRL', 'customer': {'address': {'street_name': 'Rua Teste', 'street_number': 123, 'zip_code': '10234000'}, 'email': 'email@cliente.com', 'identification': {'number': '12345678901', 'type': 'CNPJ'}, 'phone': {'area_code': '11', 'number': '23456789'}, 'registration_date': '2013-05-01T10:20:00'}, 'external_reference': 123, 'installments': 1, 'items': [{'category_id': 'others', 'description': None, 'id': 'PROD01', 'picture_url': '', 'quantity': 1.0, 'title': 'Produto 1', 'unit_price': 40.0}, {'category_id': 'others', 'description': None, 'id': 'PROD02', 'picture_url': '', 'quantity': 1.0, 'title': 'Produto 2', 'unit_price': 50.0}], 'notification_url': 'http://localhost:5000/pagador/meio-pagamento/mptransparente/retorno/8/notificacao?referencia=123', 'payer_email': 'email@cliente.com', 'payment_method_id': 'visa', 'reason': 'Pagamento do pedido 123 na Loja Loja ZAS', 'shipments': {'cost': None, 'receiver_address': {'floor': None}}})
