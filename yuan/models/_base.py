from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery

__all__ = ['db', 'YuanQuery']


db = SQLAlchemy()


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
