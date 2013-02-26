# coding: utf-8

import os
import gevent
import shutil
from flask import Flask, json
from flask import current_app
from datetime import datetime
from werkzeug import cached_property
from collections import OrderedDict
from distutils.version import StrictVersion
from ._base import db, YuanQuery, SessionMixin
from ._base import project_signal

__all__ = ['Project', 'Package', 'index_project']


class Project(db.Model, SessionMixin):
    query_class = YuanQuery

    id = db.Column(db.Integer, primary_key=True)
    family = db.Column(db.String(40), nullable=False, index=True)
    name = db.Column(db.String(40), nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, index=True)

    def __str__(self):
        return '%s/%s' % (self.family, self.name)

    def __repr__(self):
        return '<Project: %s>' % self

    def to_dict(self):
        return dict(
            family=self.family,
            name=self.name,
            created_at=self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            updated_at=self.updated_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        )

    @staticmethod
    def list(family):
        fpath = os.path.join(
            current_app.config['WWW_ROOT'],
            'repository',
            family,
            'index.json'
        )
        return _read_json(fpath)

    @staticmethod
    def read(family, name):
        storage = current_app.config['WWW_ROOT']
        fpath = os.path.join(
            storage, 'repository', family, name, 'index.json'
        )
        if not os.path.exists(fpath):
            return None
        return _read_json(fpath)

    @staticmethod
    def write(family, name, data):
        storage = current_app.config['WWW_ROOT']
        directory = os.path.join(storage, 'repository', family, name)
        if not os.path.exists(directory):
            os.makedirs(directory)

        fpath = os.path.join(directory, 'index.json')
        with open(fpath, 'w') as f:
            f.write(json.dumps(data))
            return data

    @cached_property
    def json(self):
        data = self.read(self.family, self.name)
        if data:
            return data
        return self.to_dict()

    @cached_property
    def versions(self):
        if 'versions' not in self.json:
            return {}

        versions = self.json['versions']
        o = OrderedDict()
        for v in sorted(versions.keys(),
                        key=lambda i: StrictVersion(i), reverse=True):
            o[v] = versions[v]
        return o

    def update(self, **kwargs):
        if 'version' not in kwargs:
            return False
        if 'family' in kwargs and kwargs['family'] != self.family:
            return False
        if 'name' in kwargs and kwargs['name'] != self.name:
            return False

        self.updated_at = datetime.utcnow()
        self.save()

        kwargs['family'] = self.family
        kwargs['name'] = self.name

        pkg = Package(**kwargs)
        pkg.save()

        versions = self.versions
        if 'readme' in pkg:
            del pkg['readme']
        versions[pkg.version] = pkg

        data = self.json
        data['versions'] = versions

        self.write(self.family, self.name, data)
        return data

    def remove(self, version):
        versions = self.versions
        if version in versions:
            del versions[version]

        data = self.json
        data['versions'] = versions
        self.write(self.family, self.name, data)
        return data


def to_unicode(value):
    if isinstance(value, unicode):
        return value
    if isinstance(value, basestring):
        return value.decode('utf-8')
    if isinstance(value, int):
        return str(value)
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value


class Package(dict):
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __str__(self):
        return '%s/%s@%s' % (self.family, self.name, self.version)

    def __repr__(self):
        return '<Project: %s>' % self

    def __getattr__(self, key):
        try:
            return to_unicode(self[key])
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self[key] = to_unicode(value)

    def __getitem__(self, key):
        return to_unicode(super(Package, self).__getitem__(key))

    def __setitem__(self, key, value):
        return super(Package, self).__setitem__(key, to_unicode(value))

    @cached_property
    def directory(self):
        storage = current_app.config['WWW_ROOT']
        directory = os.path.join(
            storage, 'repository', self.family, self.name, self.version
        )
        return directory

    @cached_property
    def index_file(self):
        return os.path.join(self.directory, 'index.json')

    def read(self):
        fpath = self.index_file
        if not os.path.exists(fpath):
            return None
        data = _read_json(fpath)
        for key in data:
            if not key.startswith('_'):
                self[key] = data[key]
        return self

    def save(self):
        fpath = self.index_file

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        if 'created_at' not in self:
            self.created_at = now

        with open(fpath, 'w') as f:
            self.updated_at = now
            f.write(json.dumps(self))
            return self

    def delete(self):
        if os.path.exists(self.directory):
            return shutil.rmtree(self.directory)
        return None


def index_project(project, operation):
    if isinstance(project, Project):
        project = project.to_dict()

    directory = os.path.join(
        current_app.config['WWW_ROOT'], 'repository', project['family']
    )
    fpath = os.path.join(directory, 'index.json')
    data = _read_json(fpath)
    data = filter(lambda o: o['name'] != project['name'], data)

    if operation == 'delete':
        directory = os.path.join(directory, project['name'])
        if os.path.exists(directory):
            shutil.rmtree(directory)
        with open(fpath, 'w') as f:
            f.write(json.dumps(data))
        return data

    if not os.path.exists(directory):
        os.makedirs(directory)

    data.append(project)
    data = sorted(
        data,
        key=lambda o: datetime.strptime(o['updated_at'], '%Y-%m-%dT%H:%M:%SZ'),
        reverse=True
    )
    with open(fpath, 'w') as f:
        f.write(json.dumps(data))
        return data


def _read_json(fpath):
    if not os.path.exists(fpath):
        return {}
    with open(fpath, 'r') as f:
        content = f.read()
        try:
            return json.loads(content)
        except:
            return {}


def _connect_project(sender, changes):
    project, operation = changes
    project = project.to_dict()

    def _index(config):
        app = Flask('yuan')
        app.config = config
        with app.test_request_context():
            index_project(project, operation)

    gevent.spawn(_index, current_app.config)


project_signal.connect(_connect_project)
