import gevent
import requests
from flask import Flask, current_app
from yuan.models import package_signal


def _publish(sender, changes):
    package, operation = changes

    def _run(config):
        app = Flask('yuan')
        app.config = config
        with app.test_request_context():
            if operation == 'upload':
                requests.post(
                    'http://site.alipay.im/repository/spm',
                    data=dict(package)
                )
            elif operation == 'delete':
                requests.delete(
                    'http://site.alipay.im/repository/spm',
                    data=dict(package)
                )

    gevent.spawn(_run, current_app.config)


def main():
    package_signal.connect(_publish)
