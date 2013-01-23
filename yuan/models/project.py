# coding: utf-8

from datetime import datetime
from werkzeug import cached_property
from ._base import db, cache, YuanQuery, SessionMixin

__all__ = ['Project', 'Package']


class Project(db.Model, SessionMixin):
    query_class = YuanQuery

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('account.id', ondelete='CASCADE'),
    )

    name = db.Column(db.String(40), index=True)
    homepage = db.Column(db.String(200))
    repository = db.Column(db.String(400))

    description = db.Column(db.String(400))

    private = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    packages = db.relationship('Package', lazy='dynamic')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Project: %s>' % self

    @cache.memoize(100)
    def package(self):
        pkg = Package.query.filter_by(project_id=self.id)\
                .filter_by(tag='stable')\
                .order_by(Package.id.desc())\
                .first()
        return pkg

    @cache.memoize(100)
    def tagged_project(self, tag):
        packages = Package.query.filter_by(
            project_id=self.id, tag=tag
        ).order_by(Package.id.desc()).all()

        data = self.to_dict(
            'name', 'homepage', 'repository', 'description',
            'created', 'updated',
        )

        def _to_dict(pkg):
            dct = pkg.to_dict('version', 'download_url', 'created')
            dct['md5'] = pkg.md5value
            dct['dependencies'] = pkg.dependency_list
            return dct

        data['packages'] = map(_to_dict, packages)
        return data


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

    def __str__(self):
        return '%s - %s' % (self.project_id, self.version)

    def __repr__(self):
        return '<Package: %s>' % self

    @cache.memoize(100)
    def project(self):
        return Project.query.get(self.project_id)

    @cached_property
    def dependency_list(self):
        if not self.dependencies:
            return []
        return self.dependencies.split()

    @cached_property
    def html(self):
        #TODO markdown
        return self.readme

    @classmethod
    @cache.memoize(100)
    def get_by_version(cls, project_id, version):
        q = cls.query.filter_by(project_id=project_id, version=version)
        return q.first()

    def dict_with_project(self, project=None):
        if not project:
            project = self.project

        data = project.to_dict(
            'name', 'homepage', 'repository', 'description',
            'created', 'updated', 'private',
        )
        data['version'] = self.version
        data['download_url'] = self.download_url
        data['tag'] = self.tag
        data['md5'] = self.md5value
        data['dependencies'] = self.dependency_list
        return data
