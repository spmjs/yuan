# coding: utf-8

import os
import shutil
from flask import json
from flask import current_app
from datetime import datetime
from werkzeug import cached_property
from collections import OrderedDict
from distutils.version import StrictVersion


__all__ = ['Project', 'Package', 'index_project']


class Model(dict):
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __getattr__(self, key):
        try:
            return to_unicode(self[key])
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self[key] = to_unicode(value)

    def __getitem__(self, key):
        return to_unicode(super(Model, self).__getitem__(key))

    def __setitem__(self, key, value):
        return super(Model, self).__setitem__(key, to_unicode(value))

    @cached_property
    def datafile(self):
        raise NotImplementedError

    def read(self):
        fpath = self.datafile
        if not os.path.exists(fpath):
            return None
        data = _read_json(fpath)
        for key in data:
            self[key] = data[key]
        return self

    def save(self):
        fpath = self.datafile

        directory = os.path.dirname(fpath)
        if not os.path.exists(directory):
            os.makedirs(directory)

        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        if 'created_at' not in self:
            self['created_at'] = now

        with open(fpath, 'w') as f:
            self['updated_at'] = now
            json.dump(self, f)
            return self

    def delete(self):
        directory = os.path.dirname(self.datafile)
        if os.path.exists(directory):
            return shutil.rmtree(directory)
        return None


class Project(Model):
    def __init__(self, **kwargs):
        self.family = kwargs.pop('family')
        self.name = kwargs.pop('name')
        self.read()
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __str__(self):
        return '%s/%s' % (self.family, self.name)

    def __repr__(self):
        return '<Project: %s>' % self

    @classmethod
    def sort(cls, packages=None):
        if not packages:
            return {}
        o = OrderedDict()
        for v in sorted(packages.keys(),
                        key=lambda i: StrictVersion(i), reverse=True):
            o[v] = packages[v]
        return o

    @cached_property
    def datafile(self):
        root = current_app.config['WWW_ROOT']
        return os.path.join(
            root, 'repository',
            self.family, self.name,
            'index.json'
        )

    @staticmethod
    def all():
        repo = os.path.join(
            current_app.config['WWW_ROOT'],
            'repository',
        )

        def isdir(name):
            return os.path.isdir(os.path.join(repo, name))
        return filter(isdir, os.listdir(repo))

    @staticmethod
    def list(family):
        fpath = os.path.join(
            current_app.config['WWW_ROOT'],
            'repository',
            family,
            'index.json'
        )
        return _read_json(fpath)

    def update(self, dct):
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        if 'version' not in dct:
            return False
        if 'family' in dct and dct['family'] != self.family:
            return False
        if 'name' in dct and dct['name'] != self.name:
            return False

        # save package
        dct['family'] = self.family
        dct['name'] = self.name
        pkg = Package(**dct)
        pkg.save()

        keys = [
            'homepage',
            'description',
            'keywords',
            'repository',
            'author',
            'maintainers',
        ]

        for key in keys:
            if key in dct:
                self[key] = dct[key]

        packages = self.packages or {}
        if 'readme' in pkg:
            del pkg['readme']

        packages[pkg.version] = pkg
        packages = self.sort(packages)
        if packages:
            self['version'] = packages.keys()[0]

        if 'created_at' not in self:
            self['created_at'] = now

        self.packages = packages
        self['updated_at'] = now
        self.write()


        return self

    def remove(self, version):
        if 'packages' not in self:
            return self
        packages = self['packages'] or {}
        if version in packages:
            del packages[version]
            self['packages'] = packages
            self.write()
        return self

    def write(self, data=None):
        if not data:
            data = self
        storage = current_app.config['WWW_ROOT']
        directory = os.path.join(
            storage, 'repository', self.family, self.name
        )
        if not os.path.exists(directory):
            os.makedirs(directory)

        fpath = os.path.join(directory, 'index.json')
        with open(fpath, 'w') as f:
            json.dump(data, f)
            return data


class Package(Model):
    def __init__(self, **kwargs):
        self.family = kwargs.pop('family')
        self.name = kwargs.pop('name')
        self.version = kwargs.pop('version')
        self.read()
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __str__(self):
        return '%s/%s@%s' % (self.family, self.name, self.version)

    def __repr__(self):
        return '<Package: %s>' % self

    @cached_property
    def datafile(self):
        storage = current_app.config['WWW_ROOT']
        return os.path.join(
            storage, 'repository',
            self.family, self.name, self.version,
            'index.json'
        )


def index_project(project, operation):
    # project = copy.copy(project)

    repo = os.path.join(current_app.config['WWW_ROOT'], 'repository')
    if operation == 'create' or operation == 'delete':
        fullname = '%(family)s/%(name)s' % project
        repofile = os.path.join(repo, 'index.json')
        if os.path.exists(repofile):
            repoindex = _read_json(repofile)
        else:
            repoindex = []

        if fullname not in repoindex and operation == 'create':
            repoindex.insert(0, fullname)
        elif fullname in repoindex and operation == 'delete':
            repoindex.remove(fullname)
            # delete from family index.json
            familyfile = os.path.join(repo, project['family'], 'index.json')
            familyindex = _read_json(familyfile)
            count = 0
            for pkg in familyindex:
                if pkg['name'] == project['name']:
                    break
                count += 1
            familyindex.pop(count)
            with open(familyfile, 'w') as f:
                json.dump(familyindex, f)

        with open(repofile, 'w') as f:
            json.dump(repoindex, f)

    directory = os.path.join(repo, project['family'])
    fpath = os.path.join(directory, 'index.json')
    data = _read_json(fpath)
    data = filter(lambda o: o['name'] != project['name'], data)

    if operation == 'delete':
        directory = os.path.join(directory, project['name'])
        if os.path.exists(directory):
            shutil.rmtree(directory)
        with open(fpath, 'w') as f:
            json.dump(data, f)
        return data

    if not os.path.exists(directory):
        os.makedirs(directory)

    if 'packages' in project:
        del project['packages']

    def __sort(item):
        if 'update_at' in item:
            return datetime.strptime(
                item['updated_at'], '%Y-%m-%dT%H:%M:%SZ'
            )
        return None

    data.append(project)
    data = sorted(
        data,
        key=__sort,
        reverse=True
    )
    with open(fpath, 'w') as f:
        json.dump(data, f)
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


def _read_json(fpath):
    if not os.path.exists(fpath):
        return {}
    with open(fpath, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}
