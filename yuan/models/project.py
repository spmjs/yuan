# coding: utf-8

from datetime import datetime
from werkzeug import cached_property
from flask.ext.principal import Permission
from ._base import db, YuanQuery, SessionMixin
from ._base import create_user_needs

__all__ = ['Project', 'Package']


class Project(db.Model, SessionMixin):
    query_class = YuanQuery

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('account.id', ondelete='CASCADE'),
    )

    name = db.Column(db.String(40), unique=True, index=True)
    homepage = db.Column(db.String(200))

    screen_name = db.Column(db.String(80))
    description = db.Column(db.String(400))

    private = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    packages = db.relationship(
        'Package', backref='project', lazy='dynamic',
    )

    @cached_property
    def permission_read(self):
        if not self.private:
            class _Permission(object):
                def can(self):
                    return True
            return _Permission()
        needs = create_user_needs(self.owner_id, 0)
        return Permission(*needs)


class Package(db.Model, SessionMixin):
    query_class = YuanQuery

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('project.id', ondelete='CASCADE'),
    )
    version = db.Column(db.String(50), nullable=False)
    tag = db.Column(db.String(20), default='stable')
    readme = db.Column(db.Text)

    download_url = db.Column(db.String(400))
    dependencies = db.Column(db.Text)
    md5value = db.Column(db.String(50), unique=True)

    created = db.Column(db.DateTime, default=datetime.utcnow)

    @cached_property
    def dependency_list(self):
        if not self.dependencies:
            return []
        return self.dependencies.split()

    @cached_property
    def html(self):
        #TODO markdown
        return self.readme
