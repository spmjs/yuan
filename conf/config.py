DEBUG = False
TESTING = False

# site information
SITE_TITLE = ''
SITE_URL = ''
SITE_GA = ''

# generate a secret key and keep it secret
SECRET_KEY = ''
PASSWORD_SECRECT = ''

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

# WWW_ROOT = '/www/'

# BABEL_SUPPORTED_LOCALES = ['en', 'zh']
# BABEL_DEFAULT_LOCALE = 'en'
