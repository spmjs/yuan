#!/usr/bin/env python

import json
import requests
import gevent
from flask import _app_ctx_stack
from flask_sqlalchemy import models_committed
from .models import Account, Project


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


elastic = ElasticSearch()


def update_model(sender, changes):
    for model, operation in changes:
        if isinstance(model, Project):
            gevent.spawn(update_project, model, operation)


def update_project(item, operation):
    if operation == 'delete':
        elastic.delete('project/%d', item.id)
        return
    account = Account.query.get(item.owner_id)
    if not account:
        return
    dct = {
        "name": item.name,
        "account": account.name,
        "homepage": item.homepage,
        "description": item.description,
        "keywords": item.keyword_list,
        "created": item.created.strftime('%Y-%m-%dT%H:%M:%S'),
    }
    elastic.post('project/%d' % item.id, dct)


def search_project(query):
    if not query:
        return None
    size = 30
    dct = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["name", "account", "keywords", "description"]
            }
        },
        "highlight": {
            "order": "score",
            "pre_tags": ["<i class='highlight'>"],
            "post_tags": ["</i>"],
            "fields": {
                "content": {"number_of_fragments": 1}
            }
        },
        "fields": [
            "name", "account", "homepage", "description", "keywords",
            "created"
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


#models_committed.connect(update_model)
