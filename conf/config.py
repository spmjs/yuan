#!/usr/bin/env python

# This is a example config file for production

DEBUG = False
TESTING = False

# generate a secret key and keep it secret
SECRET_KEY = ''

# database information
SQLALCHEMY_DATABASE_URI = 'mysql://user@localhost:3306/yuan?charset=utf8'
SQLALCHEMY_POOL_SIZE = 100
SQLALCHEMY_POOL_TIMEOUT = 10
SQLALCHEMY_POOL_RECYCLE = 3600


# email settings
MAIL_SERVER = 'smtp.'
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'noreply@'
MAIL_PASSWORD = ''
DEFAULT_MAIL_SENDER = MAIL_USERNAME

# site information
SITE_TITLE = ''
SITE_URL = ''
SITE_GA = ''
