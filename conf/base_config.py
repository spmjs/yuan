DEBUG = False
TESTING = False

#: site
SITE_TITLE = 'Yuan'
SITE_URL = '/'
SITE_GA = None
SITE_STYLES = [
    '/_static/all.css',
    'http://fontawesome.io/assets/font-awesome/css/font-awesome.css'
]

#: session
SESSION_COOKIE_NAME = 'yuan'
#SESSION_COOKIE_SECURE = True
PERMANENT_SESSION_LIFETIME = 3600 * 24 * 30

#: account
# generate a secret key and keep it secret
SECRET_KEY = 'secret-key'
PASSWORD_SECRET = 'password-secret'
GRAVATAR_BASE_URL = 'http://www.gravatar.com/avatar/'
GRAVATAR_EXTRA = ''

#: sqlalchemy
# SQLALCHEMY_DATABASE_URI = ''
# SQLALCHEMY_POOL_SIZE = 100
# SQLALCHEMY_POOL_TIMEOUT = 10
# SQLALCHEMY_POOL_RECYCEL = 3600

# email settings
# MAIL_SERVER = 'smtp.'
# MAIL_USE_TLS = False
# MAIL_USE_SSL = True
# MAIL_USERNAME = 'noreply@'
# MAIL_PASSWORD = ''
# MAIL_DEFAULT_SENDER = MAIL_USERNAME

#: file storage
WWW_ROOT = 'data'
# WWW_ROOT = '/www/data'
DOC_HOST = 'http://%(family)s.spmjs.org/%(name)s/'
ALLOW_ANONYMOUS = False
ASSETS_ROOT = None
# ASSETS_ROOT = /www/data/assets
WHOOSH_DIR = 'data/whoosh'

MIRROR_URL = [
    'http://spmjs.org/repository/seajs/',
    'http://spmjs.org/repository/jquery/',
    'http://spmjs.org/repository/gallery/',
    'http://spmjs.org/repository/arale/',
    'http://spmjs.org/repository/alice/',
]

# Max List Count in Homepage
LIST_MAX_COUNT = 10
