# -*- coding: utf-8 -*-
from pagador import settings, entidades
from pagador_mercadopago_transparente import cadastro

CODIGO_GATEWAY = 14


class PassosDeEnvio(object):
    pre = 'pre'
    captura = 'captura'


class Cliente(entidades.BaseParaPropriedade):
    _atributos = ['name', 'document_number', 'email', 'address', 'phone']


class Endereco(entidades.BaseParaPropriedade):
    _atributos = ['street', 'neighborhood', 'zipcode', 'street_number', 'complementary']


class Telefone(entidades.BaseParaPropriedade):
    _atributos = ['ddd', 'number']


class Malote(entidades.Malote):
    def __init__(self, configuracao):
        super(Malote, self).__init__(configuracao)
        self.amount = 0
        self.reason = None
        self.currency_id = 'BRL'
        self.installments = 1
        self.payment_method_id = None
        self.card_token_id = None
        self.payer_email = None
        self.external_reference = None

    def monta_conteudo(self, pedido, parametros_contrato=None, dados=None):
        self.amount = self.formatador.formata_decimal(pedido.valor_total, em_centavos=True)
        self.reason = 'Pagamento do pedido {} na Loja {}'.format(pedido.numero, pedido.conteudo_json['mptransparente']['nome_loja'])
        self.installments = pedido.conteudo_json.get('parcelas', 1)
        self.payment_method_id = pedido.conteudo_json['mptransparente']['bandeira']
        self.card_token_id = pedido.conteudo_json['mptransparente']['cartao_token']
        self.payer_email = pedido.cliente['email']
        self.external_reference = pedido.numero


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):

    def __init__(self, loja_id, codigo_pagamento=None, eh_listagem=False):
        self.campos = ['usuario', 'token', 'token_expiracao', 'codigo_autorizacao', 'assinatura', 'ativo', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'maximo_parcelas', 'parcelas_sem_juros']
        self.codigo_gateway = CODIGO_GATEWAY
        self.eh_gateway = True
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento, eh_listagem=eh_listagem)
        self.src_js_sdk = 'https://secure.mlstatic.com/org-img/checkout/custom/1.0/checkout.js'
        if not self.eh_listagem:
            self.formulario = cadastro.FormularioMercadoPagoTransparente()
            self.eh_aplicacao = True

    @property
    def configurado(self):
        return (
            self.usuario is not None and
            self.token is not None and
            self.codigo_autorizacao is not None
        )
