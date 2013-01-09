import hashlib
import random
from datetime import datetime
from flask.ext.login import UserMixin

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Account(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, index=True)
    email = db.Column(db.String(200), unique=True, index=True)

    # user need a password
    password = db.Column(db.String(100))

    screen_name = db.Column(db.String(80))
    bio = db.Column(db.String(400))

    # user, org, com
    account_type = db.Column(db.String(10), default='user')
    comment_service = db.Column(db.String(100))

    private = db.Column(db.Boolean, default=False)
    status = db.Column(db.Integer, default=1)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(20))

    def __init__(self, email, **kwargs):
        self.email = email.lower()
        self.token = self.create_token(16)

        if 'password' in kwargs:
            raw = kwargs.pop('password')
            self.password = self.create_password(raw)

        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_avatar(self, size=48):
        if self.avatar:
            return self.avatar
        md5email = hashlib.md5(self.email).hexdigest()
        query = "%s?s=%s%s" % (md5email, size, db.app.config['GRAVATAR_EXTRA'])
        return db.app.config['GRAVATAR_BASE_URL'] + query

    def is_active(self):
        return self.status > 1

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


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, nullable=False, index=True)

    name = db.Column(db.String(40), unique=True, index=True)
    screen_name = db.Column(db.String(80))
    description = db.Column(db.String(400))

    private = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class Version(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(db.Integer, nullable=False, index=True)
    semantic = db.Column(db.String(50), nullable=False)
    channel = db.Column(db.String(20), default='stable')

    download_url = db.Column(db.String(400))
    md5value = db.Column(db.String(50), unique=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)
