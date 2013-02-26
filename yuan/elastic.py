#!/usr/bin/env python

import json
import requests
import gevent
from flask import Flask, current_app
from flask import _app_ctx_stack
from .models import project_signal

__all__ = ['ElasticSearch', 'elastic', 'search_project', 'index_project']


class ElasticSearch(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('ELASTICSEARCH_HOST', 'http://localhost:9200')
        app.config.setdefault('ELASTICSEARCH_INDEX', app.name)

        self.app = app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['elasticsearch'] = self

    def get_app(self):
        if self.app is not None:
            return self.app
        ctx = _app_ctx_stack.top
        if ctx is not None:
            return ctx.app
        raise RuntimeError(
            'application not registered on ElasticSearch '
            'instance and no application bound to current context'
        )

    def request_base(self):
        app = self.get_app()
        host = app.config.get('ELASTICSEARCH_HOST')
        index = app.config.get('ELASTICSEARCH_INDEX')
        return '%s/%s' % (host, index)

    def get(self, path):
        url = '%s/%s' % (self.request_base(), path)
        req = requests.get(url)
        if req.status_code == 200 or req.status_code == 201:
            return json.loads(req.text)
        raise ValueError('response error %d:%s' % (req.status_code, req.text))

    def post(self, path, data=None):
        url = '%s/%s' % (self.request_base(), path)
        req = requests.post(url, data=json.dumps(data))
        if req.status_code == 200 or req.status_code == 201:
            return json.loads(req.text)
        raise ValueError('response error %d:%s' % (req.status_code, req.text))

    def put(self, path, data=None):
        url = '%s/%s' % (self.request_base(), path)
        req = requests.put(url, data=json.dumps(data))
        if req.status_code == 200 or req.status_code == 201:
            return json.loads(req.text)
        raise ValueError('response error %d:%s' % (req.status_code, req.text))

    def delete(self, path):
        url = '%s/%s' % (self.request_base(), path)
        req = requests.delete(url)
        if req.status_code == 200:
            return json.loads(req.text)
        raise ValueError('response error %d:%s' % (req.status_code, req.text))


elastic = ElasticSearch()


def index_project(project, operation):
    if operation == 'delete':
        elastic.delete('project/%d', project.id)
        return

    if not project.versions:
        return

    package = project.versions[list(project.versions)[0]]
    dct = dict(
        family=project.family,
        name=project.name,
        created_at=project.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
        updated_at=project.updated_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
    )
    if 'keywords' in package and isinstance(package['keywords'], list):
        dct['keywords'] = package['keywords']

    if 'description' in package:
        dct['description'] = package['description']

    elastic.post('project/%d' % project.id, dct)


def search_project(query):
    if not query:
        return None
    size = 30
    dct = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": [
                    "name", "family", "keywords", "description"
                ]
            }
        },
        "fields": [
            "name", "family", "homepage", "description", "keywords",
            "created_at", "updated_at"
        ],
        "size": size
    }
    content = elastic.post('project/_search', dct)
    hits = content['hits']

    def _format(item):
        fields = item['fields']
        fields['id'] = item['_id']
        return fields

    results = map(_format, hits['hits'])
    hits['results'] = results
    del hits['hits']
    return hits


def _connect_project(sender, changes):
    project, operation = changes

    def _index(config):
        app = Flask('yuan')
        app.config = config
        with app.test_request_context():
            index_project(project, operation)

    gevent.spawn(_index, current_app.config)


project_signal.connect(_connect_project)
