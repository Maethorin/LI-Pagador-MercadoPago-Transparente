# -*- coding: utf-8 -*-
from pagador import configuracoes, entidades
from pagador_mercadopago_transparente import cadastro

CODIGO_GATEWAY = 14
GATEWAY = 'mptransparente'


class PassosDeEnvio(object):
    pre = 'pre'
    captura = 'captura'


class ClientePagador(entidades.BaseParaPropriedade):
    _atributos = ['email', 'identification']


class Cliente(entidades.BaseParaPropriedade):
    _atributos = ['first_name', 'last_name', 'phone', 'address', 'registration_date']


class Endereco(entidades.BaseParaPropriedade):
    _atributos = ['street_name', 'street_number', 'zip_code']


class Telefone(entidades.BaseParaPropriedade):
    _atributos = ['area_code', 'number']


class Identificacao(entidades.BaseParaPropriedade):
    _atributos = ['type', 'number']


class InformacoesAdicionais(entidades.BaseParaPropriedade):
    _atributos = ['items', 'payer', 'shipments']


class Item(entidades.BaseParaPropriedade):
    _atributos = ['id', 'title', 'description', 'picture_url', 'category_id', 'quantity', 'unit_price']


class DadosEntrega(entidades.BaseParaPropriedade):
    _atributos = ['receiver_address']


class EnderecoEntrega(entidades.BaseParaPropriedade):
    _atributos = ['street_name', 'street_number', 'zip_code', 'floor', 'apartment']


class Malote(entidades.Malote):
    def __init__(self, configuracao):
        super(Malote, self).__init__(configuracao)
        self.transaction_amount = 0
        self.external_reference = None
        self.description = None
        self.payer = ClientePagador()
        self.additional_info = InformacoesAdicionais()
        self.installments = 1
        self.payment_method_id = None
        self.token = None
        self.binary_mode = False
        self.statement_descriptor = None
        self.notification_url = None
        self._pedido = None

    def monta_conteudo(self, pedido, parametros_contrato=None, dados=None):
        dados_pagamento = pedido.conteudo_json.get(GATEWAY, {})
        if not dados_pagamento:
            raise self.DadosInvalidos('O pedido não foi montado corretamente no checkout.')
        self._pedido = pedido
        self.transaction_amount = self.formatador.formata_decimal(pedido.valor_total, como_float=True)
        self.external_reference = pedido.numero
        self.description = 'Pagamento do pedido {} na Loja {}'.format(pedido.numero, dados_pagamento['nome_loja'].encode("utf8"))

        self.payer.email = pedido.cliente['email']
        self.payer.identification = self._cliente_documento

        self.additional_info.items = self._monta_items()
        self.additional_info.payer = Cliente(
            first_name=self.formatador.trata_unicode_com_limite(self._pedido.cliente_primeiro_nome),
            last_name=self.formatador.trata_unicode_com_limite(self._pedido.cliente_ultimo_nome),
            phone=self._cliente_telefone,
            address=Endereco(
                zip_code=self._pedido.endereco_cliente['cep'],
                street_name=self.formatador.trata_unicode_com_limite(self._pedido.endereco_cliente['endereco']),
                street_number=self._pedido.endereco_cliente['numero']
            ),
            registration_date=self.formatador.formata_data(self._pedido.cliente['data_criacao'], iso=True)
        )
        self.additional_info.shipments = DadosEntrega(
            receiver_address=EnderecoEntrega(
                zip_code=self._pedido.endereco_entrega['cep'],
                street_name=self.formatador.trata_unicode_com_limite(self._pedido.endereco_entrega['endereco']),
                street_number=self._pedido.endereco_entrega['numero'],
                apartment=self.formatador.trata_unicode_com_limite(self._pedido.endereco_entrega['complemento'])
            )
        )

        self.installments = dados_pagamento.get('parcelas', 1)
        self.payment_method_id = dados_pagamento['bandeira']
        self.token = dados_pagamento['cartao']
        notification_url = configuracoes.NOTIFICACAO_URL.format(GATEWAY, self.configuracao.loja_id)
        self.notification_url = '{}/notificacao?referencia={}'.format(notification_url, pedido.numero)
        self.statement_descriptor = self.configuracao.informacao_complementar
        try:
            sponsor_id = int(parametros_contrato['sponsor_id'])
        except (KeyError, ValueError):
            sponsor_id = None
        if sponsor_id:
            setattr(self, 'sponsor_id', sponsor_id)

    @property
    def _cliente_telefone(self):
        telefone = self._pedido.cliente_telefone
        return Telefone(area_code=telefone[0], number=telefone[1])

    @property
    def _cliente_documento(self):
        tipo = 'CPF' if self._pedido.endereco_cliente['tipo'] == "PF" else 'CNPJ'
        return Identificacao(type=tipo, number=self._pedido.cliente_documento)

    def _monta_items(self):
        items = [
            Item(
                id=self.formatador.trata_unicode_com_limite(item.sku),
                title=self.formatador.trata_unicode_com_limite(item.nome),
                unit_price=self.formatador.formata_decimal(item.preco_venda, como_float=True),
                quantity=self.formatador.formata_decimal(item.quantidade, como_float=True),
                category_id='others',
                picture_url=''
            )
            for item in self._pedido.itens
        ]
        return items


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):
    modos_pagamento_aceitos = {
        'cartoes': ['visa', 'mastercard', 'hipercard', 'amex', 'diners', 'elo'],
    }

    def __init__(self, loja_id, codigo_pagamento=None, eh_listagem=False):
        self.campos = ['usuario', 'token', 'token_expiracao', 'codigo_autorizacao', 'ativo', 'informacao_complementar', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'maximo_parcelas', 'parcelas_sem_juros']
        self.codigo_gateway = CODIGO_GATEWAY
        self.eh_gateway = True
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento, eh_listagem=eh_listagem)
        self.exige_https = True
        self.src_js_sdk = 'https://secure.mlstatic.com/sdk/javascript/v1/mercadopago.js'
        parametros = entidades.ParametrosDeContrato(loja_id).obter_para(self.extensao)
        self.public_key = parametros['public_key']
        self.parcelas_por_bandeira = {
            'visa': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'master': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'hipercard': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'diners_club_international': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'diners_club_carte_blanche': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'discover': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'elo': [1, 2, 3, 4, 5, 6, 9, 10, 12],
            'amex': [1, 2, 3, 4, 5, 6, 9, 10, 12, 15],
            'melicard': [1, 2, 3, 4, 5, 6, 9, 10, 12, 15, 18, 24]
        }
        self.mensagens_erro_geracao_cartao = {
            '106': {'mensagem': u'Você não pode fazer pagamentos para usuários em outros países.', 'referencia': 'geral'},
            '109': {'mensagem': u'O seu cartão não aceita as parcelas selecionadas.', 'referencia': 'cartao'},
            '132': {'mensagem': u'Não é possível efetuar pagamento desse valor com esse cartão.', 'referencia': 'cartao'},
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
            '214': {'mensagem': u'Você precisa estar logado ou preencher o cadastro de novo cliente para finalizar.', 'referencia': 'geral'},
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
        _formulario = cadastro.FormularioMercadoPagoTransparente()
        self._parcelas = _formulario.obter_parcelas_disponiveis()
        if not self.eh_listagem:
            self.formulario = _formulario
            self.eh_aplicacao = True

    @property
    def instalado(self):
        return (
            self.usuario is not None and
            self.token is not None and
            self.codigo_autorizacao is not None
        )
