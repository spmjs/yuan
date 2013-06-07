#!/usr/bin/env python

import os
from flask import _app_ctx_stack, json
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.qparser import MultifieldParser


schema = Schema(
    path=ID(stored=True),
    family=ID(stored=True),
    name=ID(stored=True),
    description=TEXT(stored=True),
    keywords=KEYWORD(stored=True, commas=True),
    created_at=STORED(),
    updated_at=STORED(),
)


class WhooshSearch(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('WHOOSH_DIR', 'data')
        self.app = app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['elasticsearch'] = self

        @app.teardown_appcontext
        def close_searcher(response_or_exc):
            if hasattr(self, '_searcher') and \
               hasattr(self._searcher, 'close'):
                self._searcher.close()
                del self._searcher
            return response_or_exc

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

    def indexer(self):
        if hasattr(self, '_indexer'):
            return self._indexer
        app = self.get_app()
        indexdir = app.config.get('WHOOSH_DIR')
        if not os.path.exists(indexdir):
            os.mkdir(indexdir)
            indexer = create_in(indexdir, schema)
        else:
            indexer = open_dir(indexdir)
        self._indexer = indexer
        return indexer

    def search(self, query):
        q = MultifieldParser([
            'name', 'family', 'keywords', 'description'
        ], schema)

        app = self.get_app()
        if hasattr(self, '_searcher'):
            searcher = self._searcher
        else:
            ix = self.indexer()
            searcher = ix.searcher()
            self._searcher = searcher
        results = searcher.search(q.parse(query), limit=30)
        return results

    def write(self, family, name, description=None, keywords=None, **kwargs):
        ix = self.indexer()
        writer = ix.writer()

        kwargs['family'] = unicode(family)
        kwargs['name'] = unicode(name)
        kwargs['description'] = unicode(description or '')
        kwargs['path'] = u'%s/%s' % (family, name)

        if keywords and isinstance(keywords, (list, tuple)):
            kwargs['keywords'] = u','.join(keywords)

        writer.delete_by_term('path', kwargs['path'])
        writer.add_document(**kwargs)
        writer.commit()
        return self

    def delete(self, family, name):
        path = u'%s/%s' % (family, name)
        ix = self.indexer()
        ix.delete_by_term('path', path)
        ix.commit()
        return self


searcher = WhooshSearch()


def index_project(project, operation):
    if operation == 'delete':
        searcher.delete(project.family, project.name)
        return

    if 'packages' not in project:
        return

    package = project.packages[project.version]
    dct = dict(
        family=project.family,
        name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
    if 'keywords' in package and isinstance(package['keywords'], list):
        dct['keywords'] = package['keywords']

    if 'description' in package:
        dct['description'] = package['description']

    searcher.write(**dct)


def search_project(query):
    if not query:
        return None
    return searcher.search(query)
