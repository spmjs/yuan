# coding: utf-8

import os
import sys
import gevent.monkey
gevent.monkey.patch_all()

from flask.ext.script import Manager
from yuan.app import create_app
from yuan.models import Project, Package
from flask import json

ROOTDIR = os.path.abspath(os.path.dirname(__file__))
CONF = os.path.join(ROOTDIR, 'etc/config.py')
if not os.path.exists(CONF):
    CONF = os.path.join(ROOTDIR, 'conf/dev_config.py')

app = create_app(CONF)
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

    try:
        run_server()
    except TypeError:
        sys.exit()


@manager.command
def createdb():
    """Create a database."""
    from yuan.models import db
    db.create_all()


@manager.command
def initsearch():
    """init search engine."""
    from yuan.search import index_project
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
def initassets():
    from yuan.tasks import extract_assets
    for name in Project.all():
        for item in Project.list(name):
            item = Project(family=item['family'], name=item['name'])
            for key in item.packages:
                pkg = Package(**item.packages[key])
                print(pkg)
                extract_assets(pkg, 'upload')


@manager.command
def initdependents():
    from yuan.tasks import calculate_dependents
    for name in Project.all():
        for item in Project.list(name):
            item = Project(family=item['family'], name=item['name'])
            for key in item.packages:
                pkg = Package(**item.packages[key])
                print(pkg)
                calculate_dependents(pkg, 'update')


@manager.command
def status():
    from scripts.status import calculate

    data = calculate()
    repo = os.path.join(app.config['WWW_ROOT'], 'repository')

    with open(os.path.join(repo, 'popular.json'), 'w') as f:
        json.dump(data['popular'], f)

    with open(os.path.join(repo, 'latest.json'), 'w') as f:
        json.dump(data['latest'], f)


@manager.command
def mirror(url=None):
    """sync a mirror site."""
    if not url:
        url = app.config['MIRROR_URL']

    from scripts.mirror import mirror
    import time
    print('\n  %s' % time.ctime())
    if isinstance(url, (list, tuple)):
        for i in url:
            mirror(i, app.config)
    else:
        mirror(url, app.config)


if __name__ == '__main__':
    manager.run()
