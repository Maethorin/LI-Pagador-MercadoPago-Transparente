# -*- coding: utf-8 -*-

import sure, os
from tests import settings


os.environ['API_URL'] = 'http://localhost:5000/'
os.environ['CHAVE_API_PEDIDO'] = ''
os.environ['CHAVE_API_PLATAFORMA'] = ''
os.environ['PAGADOR_DEBUG'] = 'True'
os.environ['PAGADOR_ENVIRONMENT'] = 'local'
os.environ['PAGADOR_CHAVE_APLICACAO'] = '2a35710a-b0a6-4807-ab3f-95f4e4551f45'

os.environ['PAGADOR_REQUEST_BASE_TIMEOUT'] = '(15, 30)'
os.environ['PAGADOR_EXTENSOES'] = '{"deposito": "pagador_deposito", "mptransparente": "pagador_mercadopago_transparente", "koin": "pagador_koin", "pagarme": "pagador_pagarme", "boleto": "pagador_boleto", "bcash": "pagador_bcash", "pagseguro": "pagador_pagseguro", "paypal": "pagador_paypal", "mercadopago": "pagador_mercadopago", "entrega": "pagador_entrega"}'
os.environ['PAGADOR_INSTALAR_REDIRECT_URL'] = 'pagador/loja/{}/meio-pagamento/{}/instalar'
os.environ['PAGADOR_NOTIFICACAO_URL'] = 'pagador/meio-pagamento/{}/retorno/{}'

os.environ['PAGADOR_API_PEDIDO'] = 'pedido/'
os.environ['PAGADOR_AUTENTICACAO_API_PEDIDO'] = 'chave_aplicacao {}'.format(os.environ['CHAVE_API_PEDIDO'])

os.environ['PAGADOR_GRAVA_EVIDENCIA'] = 'True'
os.environ['PAGADOR_EVIDENCIA_URL'] = 'plataforma/doing/async.utils.salvar_evidencia/delay'
os.environ['PAGADOR_EVIDENCIA_USA_AUTENTICACAO_HEADER'] = 'True'
os.environ['PAGADOR_EVIDENCIA_AUTENTICACAO'] = 'chave_aplicacao '.format(os.environ['CHAVE_API_PLATAFORMA'])

os.environ['PAGADOR_PAYPAL_VERSION'] = '108.0'
