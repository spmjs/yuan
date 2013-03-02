# coding: utf-8

import gevent
from flask import Flask
from flask import current_app, url_for, render_template
from flask.ext.babel import gettext as _
from flask_mail import Mail, Message
from .helpers import create_auth_token


def send_mail(config, msg):
    app = Flask('yuan')
    app.config = config
    with app.test_request_context():
        mail = Mail(app)
        mail.send(msg)


def signup_mail(user, path=None):
    config = current_app.config
    if not config.get('DEFAULT_MAIL_SENDER', None):
        return
    msg = Message(
        _("Signup for %(site)s", site=config['SITE_TITLE']),
        recipients=[user.email],
        extra_headers={
            'Category': 'signup'
        },
    )
    reply_to = config.get('MAIL_REPLY_TO', None)
    if reply_to:
        msg.reply_to = reply_to
    host = config.get('SITE_SECURE_URL', '') or config.get('SITE_URL', '')
    dct = {
        'host': host.rstrip('/'),
        'token': create_auth_token(user)
    }
    if path:
        dct['path'] = path
    else:
        dct['path'] = url_for('account.signup')
    link = '%(host)s%(path)s?token=%(token)s' % dct
    html = render_template('email/signup.html', user=user, link=link)
    msg.html = html
    gevent.spawn(send_mail, config, msg)
