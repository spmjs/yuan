#!/usr/bin/env python

import json
import requests
from flask import _app_ctx_stack


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
        raise ValueError('response error %d' % req.status_code)

    def post(self, path, data=None):
        url = '%s/%s' % (self.request_base(), path)
        req = requests.post(url, data=json.dumps(data))
        if req.status_code == 200 or req.status_code == 201:
            return json.loads(req.text)
        raise ValueError('response error %d' % req.status_code)

    def put(self, path, data=None):
        url = '%s/%s' % (self.request_base(), path)
        req = requests.put(url, data=json.dumps(data))
        if req.status_code == 200 or req.status_code == 201:
            return json.loads(req.text)
        raise ValueError('response error %d' % req.status_code)

    def delete(self, path):
        url = '%s/%s' % (self.request_base(), path)
        req = requests.delete(url)
        if req.status_code == 200:
            return json.loads(req.text)
        raise ValueError('response error %d' % req.status_code)
