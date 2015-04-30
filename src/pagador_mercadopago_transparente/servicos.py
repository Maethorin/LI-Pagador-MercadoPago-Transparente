# -*- coding: utf-8 -*-
from urllib import urlencode
from datetime import datetime, timedelta

from li_common.comunicacao import requisicao

from pagador import settings, servicos


class TipoToken(object):
    authorization_code = 'authorization_code'
    refresh_token = 'refresh_token'


class InstalaMeioDePagamento(servicos.InstalaMeioDePagamento):
    campos = ['usuario', 'token', 'token_expiracao', 'codigo_autorizacao']

    def __init__(self, loja_id, dados):
        super(InstalaMeioDePagamento, self).__init__(loja_id, dados)
        parametros = self.cria_entidade_pagador('ParametrosDeContrato', loja_id=loja_id).obter_para('mercadopago')
        self.client_id = parametros['client_id']
        self.client_secret = parametros['client_secret']
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
            'redirect_uri': '{}?{}'.format(settings.INSTALAR_REDIRECT_URL.format(self.loja_id, 'mptransparente'), parametros_redirect)
        }
        return 'http://auth.mercadolivre.com.br/authorization?{}'.format(urlencode(dados))

    def obter_user_id(self, access_token):
        url = 'https://api.mercadolibre.com/users/me?access_token={}'.format(access_token)
        resposta = self.conexao.get(url)
        if resposta.sucesso:
            return resposta.conteudo['id']
        return None

    @property
    def _dados_instalacao(self):
        try:
            parametros_redirect = urlencode({'next_url': self.dados['next_url'], 'fase_atual': '2'})
        except KeyError:
            raise self.InstalacaoNaoFinalizada(u'Você precisa informar a url de redirecionamento na volta do MercadoPago na chave next_url do parâmetro dados.')
        return {
            'code': self.dados['code'],
            'grant_type': TipoToken.authorization_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': '{}?{}'.format(settings.INSTALAR_REDIRECT_URL.format(self.loja_id, 'mptransparente'), parametros_redirect)
        }

    @property
    def _dados_atualizacao(self):
        return {
            'refresh_token': self.dados['codigo_autorizacao'],
            'grant_type': TipoToken.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

    def obter_dados(self):
        url = 'https://api.mercadolibre.com/oauth/token'
        tipo = self.dados.get('tipo', 'instalar')
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
                user_id = self.obter_user_id(resposta.conteudo['access_token'])
                resultado['usuario'] = user_id
            return resultado
        raise self.InstalacaoNaoFinalizada(u'Erro ao entrar em contato com o MercadoPago. Código: {}, Resposta: {}'.format(resposta.status_code, resposta.conteudo))

    def desinstalar(self, dados):
        url_base = 'https://api.mercadolibre.com/users/{}/applications/{}?access_token={}'
        url = url_base.format(dados['usuario'], self.client_id, dados['token'])
        resposta = self.conexao.delete(url)
        if resposta.nao_autorizado:
            self.dados['tipo'] = 'atualizar'
            dados_atualizados = self.obter_dados()
            url = url_base.format(dados['usuario'], self.client_id, dados_atualizados['token'])
            resposta = self.conexao.delete(url)
        if resposta.sucesso:
            return u'Aplicação removida com sucesso'
        raise self.InstalacaoNaoFinalizada(u'Aplicação não foi removida do MercadoPago devido a um erro de comunicação. Código: {}, Resposta: {}'.format(resposta.status_code, resposta.conteudo))


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
    '106': u'Você não poe fazer pagamentos para usuários em outros países.',
    '109': u'O seu cartão não aceita as parcelas selecionadas.',
    '126': u'Não foi possível efetuar o pagamento com esse cartão.',
    '129': u'O cartão informado não suporta o valor da compra.',
    '145': u'Não foi possível processar o pagamento.',
    '150': u'Você não pode realizar pagamentos por essa forma de pagamento. Por favor, escolha outra.',
    '151': u'Você não pode realizar pagamentos por essa forma de pagamento. Por favor, escolha outra.',
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
    'accredited': u'Seu pagamento foi aprovado com sucesso.',
    'pending_contingency': u'Estamos processando o pagamento e em até 1 hora você será informado do resultado por e-mail.',
    'pending_review_manual': u'O pagamento está em análise e em até 2 dias úteis você será informado do resultado por e-mail.',
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


class EntregaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(EntregaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        self.tem_malote = True
        self.faz_http = True
        self.conexao = self.obter_conexao()
        self.url = 'https://api.mercadolibre.com/checkout/custom/create_payment'
        self.tentativa = 1
        self.tentativa_maxima = 2

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def atualiza_credenciais(self):
        self.configuracao.instalar({'fase_atual': '2', 'tipo': 'atualizar', 'codigo_autorizacao': self.configuracao.codigo_autorizacao})
        self.conexao.credenciador.configuracao = self.configuracao
        self.conexao.credenciador.atualiza_credenciais()

    def envia_pagamento(self, tentativa=1):
        self.tentativa = tentativa
        if self.tentativa > 1:
            self.atualiza_credenciais()
        self.dados_enviados = {'tentativa': tentativa}
        self.dados_enviados.update(self.malote.to_dict())
        self.resposta = self.conexao.post(self.url, self.malote.to_dict())
        if self.resposta.nao_autenticado or self.resposta.nao_autorizado:
            self.reenviar = self.tentativa <= self.tentativa_maxima and (
                self.resposta.conteudo.get('message', '') in ['expired_token', 'invalid_token'] or
                self.resposta.conteudo.get('error', '') == 'invalid_access_token'
            )
            if self.reenviar:
                raise self.EnvioNaoRealizado(u'Autenticação da loja com o MercadoPago Falhou. Tentou reenviar: {}'.format(self.reenviar), self.loja_id, self.pedido.numero)

    def processa_dados_pagamento(self):
        if self.resposta.sucesso:
            self.dados_pagamento = {
                'transacao_id': self.resposta.conteudo['payment_id'],
                'valor_pago': self.resposta.conteudo['amount']
            }
            self.identificacao_pagamento = self.resposta.conteudo['payment_id']
            self.dados_pagamento = {
                'conteudo_json': {
                    'bandeira': self.resposta.conteudo['payment_method_id']
                }
            }
            if self.tem_parcelas:
                self.dados_pagamento['conteudo_json'].update({
                    'numero_parcelas': int(self.resposta.conteudo.get('installments', 1)),
                    'valor_parcela': float(self.resposta.conteudo.get('installment_amount', self.resposta.conteudo['amount']))
                })
            self.situacao_pedido = SituacoesDePagamento.do_tipo(self.resposta.conteudo['status'])
            self.resultado = {'resultado': self.resposta.conteudo['status'], 'mensagem': MENSAGENS_RETORNO.get(self.resposta.conteudo['status_detail'], u'O pagamento pelo cartão informado não foi processado. Por favor, tente outra forma de pagamento.')}
        if self.resposta.requisicao_invalida:
            raise self.EnvioNaoRealizado(
                u'Dados inválidos enviados ao MercadoPago',
                self.loja_id,
                self.pedido.numero,
                dados_envio=self.malote.to_dict(),
                erros=[u'{}: {}'.format(causa['code'], MENSAGENS_RETORNO.get(str(causa['code']), causa.get('description', u'Erro não identificado.'))) for causa in self.resposta.conteudo.get('cause', [])]
            )

    @property
    def tem_parcelas(self):
        parcelas = self.resposta.conteudo.get('installments', 1)
        return int(parcelas) > 1


class SituacoesDePagamento(servicos.SituacoesDePagamento):
    DE_PARA = {
        'approved': servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO,
        'pending': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE,
        'in_process': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE,
        'rejected': servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO,
    }
