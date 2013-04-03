# coding: utf-8

import os

from flask.ext.script import Manager
from yuan.app import create_app
from yuan.models import Project

app = create_app(os.path.abspath('./conf/config.py'))
manager = Manager(app)


@manager.command
def runserver(port=5000):
    """Runs a development server."""
    import gevent.monkey
    gevent.monkey.patch_all()

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
    """init search engine."""
    from yuan.elastic import index_project
    for name in Project.all():
        for item in Project.list(name):
            print '%(family)s/%(name)s' % item
            item = Project(family=item['family'], name=item['name'])
            index_project(item, 'update')


@manager.command
def index():
    """index projects."""
    from yuan.models import index_project
    for name in Project.all():
        for item in Project.list(name):
            print '%(family)s/%(name)s' % item
            index_project(item, 'update')


@manager.command
def mirror(url=None):
    """sync a mirror site."""
    if not url:
        url = app.config['MIRROR_URL']

    from scripts.mirror import mirror
    mirror(url, app.config)


if __name__ == '__main__':
    manager.run()
