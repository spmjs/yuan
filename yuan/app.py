# coding: utf-8

import os
import re
import datetime
PROJDIR = os.path.abspath(os.path.dirname(__file__))
ROOTDIR = os.path.split(PROJDIR)[0]

import misaka as m
import tempfile
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from flask import Flask
from flask import request, g, escape
from flask.ext.babel import Babel
from flask.ext.principal import Principal, Identity, identity_loaded, UserNeed
from flask import Markup
from werkzeug.routing import BaseConverter


class HighlightRender(m.HtmlRenderer, m.SmartyPants):
    def block_code(self, text, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % escape(text.strip())
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
            formatter = HtmlFormatter()
            return highlight(text, lexer, formatter)
        except:
            return '\n<pre class="language-%s"><code>%s</code></pre>\n' % (
                lang, escape(text.strip())
            )


class FamilyConverter(BaseConverter):
    regex = '[a-z][a-z0-9\-]+'


def create_app(config=None):
    from .models import db
    from .views import front, account, repository, admin
    from .helpers import get_current_user
    from .search import searcher
    from .tasks import connect

    app = Flask(
        __name__,
        static_folder='_static',
        template_folder='templates',
    )
    app.config.from_pyfile(os.path.join(ROOTDIR, 'conf', 'base_config.py'))
    app.url_map.converters['family'] = FamilyConverter

    if 'YUAN_SETTINGS' in os.environ:
        app.config.from_envvar('YUAN_SETTINGS')
    if config and isinstance(config, dict):
        app.config.update(config)
    elif config:
        app.config.from_pyfile(config)

    app.config.update({'SITE_TIME': datetime.datetime.utcnow()})

    # set tempdir
    tempdir = app.config.get('TEMPDIR', None)
    tempfile.tempdir = tempdir

    # prepare for database
    db.init_app(app)
    db.app = app

    searcher.init_app(app)
    admin.admin.init_app(app)

    # register blueprints
    app.register_blueprint(account.bp, url_prefix='/account')
    app.register_blueprint(repository.bp, url_prefix='/repository')
    app.register_blueprint(front.bp, url_prefix='')

    register_jinja(app)

    @app.before_request
    def load_current_user():
        g.user = get_current_user()

    connect()
    register_babel(app)
    register_principal(app)
    register_logger(app)
    return app


def register_jinja(app):
    @app.template_filter('markdown')
    def markdown(text):
        if not text:
            return Markup('')
        render = HighlightRender(flags=m.HTML_ESCAPE | m.HTML_USE_XHTML)
        md = m.Markdown(
            render,
            extensions=m.EXT_FENCED_CODE | m.EXT_AUTOLINK
        )
        return Markup(md.render(text))

    @app.template_filter('repo_link')
    def repo_link(repo):
        if not repo:
            return Markup('')

        url = None
        if isinstance(repo, basestring):
            url = repo
        if isinstance(repo, dict) and 'url' in repo:
            url = repo['url']

        if not url:
            return Markup('')

        link = url.replace('git@', 'https://', 1)
        link = url.replace('git://', 'https://', 1)
        link = re.sub(r'.git$', '', link)
        link = re.sub(r'^git(@|:\/\/)', 'https://', link)
        return Markup('<a href="%s">%s</a>' % (link, url))

    @app.template_filter('doc_link')
    def doc_link(family, name):
        rootdir = app.config.get('WWW_ROOT', None)
        if not rootdir:
            return None
        doc_host = app.config.get('DOC_HOST', None)
        if not doc_host:
            return None
        path = os.path.join(rootdir, 'docs', family, name)
        if not os.path.exists(path):
            return None
        return doc_host % {'family': family, 'name': name}

    @app.template_filter("package_to_url")
    def package_to_url(pkg_name):
        return "/" + pkg_name.replace("@", "/")


def register_babel(app):
    # babel for i18n
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        app.config.setdefault('BABEL_SUPPORTED_LOCALES', ['en', 'zh'])
        app.config.setdefault('BABEL_DEFAULT_LOCALE', 'en')
        match = app.config['BABEL_SUPPORTED_LOCALES']
        default = app.config['BABEL_DEFAULT_LOCALE']
        return request.accept_languages.best_match(match, default)


def register_principal(app):
    princi = Principal(app)

    @princi.identity_loader
    def load_identity():
        return Identity('yuan')

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        identity.user = g.user
        if not g.user:
            return
        identity.provides.add(UserNeed(g.user.id))


def register_logger(app):
    import logging
    if app.debug:
        return
    handler = logging.StreamHandler()
    handler.setLevel(logging.ERROR)
    app.logger.addHandler(handler)
