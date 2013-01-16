# coding: utf-8

from flask import Flask
from flask_mail import Mail


def send_mail(config, msg):
    app = Flask('yuan')
    app.config = config
    with app.test_request_context():
        mail = Mail(app)
        mail.send(msg)
