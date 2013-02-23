# coding: utf-8

import os
from flask import json
from flask import current_app
from datetime import datetime
from werkzeug import cached_property
from collections import OrderedDict
from ._base import db, YuanQuery, SessionMixin

__all__ = ['Project', 'Package']


class Project(db.Model, SessionMixin):
    query_class = YuanQuery

    id = db.Column(db.Integer, primary_key=True)
    family = db.Column(db.String(40), nullable=False, index=True)
    name = db.Column(db.String(40), nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __str__(self):
        return '%s/%s' % (self.family, self.name)

    def __repr__(self):
        return '<Project: %s>' % self

    def __file__(self):
        storage = current_app.config['PACKAGE_STORAGE']
        return os.path.join(storage, self.family, self.name, 'index.json')

    @cached_property
    def json(self):
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        if self.created_at:
            created_at = self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            created_at = now

        if self.updated_at:
            updated_at = self.updated_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            updated_at = now

        fpath = self.__file__()
        if not os.path.exists(fpath):
            return {
                'family': self.family,
                'name': self.name,
                'created_at': created_at,
                'updated_at': updated_at,
            }

        with open(fpath, 'r') as f:
            content = f.read()
            return json.loads(content)

    @cached_property
    def versions(self):
        if 'versions' in self.json:
            return self.json['versions']
        return []

    def write(self, dct):
        fpath = self.__file__()
        directory = os.path.dirname(fpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(fpath, 'w') as f:
            f.write(json.dumps(dct))
            return dct

    def update(self, dct):
        pkg = Package(**dct)
        pkg.write()

        vers = OrderedDict()
        for v in self.versions:
            if v['version'] == dct['version']:
                vers[v['version']] = dct
            else:
                vers[v['version']] = v

        versions = vers.items()
        if dct['version'] not in vers:
            versions.insert(0, dct)

        data = self.json
        data['versions'] = versions

        self.write(data)
        return data

    def remove(self, version):
        pass


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

    def __file__(self):
        storage = current_app.config['PACKAGE_STORAGE']
        fpath = os.path.join(
            storage, self.family, self.name, self.version,
            'package.json'
        )
        return fpath

    def read(self):
        fpath = self.__file__()
        if not os.path.exists(fpath):
            return None

        with open(fpath, 'r') as f:
            content = f.read()
            data = json.loads(content)
            for key in data:
                if not key.startswith('_') and not hasattr(self, key):
                    self[key] = data[key]
            return self

    def write(self):
        fpath = self.__file__()

        directory = os.path.dirname(fpath)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(fpath, 'w') as f:
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            self.created_at = now
            self.updated_at = now
            f.write(json.dumps(self))
            return self

    def delete(self):
        directory = os.path.dirname(self.__file__())
        return os.removedirs(directory)
