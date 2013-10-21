import gevent
import gevent.monkey
gevent.monkey.patch_all()

import os
import urllib
import requests
from datetime import datetime
from urlparse import urlparse
from flask import Flask
from yuan.models import Package
from yuan.models import Project
from yuan.models import index_project
from yuan.search import index_project as index_search
from yuan.tasks import extract_assets


def mirror(url, config):
    """sync a mirror site."""

    print('  mirror: %s' % url)
    rv = requests.get(url)
    if rv.status_code != 200:
        raise Exception('%s: %s' % url, rv.status_code)

    data = rv.json()

    rv = urlparse(url)
    domain = '%s://%s/repository' % (rv.scheme, rv.netloc)

    def index_with_ctx(config, project):
        app = Flask('mirror')
        app.config = config
        with app.test_request_context():
            _index(project, domain, config)

    jobs = []
    for project in data:
        if not isinstance(project, dict):
            raise Exception('Only mirror a selected family')

        me = Project(family=project['family'], name=project['name'])
        if 'updated_at' not in me or \
           _strptime(me['updated_at']) < _strptime(project['updated_at']):
            jobs.append(gevent.spawn(index_with_ctx, config, project))

    gevent.joinall(jobs)


def _strptime(t):
    return datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ')


def _fetch(pkg, domain, config):
    url = '%s/%s/%s/%s/' % (
        domain, pkg['family'], pkg['name'], pkg['version'])
    rv = requests.get(url)
    print('   fetch: %s' % url)
    if rv.status_code != 200:
        raise Exception('%s: %s' % url, rv.status_code)
    pkg = Package(**rv.json()).save()

    url = '%s%s' % (url, pkg['filename'])
    fpath = os.path.join(
        config['WWW_ROOT'], 'repository',
        pkg.family, pkg.name, pkg.version,
        pkg['filename']
    )
    print('    save: %s' % fpath)
    urllib.urlretrieve(url, fpath)
    try:
        extract_assets(pkg, 'upload')
    except:
        print('  extract: assets error')


def _index(project, domain, config):
    print('    sync: %(family)s/%(name)s' % project)
    url = '%s/%s/%s/' % (domain, project['family'], project['name'])
    rv = requests.get(url)
    if rv.status_code != 200:
        raise Exception('%s: %s' % url, rv.status_code)
    data = rv.json()
    if 'packages' not in data:
        data['packages'] = {}

    me = Project(family=project['family'], name=project['name'])

    if 'packages' in me:
        packages = me['packages'].copy()
    else:
        packages = {}

    for v in packages:
        local = packages[v]
        server = None
        if v in data['packages']:
            server = data['packages'][v]

        if not server:
            print('  delete: %s/%s@%s' % (me['family'], me['name'], v))
            pkg = Package(family=me['family'], name=me['name'], version=v)
            try:
                extract_assets(pkg, 'delete')
            except:
                print('  delete: assets error')

            pkg.delete()
            # remove this version from project
            Project(**me).remove(v)
        elif 'md5' not in server:
            print('  error: md5 not in remote')
            continue
        elif 'md5' not in local or local['md5'] != server['md5']:
            print('  create: %s/%s@%s' % (me['family'], me['name'], v))
            _fetch(server, domain, config)
            # add this version to project
            Project(**me).update(server)
        elif local['md5'] == server['md5']:
            print('    warn: %s/%s@%s, same md5' % (
                me['family'], me['name'], v
            ))
            Project(**me).save()
            continue

    for v in data['packages']:
        if v not in packages:
            pkg = data['packages'][v]
            print('  create: %s/%s@%s' % (pkg['family'], pkg['name'], v))
            _fetch(pkg, domain, config)
            # add this version to project
            Project(**me).update(pkg)

    project = Project(family=project['family'], name=project['name'])
    try:
        index_search(project, 'update')
    except:
        print('  index: search error')
    index_project(project, 'update')
    return True
