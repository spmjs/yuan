import hashlib
import random
from datetime import datetime

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_models_by_ids(model, ids):
    ids = set(ids)
    if len(ids) == 0:
        return {}
    if len(ids) == 1:
        ident = ids.pop()
        rv = model.query.get(ident)
        if not rv:
            return {}
        return {ident: rv}
    items = model.query.filter(model.id.in_(ids))
    dct = {}
    for u in items:
        dct[u.id] = u
    return dct


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, index=True, nullable=False)
    email = db.Column(db.String(200), index=True)

    # user need a password
    password = db.Column(db.String(100))

    screen_name = db.Column(db.String(80))
    bio = db.Column(db.String(400))

    # user, org, com
    account_type = db.Column(db.String(10), default='user')
    comment_service = db.Column(db.String(100))

    private = db.Column(db.Boolean, default=False)

    # if it is an org, role means the owner
    # if it is a user: 1 - not verified, 2 - verified, > 20 staff > 40 admin
    role = db.Column(db.Integer, default=1)

    created = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(20))

    def __init__(self, **kwargs):
        self.token = self.create_token(16)

        if 'password' in kwargs:
            raw = kwargs.pop('password')
            self.password = self.create_password(raw)

        if 'name' in kwargs:
            name = kwargs.pop('name')
            self.name = name.lower()

        if 'email' in kwargs:
            email = kwargs.pop('email')
            self.email = email.lower()

        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_avatar(self, size=48):
        if self.avatar:
            return self.avatar
        md5email = hashlib.md5(self.email).hexdigest()
        query = "%s?s=%s%s" % (md5email, size, db.app.config['GRAVATAR_EXTRA'])
        return db.app.config['GRAVATAR_BASE_URL'] + query

    @property
    def comment_service_name(self):
        if self.comment_service:
            return self.comment_service.split('-')[0]
        return None

    @property
    def comment_service_id(self):
        if self.comment_service:
            bits = self.comment_service.split('-')
            return '-'.join(bits[1:])
        return None

    @staticmethod
    def create_password(raw):
        salt = Account.create_token(8)
        passwd = '%s%s%s' % (salt, raw,
                             db.app.config['PASSWORD_SECRET'])
        hsh = hashlib.sha1(passwd).hexdigest()
        return "%s$%s" % (salt, hsh)

    @staticmethod
    def create_token(length=16):
        chars = ('0123456789'
                 'abcdefghijklmnopqrstuvwxyz'
                 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        salt = ''.join([random.choice(chars) for i in range(length)])
        return salt

    def check_password(self, raw):
        if not self.password:
            return False
        if '$' not in self.password:
            return False
        salt, hsh = self.password.split('$')
        passwd = '%s%s%s' % (salt, raw, db.app.config['PASSWORD_SECRET'])
        verify = hashlib.sha1(passwd).hexdigest()
        return verify == hsh


class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

    # owner, admin, write, read
    role_type = db.Column(db.String(20), default='write')
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def __getattr__(self, key):
        try:
            return super(GroupMember, self).__getattr__(key)
        except AttributeError as e:
            if not hasattr(self, '_model'):
                raise e
            pass
        return getattr(self._model, key)

    @classmethod
    def get_groups(cls, user_id):
        items = cls.query.filter_by(user_id=user_id).all()
        ids = (o.group_id for o in items)
        relates = get_models_by_ids(Account, ids)
        for item in items:
            if item.id in relates:
                item._model = relates[item.id]
                yield item

    @classmethod
    def get_members(cls, group_id):
        items = cls.query.filter_by(group_id=group_id).all()
        ids = (o.user_id for o in items)
        relates = get_models_by_ids(Account, ids)
        for item in items:
            if item.id in relates:
                item._model = relates[item.id]
                yield item

    @classmethod
    def is_member(cls, group_id, user_id):
        rv = cls.query.filter_by(group_id=group_id, user_id=user_id).first()
        return rv


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, nullable=False, index=True)

    name = db.Column(db.String(40), unique=True, index=True)
    homepage = db.Column(db.String(200))

    screen_name = db.Column(db.String(80))
    description = db.Column(db.String(400))

    private = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(db.Integer, nullable=False, index=True)
    version = db.Column(db.String(50), nullable=False)
    channel = db.Column(db.String(20), default='stable')

    download_url = db.Column(db.String(400))
    dependencies = db.Column(db.Text)
    md5value = db.Column(db.String(50), unique=True)

    created = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def dependency_list(self):
        if not self.dependencies:
            return []
        return self.dependencies.split()
