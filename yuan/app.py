# coding: utf-8

import os
PROJDIR = os.path.abspath(os.path.dirname(__file__))
ROOTDIR = os.path.split(PROJDIR)[0]
CONFDIR = os.path.join(PROJDIR, '_config')

from flask import Flask
from flask import request
from flask.ext.babel import Babel
from .models import db
from .views import front, account


def create_app(config=None):
    app = Flask(
        __name__,
        static_folder='_static',
        template_folder='templates',
    )
    app.config.from_pyfile(os.path.join(CONFDIR, 'base.py'))
    if config:
        app.config.from_pyfile(config)

    # prepare for database
    db.init_app(app)
    db.app = app

    # register blueprints
    app.register_blueprint(account.bp, url_prefix='/account')
    app.register_blueprint(front.bp, url_prefix='')

    @app.before_request
    def load_current_user():
        pass

    # babel for i18n
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        app.config.setdefault('BABEL_SUPPORTED_LOCALES', ['en', 'zh'])
        app.config.setdefault('BABEL_DEFAULT_LOCALE', 'en')
        match = app.config['BABEL_SUPPORTED_LOCALES']
        defautl = app.config['BABEL_DEFAULT_LOCALE']
        return request.accept_languages.best_match(match, defautl)

    return app
