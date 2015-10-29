# -*- coding: utf-8 -*-
from time import sleep
from urllib import urlencode
from datetime import datetime, timedelta

from li_common.comunicacao import requisicao

from pagador import configuracoes, servicos

TEMPO_MAXIMO_ESPERA_NOTIFICACAO = 30
GATEWAY = 'mptransparente'
CODIGO_GATEWAY = 14
MENSAGEM_ERRO_PADRAO = u'O pagamento pelo cartão informado não foi processado. Por favor, tente outra forma de pagamento.'

URL_API_BASE = 'https://api.mercadopago.com'


class TipoToken(object):
    authorization_code = 'authorization_code'
    refresh_token = 'refresh_token'


class InstalaMeioDePagamento(servicos.InstalaMeioDePagamento):
    campos = ['usuario', 'token', 'token_expiracao', 'codigo_autorizacao']

    def __init__(self, loja_id, dados):
        super(InstalaMeioDePagamento, self).__init__(loja_id, dados)
        parametros = self.cria_entidade_pagador('ParametrosDeContrato', loja_id=loja_id).obter_para('mptransparente')
        self.client_id = parametros['client_id']
        self.client_access_token = parametros['client_access_token']
        headers = {
            'Accept': 'application/json',
        }
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.form_urlencode, formato_resposta=requisicao.Formato.json, headers=headers)

    def montar_url_autorizacao(self):
        try:
            parametros_redirect = urlencode({'next_url': self.dados['next_url'], 'fase_atual': '2'})
        except KeyError:
            raise self.InstalacaoNaoFinalizada(u'Você precisa informar a url de redirecionamento na volta do MercadoPago na chave next_url do parâmetro dados.')
        dados = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': '{}?{}'.format(self.instalar_redirect_url, parametros_redirect)
        }
        return 'http://auth.mercadopago.com.br/authorization?{}'.format(urlencode(dados))

    @property
    def instalar_redirect_url(self):
        return configuracoes.INSTALAR_REDIRECT_URL.format(self.loja_id, 'mptransparente').replace('http://', 'https://')

    @property
    def _dados_instalacao(self):
        try:
            parametros_redirect = urlencode({'next_url': self.dados['next_url'], 'fase_atual': '2'})
        except KeyError:
            raise self.InstalacaoNaoFinalizada(u'Você precisa informar a url de redirecionamento na volta do MercadoPago na chave next_url do parâmetro dados.')
        return {
            'code': self.dados['code'],
            'grant_type': TipoToken.authorization_code,
            'client_secret': self.client_access_token,
            'redirect_uri': '{}?{}'.format(self.instalar_redirect_url, parametros_redirect)
        }

    @property
    def _dados_atualizacao(self):
        return {
            'refresh_token': self.dados['codigo_autorizacao'],
            'grant_type': TipoToken.refresh_token,
            'client_secret': self.client_access_token,
        }

    def obter_dados(self):
        url = '{}/oauth/token'.format(URL_API_BASE)
        tipo = self.dados.get('tipo', 'instalar')
        if self.dados.get('error', '') == 'access-denied':
            raise self.InstalacaoNaoFinalizada(u'A autorização foi cancelada no MercadoPago.')
        if tipo == 'instalar':
            dados = self._dados_instalacao
        else:
            dados = self._dados_atualizacao
        resposta = self.conexao.post(url, dados)
        if resposta.sucesso:
            resultado = {
                'token': resposta.conteudo['access_token'],
                'token_expiracao': datetime.utcnow() + timedelta(seconds=resposta.conteudo['expires_in']),
                'codigo_autorizacao': resposta.conteudo['refresh_token']
            }
            if tipo == 'instalar':
                resultado['usuario'] = resposta.conteudo['user_id']
            return resultado
        raise self.InstalacaoNaoFinalizada(u'Erro ao entrar em contato com o MercadoPago. Código: {}, Resposta: {}'.format(resposta.status_code, resposta.conteudo))

    def desinstalar(self, dados):
        url_base = 'https://api.mercadolibre.com/users/{}/applications/{}?access_token={}'
        url = url_base.format(dados['usuario'], self.client_id, dados['token'])
        resposta = self.conexao.delete(url)
        if resposta.sucesso:
            return u'Aplicação removida com sucesso'
        return u'Desinstalação foi feita com sucesso, mas a aplicação não foi removida do MercadoPago. Você precisará <a href="https://www.mercadopago.com/mlb/account/security/applications/connections" _target="blank">remover manualmente</a>.'


class Credenciador(servicos.Credenciador):
    def __init__(self, tipo=None, configuracao=None):
        super(Credenciador, self).__init__(tipo, configuracao)
        self.tipo = self.TipoAutenticacao.query_string
        self.access_token = None
        self.refresh_token = None
        self.token_expiracao = None
        self.atualiza_credenciais()

    def atualiza_credenciais(self):
        self.access_token = getattr(self.configuracao, 'token', '')
        self.refresh_token = getattr(self.configuracao, 'codigo_autorizacao', '')
        self.token_expiracao = getattr(self.configuracao, 'token_expiracao', datetime.utcnow())

    def obter_credenciais(self):
        return self.access_token


MENSAGENS_RETORNO = {
    '106': u'Você não pode fazer pagamentos para usuários em outros países.',
    '109': u'O seu cartão não aceita as parcelas selecionadas.',
    '126': u'Não foi possível efetuar o pagamento com esse cartão.',
    '129': u'O cartão informado não suporta o valor da compra.',
    '132': u'Não é possível efetuar pagamento desse valor com esse cartão.',
    '145': u'Não foi possível processar o pagamento com o e-mail cadastrado.',
    '150': u'Você não pode realizar pagamentos por essa forma de pagamento. Por favor, escolha outra.',
    '151': u'Você não pode realizar pagamentos por essa forma de pagamento. Por favor, escolha outra.',
    '159': u'Seu pagamento não pode ser processado. Verifique seu cadastro junto ao MercadoPago através desse <a href="https://www.mercadopago.com.br/ajuda/contactForm?form_id=148" target="_blank">formulário</a> informando a situação e o código de erro: 159.',
    '160': u'Não foi possível processar o pagamento.',
    '204': u'A operadora do cartão informado não está disponível no momento.',
    '205': u'Digite o seu número de cartão.',
    '208': u'Escolha um mês para a data de expiração.',
    '209': u'Escolha um ano para a data de expiração.',
    '221': u'Digite o seu nome como está impresso no cartão.',
    '224': u'Digite o código de segurança do seu cartão.',
    'E301': u'Número do cartão inválido.',
    'E302': u'Código de segurança inválido.',
    '316': u'Titular do cartão inválido.',
    '325': u'Mês da data de expiração inválido.',
    '326': u'Ano da data de expiração inválido.',
    '801': u'Você já enviou um pagamento semelhante no mesmo minuto. Tente novamente em alguns minutos.',
    '2001': u'Você já enviou um pagamento semelhante no mesmo minuto. Tente novamente em alguns minutos.',
    '2004': u'Pedido cancelado devido a um erro interno no MercadoPago.',
    '2018': u'Esse pedido foi cancelado devido a um erro de processamento.',
    '2020': u'Seu pagamento não pode ser processado. Verifique seu cadastro junto ao MercadoPago através desse <a href="https://www.mercadopago.com.br/ajuda/contactForm?form_id=148" target="_blank">formulário</a> informando a situação e o código de erro: 159.',
    '2027': u'Não foi possível realizar esse pagamento com a operadora do seu cartão. Por favor, use um cartão de outra operadora.',
    '2034': u'Não foi possível processar o pagamento com o e-mail cadastrado.',
    '2040': u'Não foi possível processar o pagamento com o e-mail informado.',
    '3000': u'Digite o seu nome como está impresso no cartão.',
    '3003': u'Número do cartão parece inválido. Por favor verfique o número e tente de novo com outro pedido.',
    '3005': u'Esse pedido foi cancelado devido a um erro de processamento.',
    '3006': u'Número do cartão parece inválido. Por favor verfique o número e tente de novo com outro pedido.',
    '3008': u'Número do cartão parece inválido. Por favor verfique o número e tente de novo com outro pedido.',
    '3011': u'A operadora do seu cartão não foi identificada pelo sistema. Por favor, tente um cartão de outra operadora.',
    '3014': u'A operadora do seu cartão não foi identificada pelo sistema. Por favor, tente um cartão de outra operadora.',
    '3015': u'Número do cartão parece inválido. Por favor verfique o número e tente de novo com outro pedido.',
    '3016': u'Número do cartão parece inválido. Por favor verfique o número e tente de novo com outro pedido.',
    '3018': u'Escolha um mês para a data de expiração.',
    '3019': u'Escolha um ano para a data de expiração.',
    '3020': u'Digite o seu nome como está impresso no cartão.',
    '3028': u'Não foi possível realizar esse pagamento com a operadora do seu cartão. Por favor, use um cartão de outra operadora.',
    '3029': u'Mês da data de expiração inválido.',
    '3030': u'Ano da data de expiração inválido.',
    '4029': u'Não foi possível processar o pagamento com o e-mail cadastrado.',
    '4033': u'O cartão escolhido não aceitou o parcelamento selecionado. Por favor tente de novo com outro cartão.',
    '4037': u'O cartão escolhido não aceitou o parcelamento selecionado. Por favor tente de novo com outro cartão.',
    'accredited': u'Seu pagamento foi aprovado com sucesso.',
    'refunded': u'O pagamento foi devolvido ao comprador.',
    'pending_contingency': u'Estamos processando o pagamento e em até 1 hora você será informado do resultado por e-mail.',
    'pending_review_manual': u'O pagamento está em análise e em até 2 dias úteis você será informado do resultado por e-mail.',
    'payer_unavailable': u'Seu pagamento não pode ser processado. Verifique seu cadastro junto ao MercadoPago através desse <a href="https://www.mercadopago.com.br/ajuda/contactForm?form_id=148" target="_blank">formulário</a> informando a situação e o código de erro: payer_unavailable.',
    'cc_rejected_bad_filled_card_number': u'O número do cartão informado é inválido.',
    'cc_rejected_bad_filled_date': u'A data de expiração do cartão é inválida.',
    'cc_rejected_bad_filled_other': u'Uma ou mais informações enviadas estão inválidas.',
    'cc_rejected_bad_filled_security_code': u'O código de segurança é inválido.',
    'cc_rejected_blacklist': u'Não foi possível processar o pagamento.',
    'cc_rejected_call_for_authorize': u'Você precisa autorizar o MercadoPago junto a operadora do cartão.',
    'cc_rejected_card_disabled': u'O cartão usado precisa ser habilitado com a operadora.',
    'cc_rejected_card_error': u'Não foi possível processar o pagamento.',
    'cc_rejected_duplicated_payment': u'Você já fez um pagamento desse valor. Se você precisa pagar novamente use outro cartão ou outro meio de pagamento.',
    'cc_rejected_high_risk': u'O seu pagamento foi recusado.',
    'cc_rejected_insufficient_amount': u'O cartão usado não tem saldo suficiente.',
    'cc_rejected_invalid_installments': u'O cartão usado não aceita as parcelas selecionadas.',
    'cc_rejected_max_attempts': u'Você atingiu o limite de tentativas permitidas. Use outro cartão ou um outro meio de pagamento.',
    'cc_rejected_other_reason': u'A operadora do cartão não processou o pagamento.',
}


class AtualizadorAccessToken(object):
    def __init__(self):
        self.configuracao = None
        self.conexao = None
        self.tentativa = 1
        self.tentativa_maxima = 2

    def define_configuracao_e_conexao(self, servico):
        self.configuracao = servico.configuracao
        self.conexao = servico.conexao

    def deve_reenviar(self, resposta):
        self.tentativa += 1
        deve = 1 < self.tentativa <= self.tentativa_maxima and (
            resposta.conteudo.get('message', '') in ['expired_token', 'invalid_token'] or
            resposta.conteudo.get('error', '') == 'invalid_access_token'
        )
        if deve:
            self.atualiza_credenciais()
        return deve

    def atualiza_credenciais(self):
        self.configuracao.instalar({'fase_atual': '2', 'tipo': 'atualizar', 'codigo_autorizacao': self.configuracao.codigo_autorizacao})
        self.conexao.credenciador.configuracao = self.configuracao
        self.conexao.credenciador.atualiza_credenciais()


class EntregaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(EntregaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        self.tem_malote = True
        self.faz_http = True
        self.conexao = self.obter_conexao()
        # self.conexao.tenta_outra_vez = False
        self.url = '{}/v1/payments'.format(URL_API_BASE)
        self.tentativa_maxima = 4

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def atualiza_credenciais(self):
        self.configuracao.instalar({'fase_atual': '2', 'tipo': 'atualizar', 'codigo_autorizacao': self.configuracao.codigo_autorizacao})
        self.conexao.credenciador.configuracao = self.configuracao
        self.conexao.credenciador.atualiza_credenciais()

    @property
    def idempotencia(self):
        return '{}_{}_{}_{}'.format(
            self.loja_id,
            self.pedido.numero,
            CODIGO_GATEWAY,
            self.formatador.formata_decimal(self.malote.transaction_amount, como_int=True)
        )

    def envia_pagamento(self, tentativa=1):
        if self.pedido.situacao_id and self.pedido.situacao_id not in [
                    servicos.SituacaoPedido.SITUACAO_PEDIDO_PENDENTE,
                    servicos.SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO,
                    servicos.SituacaoPedido.SITUACAO_PEDIDO_EFETUADO
                ]:
            self.resultado = {
                'resultado': DE_PARA_SITUACAO_STATUS.get(self.pedido.situacao_id, 'pending'),
                'mensagem': DE_PARA_SITUACAO_MENSAGEM.get(self.pedido.situacao_id, MENSAGEM_ERRO_PADRAO),
                'fatal': self.pedido.situacao_id == servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO,
            }
            next_url = self.dados.get('next_url', None)
            if next_url:
                self.resultado['next_url'] = next_url
            raise self.PedidoJaRealizado(
                u'Já foi realizado um pedido com o número {} e ele está como {}.\n{}'.format(
                    self.pedido.numero,
                    servicos.SituacaoPedido.NOMES_SITUACAO[self.pedido.situacao_id],
                    servicos.SituacaoPedido.mensagens_complementares(self.pedido.situacao_id)
                )
            )
        self.conexao.headers.update({'X-Idempotency-Key': self.idempotencia})
        self._enviando_pagamento(tentativa)

    def _enviando_pagamento(self, tentativa):
        self.dados_enviados = {'tentativa': tentativa}
        self.dados_enviados.update(self.malote.to_dict())
        self.resposta = self.conexao.post(self.url, self.malote.to_dict())
        if self.resposta.nao_autenticado or self.resposta.nao_autorizado:
            reenviar = tentativa <= self.tentativa_maxima and (
                self.resposta.conteudo.get('message', '') in ['expired_token', 'invalid_token'] or
                self.resposta.conteudo.get('error', '') == 'invalid_access_token'
            )
            if reenviar:
                tentativa += 1
                self.atualiza_credenciais()
                self._enviando_pagamento(tentativa)
        if self.resposta.requisicao_invalida:
            reenviar = tentativa <= self.tentativa_maxima and (
                self.resposta.conteudo.get('message', '') == 'Invalid card token'
            )
            if reenviar:
                tentativa += 1
                self._enviando_pagamento(tentativa)

    def processa_dados_pagamento(self):
        tempo_espera = TEMPO_MAXIMO_ESPERA_NOTIFICACAO
        while tempo_espera:
            pedido = self.cria_entidade_pagador('Pedido', numero=self.pedido.numero, loja_id=self.configuracao.loja_id)
            if pedido.situacao_id not in [servicos.SituacaoPedido.SITUACAO_PEDIDO_EFETUADO]:
                self.situacao_pedido = None
                self.resultado = {'resultado': 'alterado_por_notificacao', 'mensagem': '', 'fatal': pedido.situacao_id == servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO, 'pago': self.situacao_pedido in [servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO, servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE]}
                return
            sleep(1)
            tempo_espera -= 1
        if self.resposta.sucesso:
            self.define_dados_pagamento()
            self.situacao_pedido = SituacoesDePagamento.do_tipo(self.resposta.conteudo['status'])
            mensagem_retorno = MENSAGENS_RETORNO.get(self.resposta.conteudo['status_detail'], MENSAGEM_ERRO_PADRAO)
            self.resultado = {'resultado': self.resposta.conteudo['status'], 'mensagem': mensagem_retorno, 'fatal': self.situacao_pedido == servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO, 'pago': self.situacao_pedido in [servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO, servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE]}
        else:
            self.situacao_pedido = servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO if self.resposta.requisicao_invalida else servicos.SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO
            if isinstance(self.resposta.conteudo, dict):
                erros = [u'{}'.format(MENSAGENS_RETORNO.get(str(causa['code']), causa.get('description', u'Erro não identificado.'))) for causa in self.resposta.conteudo.get('cause', [])]
            else:
                erros = MENSAGEM_ERRO_PADRAO
            self.dados_pagamento = {
                'conteudo_json': {
                    'mensagem_retorno': erros
                }
            }
            mensagem = u'Dados inválidos enviados ao MercadoPago'
            if len(erros) > 0:
                if u'Erro não identificado.' not in erros[0]:
                    mensagem = erros[0]
            self.resultado = {'resultado': self.resposta.conteudo['status'], 'mensagem': mensagem, 'fatal': self.situacao_pedido == servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO, 'pago': False}
            raise self.EnvioNaoRealizado(
                mensagem,
                self.loja_id,
                self.pedido.numero,
                dados_envio=self.malote.to_dict(),
                erros=erros,
                status=self.resposta.conteudo.get('status', 500)
            )

    def define_dados_pagamento(self):
        self.dados_pagamento = {
            'transacao_id': self.resposta.conteudo['id'],
            'valor_pago': self.malote.transaction_amount,
            'conteudo_json': {
                'bandeira': self.malote.payment_method_id,
                'mensagem_retorno': MENSAGENS_RETORNO.get(self.resposta.conteudo.get('status_detail'), MENSAGEM_ERRO_PADRAO),
                'numero_parcelas': int(self.malote.installments),
                'valor_parcela': float(self.dados_cartao.get('valor_parcela', float(self.malote.transaction_amount)))
            }
        }
        self.identificacao_pagamento = self.resposta.conteudo['id']

    @property
    def dados_cartao(self):
        return self.pedido.conteudo_json.get(GATEWAY, {})


class SituacoesDePagamento(servicos.SituacoesDePagamento):
    DE_PARA = {
        'approved': servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO,
        'pending': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE,
        'in_process': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE,
        'rejected': servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO,
        'in_mediation': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_DISPUTA,
        'refunded': servicos.SituacaoPedido.SITUACAO_PAGTO_DEVOLVIDO,
        'cancelled': servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO,
        'charged_back': servicos.SituacaoPedido.SITUACAO_PAGTO_CHARGEBACK
    }


DE_PARA_SITUACAO_STATUS = {
    servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO: 'approved',
    servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE: 'pending',
    servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO: 'rejected'
}

DE_PARA_SITUACAO_MENSAGEM = {
    servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO: 'Seu pagamento foi aprovado.',
    servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE: 'Estamos processando o pagamento',
    servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO: 'Seu pagamento foi recusado pela operadora'
}


class Retorno(object):
    def __init__(self, dados):
        tipo = dados.get('type', None)
        eh_pagamento = tipo == 'payment'
        self.valido = 'data' in dados and eh_pagamento
        self.dados = {}
        self.id = dados['data']['id']
        self.valor_pago = None
        self.metodo_pagamento = None
        self.mensagem_retorno = None
        self.numero_parcelas = None
        self.valor_parcela = None
        self.situacao_pedido = None
        self.pedido_numero = None

    def recebe_dados_de_retorno(self, dados):
        self.dados = dados
        self.valido = 'id' in dados
        if not self.valido:
            return
        self.id = dados['id']
        self.valor_pago = float(dados.get('transaction_amount', 0.0))
        self.metodo_pagamento = dados.get('payment_method_id')
        self.mensagem_retorno = MENSAGENS_RETORNO.get(dados.get('status_detail'), MENSAGEM_ERRO_PADRAO)
        self.numero_parcelas = int(dados.get('installments', 1))
        self.valor_parcela = self.valor_pago
        self.situacao_pedido = SituacoesDePagamento.do_tipo(dados.get('status', ''))
        self.pedido_numero = dados['external_reference']
        if 'transaction_details' in self.dados:
            self.valor_parcela = self.dados['transaction_details'].get('installment_amount', self.valor_pago)


class RegistraNotificacao(servicos.RegistraResultado):
    def __init__(self, loja_id, dados=None):
        super(RegistraNotificacao, self).__init__(loja_id, dados)
        self.conexao = self.obter_conexao()
        self.retorno = Retorno(dados)
        self.faz_http = True
        self.tentativa = 1
        self.tentativa_maxima = 2
        self._url = '{}/v1/payments'.format(URL_API_BASE)

    @property
    def url(self):
        return '{}/{}'.format(self._url, self.retorno.id)

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def define_dados_pagamento(self):
        self.dados_pagamento = {
            'transacao_id': self.retorno.id,
            'valor_pago': self.retorno.valor_pago,
            'conteudo_json': {
                'bandeira': self.retorno.metodo_pagamento,
                'mensagem_retorno': self.retorno.mensagem_retorno,
                'numero_parcelas': self.retorno.numero_parcelas,
                'valor_parcela': self.retorno.valor_parcela
            }
        }
        self.identificacao_pagamento = self.retorno.id

    def monta_dados_pagamento(self):
        if self.resposta and self.resposta.sucesso:
            self.retorno.recebe_dados_de_retorno(self.resposta.conteudo)
            if not self.retorno.valido:
                self.resultado = {'resultado': 'erro', 'status_code': self.resposta.status_code, 'conteudo': self.resposta.conteudo}
                return
            self.pedido_numero = self.retorno.pedido_numero
            self.define_dados_pagamento()
            self.situacao_pedido = self.retorno.situacao_pedido
            self.resultado = {'resultado': 'OK'}
        elif self.resposta and (self.resposta.nao_autenticado or self.resposta.nao_autorizado):
            self.reenviar = self.tentativa <= self.tentativa_maxima and (
                self.resposta.conteudo.get('message', '') in ['expired_token', 'invalid_token'] or
                self.resposta.conteudo.get('error', '') == 'invalid_access_token'
            )
            if self.reenviar:
                self.reenviando()
            else:
                self.resultado = {'resultado': 'nao autorizado', 'conteudo': self.resposta.conteudo}
        elif self.resposta:
            self.resultado = {'resultado': 'erro', 'status_code': self.resposta.status_code, 'conteudo': self.resposta.conteudo}
        else:
            self.resultado = {'resultado': 'erro', 'status_code': 500, 'conteudo': {'mensagem': u'MercadoPago não retornou uma resposta válida'}}

    def reenviando(self):
        self.tentativa += 1
        self.obtem_informacoes_pagamento()
        self.monta_dados_pagamento()

    def atualiza_credenciais(self):
        self.configuracao.instalar({'fase_atual': '2', 'tipo': 'atualizar', 'codigo_autorizacao': self.configuracao.codigo_autorizacao})
        self.conexao.credenciador.configuracao = self.configuracao
        self.conexao.credenciador.atualiza_credenciais()

    def obtem_informacoes_pagamento(self):
        if not self.retorno.valido:
            return
        if self.tentativa > 1:
            self.atualiza_credenciais()
        self.resposta = self.conexao.get(self.url)


class AtualizaTransacoes(servicos.AtualizaTransacoes):
    def __init__(self, loja_id, dados):
        super(AtualizaTransacoes, self).__init__(loja_id, dados)
        self.url = '{}/collections/search'.format(URL_API_BASE)
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.querystring)
        self.atualizador_credenciais = AtualizadorAccessToken()

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def _gera_dados_envio(self):
        initial_date = '{}T00:00:00Z'.format(self.dados['data_inicial'])
        final_date = '{}T23:59:59Z'.format(self.dados['data_final'])
        return {
            'criteria': 'desc',
            'sort': 'date_created',
            'range': 'date_created',
            'limit': 1000,
            'begin_date': initial_date,
            'end_date': final_date
        }

    def consulta_transacoes(self):
        self.atualizador_credenciais.define_configuracao_e_conexao(self)
        self._obtem_resposta()

    def _obtem_resposta(self):
        self.dados_enviados = self._gera_dados_envio()
        self.resposta = self.conexao.get(self.url, dados=self.dados_enviados)

    def analisa_resultado_transacoes(self):
        if self.resposta.sucesso:
            transacoes = self.resposta.conteudo['results']
            self.dados_pedido = []
            for transacao in transacoes:
                transacao = transacao['collection']
                if transacao['notification_url'] and GATEWAY in transacao['notification_url']:
                    self.dados_pedido.append({
                        'situacao_pedido': SituacoesDePagamento.do_tipo(transacao['status']),
                        'pedido_numero': transacao['external_reference']
                    })
        elif self.resposta.nao_autenticado or self.resposta.nao_autorizado:
            if self.atualizador_credenciais.deve_reenviar(self.resposta):
                self._obtem_resposta()
                self.analisa_resultado_transacoes()
        else:
            if 'error' in self.resposta.conteudo:
                self.erros = self.resposta.conteudo
