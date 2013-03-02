# coding: utf-8

import datetime
from flask.signals import Namespace
from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
from flask.ext.cache import Cache

__all__ = [
    'db', 'cache', 'SessionMixin',
    'model_created', 'model_updated', 'model_deleted',
    'project_signal', 'package_signal'
]

signals = Namespace()
model_created = signals.signal('model-created')
model_updated = signals.signal('model-updated')
model_deleted = signals.signal('model-deleted')
project_signal = signals.signal('project-signal')
package_signal = signals.signal('package-signal')

db = SQLAlchemy()
cache = Cache()


class SessionMixin(object):
    def to_dict(self, *columns):
        dct = {}
        for col in columns:
            value = getattr(self, col)
            if isinstance(value, datetime.datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            dct[col] = value
        return dct

    def save(self):
        if self.id:
            emitter = model_updated
        else:
            emitter = model_created
        db.session.add(self)
        db.session.commit()
        emitter.send(self, model=self)
        return self

    def delete(self):
        db.session.delete(self)
        model_deleted.send(self, model=self)
        db.session.commit()
        return self
