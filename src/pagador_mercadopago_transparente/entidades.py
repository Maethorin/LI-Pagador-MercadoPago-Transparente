# -*- coding: utf-8 -*-
from pagador import settings, entidades
from pagador_mercadopago_transparente import cadastro

CODIGO_GATEWAY = 14
GATEWAY = 'mptransparente'


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
        self.notification_url = None

    def monta_conteudo(self, pedido, parametros_contrato=None, dados=None):
        self.amount = self.formatador.formata_decimal(pedido.valor_total, como_float=True)
        dados_pagamento = pedido.conteudo_json.get(GATEWAY, {})
        if not dados_pagamento:
            raise self.DadosInvalidos('O pedido não foi montado corretamente no checkout.')
        self.reason = 'Pagamento do pedido {} na Loja {}'.format(pedido.numero, dados_pagamento['nome_loja'])
        self.installments = dados_pagamento.get('parcelas', 1)
        self.payment_method_id = dados_pagamento['bandeira']
        self.card_token_id = dados_pagamento['cartao']
        self.payer_email = pedido.cliente['email']
        self.external_reference = pedido.numero
        notification_url = settings.NOTIFICACAO_URL.format(GATEWAY, self.configuracao.loja_id)
        self.notification_url = '{}/notificacao?referencia={}'.format(notification_url, pedido.numero)


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):

    def __init__(self, loja_id, codigo_pagamento=None, eh_listagem=False):
        self.campos = ['usuario', 'token', 'token_expiracao', 'codigo_autorizacao', 'ativo', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'maximo_parcelas', 'parcelas_sem_juros']
        self.codigo_gateway = CODIGO_GATEWAY
        self.eh_gateway = True
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento, eh_listagem=eh_listagem)
        self.src_js_sdk = 'https://secure.mlstatic.com/org-img/checkout/custom/1.0/checkout.js'
        parametros = entidades.ParametrosDeContrato(loja_id).obter_para(self.extensao)
        self.public_key = parametros['public_key']
        self.parcelas_por_bandeira = {
            'visa': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'mastercard': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'hipercard': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'diners_club_international': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'elo': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'amex': [1, 2, 3, 4, 5, 6, 9, 10, 12, 15],
            'melicard': [1, 2, 3, 4, 5, 6, 9, 10, 12, 15, 18, 24]
        }
        self.mensagens_erro_geracao_cartao = {
            '106': {'mensagem': u'Você não pode fazer pagamentos para usuários em outros países.', 'referencia': 'geral'},
            '109': {'mensagem': u'O seu cartão não aceita as parcelas selecionadas.', 'referencia': 'cartao'},
            '126': {'mensagem': u'Não foi possível efetuar o pagamento com esse cartão.', 'referencia': 'cartao'},
            '129': {'mensagem': u'O cartão informado não suporta o valor da compra.', 'referencia': 'geral'},
            '145': {'mensagem': u'Não foi possível processar o pagamento.', 'referencia': 'geral'},
            '150': {'mensagem': u'Você não pode realizar pagamentos por essa forma de pagamento. Por favor, escolha outra.', 'referencia': 'geral'},
            '151': {'mensagem': u'Você não pode realizar pagamentos por essa forma de pagamento. Por favor, escolha outra.', 'referencia': 'geral'},
            '160': {'mensagem': u'Não foi possível processar o pagamento.', 'referencia': 'geral'},
            '204': {'mensagem': u'A operadora do cartão informado não está disponível no momento.', 'referencia': 'geral'},
            '205': {'mensagem': u'Digite o seu número de cartão.', 'referencia': 'cartao'},
            '208': {'mensagem': u'Escolha um mês para a data de expiração.', 'referencia': 'mes'},
            '209': {'mensagem': u'Escolha um ano para a data de expiração.', 'referencia': 'ano'},
            '221': {'mensagem': u'Digite o seu nome como está impresso no cartão.', 'referencia': 'nome'},
            '224': {'mensagem': u'Digite o código de segurança do seu cartão.', 'referencia': 'cvv'},
            'E301': {'mensagem': u'Número do cartão inválido.', 'referencia': 'cartao'},
            'E302': {'mensagem': u'Código de segurança inválido.', 'referencia': 'cvv'},
            '316': {'mensagem': u'Titular do cartão inválido.', 'referencia': 'nome'},
            '322': {'mensagem': u'Você deve estar logado para realizar compras.', 'referencia': 'geral'},
            '324': {'mensagem': u'Você deve estar logado para realizar compras.', 'referencia': 'geral'},
            '325': {'mensagem': u'Mês da data de expiração inválido.', 'referencia': 'mes'},
            '326': {'mensagem': u'Ano da data de expiração inválido.', 'referencia': 'ano'},
            '801': {'mensagem': u'Você já enviou um pagamento semelhante no mesmo minuto. Tente novamente em alguns minutos.', 'referencia': 'geral'}
        }
        if not self.eh_listagem:
            self.formulario = cadastro.FormularioMercadoPagoTransparente()
            self.eh_aplicacao = True

    @property
    def instalado(self):
        return (
            self.usuario is not None and
            self.token is not None and
            self.codigo_autorizacao is not None
        )
