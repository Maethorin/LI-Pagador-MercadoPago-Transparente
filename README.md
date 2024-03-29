# LI-Pagador-MercadoPago

Meio de pagamento usando o checkout transparente do MercadoPago (http://developers.mercadopago.com/documentation/custom-checkout-advanced)


## Versão:

[![PyPi version](https://pypip.in/version/li-pagador-mercadopago-transparente/badge.svg?text=versão)](https://pypi.python.org/pypi/li-pagador-mercadopago-transparente)
[![PyPi downloads](https://pypip.in/download/li-pagador-mercadopago-transparente/badge.svg)](https://pypi.python.org/pypi/li-pagador-mercadopago-transparente)


## Build Status

### Master

[![Build Status](https://travis-ci.org/lojaintegrada/LI-Pagador-MercadoPago-Transparente.svg?branch=master)](https://travis-ci.org/lojaintegrada/LI-Pagador-MercadoPago-Transparente)
[![Coverage Status](https://coveralls.io/repos/lojaintegrada/LI-Pagador-MercadoPago-Transparente/badge.svg?branch=master)](https://coveralls.io/r/lojaintegrada/LI-Pagador-MercadoPago-Transparente?branch=master)


## Usuários de teste

### Como criar:

https://developers.mercadopago.com/documentacao/autenticacao
POST em https://api.mercadolibre.com/oauth/token
com grant_type=client_credentials&client_id=ZAS&client_secret=ZAS

https://developers.mercadopago.com/documentacao/criar-usuarios-de-teste#create-test-user
POST em https://api.mercadolibre.com/users/test_user?access_token=ZAS
com {"site_id":"MLB"}


### Usuários criados pela LI

 [
    {
        "id": 192273789,
        "nickname": "TETE3535964",
        "password": "qatest9936",
        "site_status": "active",
        "email": "test_user_53308633@testuser.com",
        "descricao": "admin"
    },
    {
        "id": 192275808,
        "nickname": "TETE3981515",
        "password": "qatest8893",
        "site_status": "active",
        "email": "test_user_65234069@testuser.com",
        "descricao": "vendedor"
    },
    {
        "id": 192275813,
        "nickname": "TETE1773031",
        "password": "qatest1152",
        "site_status": "active",
        "email": "test_user_85037308@testuser.com",
        "descricao": "comprador"
    }
]

## Criando aplicações:

http://developers.mercadopago.com/documentation/applications

## Removendo permissões:

https://www.mercadopago.com/mlb/account/security/applications/connections

### Aplicação usada nos testes da LI

APP Local:
ID: 4881490647844915
SECRET: 9UtO6yiQsml1GPH0WtqHiPMjvbJYo69E

## Exemplo de retorno de resultado do MP

http://localhost:5000/pagador/meio-pagamento/mercadopago/retorno/8/resultado?
    referencia=707&
    next_url=http://www.custompaper.com.br/checkout/707/finalizacao&sucesso=2&
    collection_id=1078562391&
    collection_status=pending&
    preference_id=177547755-8d1ff996-61df-4c7c-ba2e-ee71d108cbd4&
    external_reference=707&
    payment_type=ticket
