# -*- coding: utf-8 -*-

from li_common.padroes import cadastro


class FormularioMercadoPagoTransparente(cadastro.Formulario):
    _PARCELAS = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (9, 9), (10, 10), (12, 12), (15, 15), (18, 18), (24, 24)]
    ativo = cadastro.CampoFormulario('ativo', 'Pagamento ativo?', tipo=cadastro.TipoDeCampo.boleano, ordem=1)
    nome_fatura = cadastro.CampoFormulario('informacao_complementar', u'Nome na Fatura do Comprador', tamanho_max=11, requerido=False, ordem=3, texto_ajuda=u'Informe o nome que deve aparecer na fatura do cartão do comprador.')
    valor_minimo_aceitado = cadastro.CampoFormulario('valor_minimo_aceitado', u'Valor mínimo', requerido=False, decimais=2, ordem=4, tipo=cadastro.TipoDeCampo.decimal, texto_ajuda=u'Informe o valor mínimo para exibir esta forma de pagamento.')
    valor_minimo_parcela = cadastro.CampoFormulario('valor_minimo_parcela', u'Valor mínimo da parcela', requerido=False, decimais=2, ordem=5, tipo=cadastro.TipoDeCampo.decimal)
    mostrar_parcelamento = cadastro.CampoFormulario('mostrar_parcelamento', u'Marque para mostrar o parcelamento na listagem e na página do produto.', tipo=cadastro.TipoDeCampo.boleano, requerido=False, ordem=6)
    maximo_parcelas = cadastro.CampoFormulario('maximo_parcelas', u'Máximo de parcelas', tipo=cadastro.TipoDeCampo.escolha, requerido=False, ordem=7, texto_ajuda=u'Quantidade máxima de parcelas para esta forma de pagamento.', opcoes=_PARCELAS)
    parcelas_sem_juros = cadastro.CampoFormulario('parcelas_sem_juros', 'Parcelas sem juros', tipo=cadastro.TipoDeCampo.escolha, requerido=False, ordem=8, texto_ajuda=u'Número de parcelas sem juros para esta forma de pagamento.', opcoes=_PARCELAS)

    def obter_parcelas_disponiveis(self):
        return [parcela[0] for parcela in self._PARCELAS]