# coding: utf-8

import os
import gevent.monkey
gevent.monkey.patch_all()

from flask.ext.script import Manager
from yuan.app import create_app

CONFIG = os.path.abspath('./etc/config.py')

app = create_app(CONFIG)
manager = Manager(app)


@manager.command
def runserver(port=5000):
    """Runs a development server."""
    from gevent.wsgi import WSGIServer
    from werkzeug.serving import run_with_reloader
    from werkzeug.debug import DebuggedApplication

    port = int(port)

    @run_with_reloader
    def run_server():
        print('start server at: 127.0.0.1:%s' % port)
        http_server = WSGIServer(('', port), DebuggedApplication(app))
        http_server.serve_forever()

    run_server()


@manager.command
def createdb():
    """Create a database."""
    from yuan.models import db
    db.create_all()


@manager.command
def initsearch():
    from yuan.models import Project
    from yuan.elastic import index_project

    for item in Project.query.all():
        index_project(item, 'update')


@manager.command
def index():
    from yuan.models import Project, index_project

    for item in Project.query.all():
        index_project(item, 'update')


if __name__ == '__main__':
    manager.run()
