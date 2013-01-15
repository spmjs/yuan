# coding: utf-8

from functools import partial
from flask.signals import Namespace
from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
from flask.ext.principal import Need, UserNeed

__all__ = [
    'db', 'YuanQuery', 'SessionMixin',
    'model_created', 'model_updated', 'model_deleted',
    'create_user_needs', 'TeamNeed',
]

signals = Namespace()
model_created = signals.signal('model-created')
model_updated = signals.signal('model-updated')
model_deleted = signals.signal('model-deleted')

db = SQLAlchemy()
TeamNeed = partial(Need, 'team')


def create_user_needs(owner_id, permission):
    rv = db.session.execute(
        'SELECT account_id FROM team_member '
        'JOIN team ON team_member.team_id=team.id '
        'AND team.owner_id=:id AND team._permission>:permission '
        'GROUP BY account_id', {'id': owner_id, 'permission': permission})
    return map(lambda o: UserNeed(o[0]), rv)


class YuanQuery(BaseQuery):
    def filter_in(self, key, ids):
        ids = set(ids)
        if len(ids) == 0:
            return {}
        if len(ids) == 1:
            ident = ids.pop()
            rv = self.get(ident)
            if not rv:
                return {}
            return {ident: rv}
        items = self.filter(key.in_(ids))
        dct = {}
        for u in items:
            dct[u.id] = u
        return dct

    def as_list(self, *columns):
        columns = map(db.defer, columns)
        return self.options(map(db.defer, columns))


class SessionMixin(object):
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
