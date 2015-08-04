# -*- coding: utf-8 -*-

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

SECRET_KEY = 'chavesecretadetestes1234567890dompt'

TIMEZONE = 'America/Sao_Paulo'

DEBUG = False
#
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql_psycopg2",
#         "HOST": "127.0.0.1",
#         "NAME": "lojaintegrada",
#         "USER": "lojaintegrada",
#         "PASSWORD": "lojaintegrada",
#         "PORT": "5432",
#         "CONN_MAX_AGE": 60,
#         "TIME_ZONE": 'America/Sao_Paulo'
#     }
# }