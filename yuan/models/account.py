# coding: utf-8

import hashlib
import random
from datetime import datetime
from werkzeug import cached_property
from ._base import db, YuanQuery

__all__ = ['Account', 'Group']


class Account(db.Model):
    query_class = YuanQuery

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, index=True, nullable=False)
    email = db.Column(db.String(200), index=True)

    # user need a password
    password = db.Column(db.String(100))

    screen_name = db.Column(db.String(80))
    bio = db.Column(db.String(400))

    # user, org
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

    @cached_property
    def created_by(self):
        if self.account_type == 'user':
            return self.id
        return self.role

    @cached_property
    def comment_service_name(self):
        if self.comment_service:
            return self.comment_service.split('-')[0]
        return None

    @cached_property
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


group_member = db.Table(
    'group_member', db.Model.metadata,
    db.Column(
        'account_id', db.Integer,
        db.ForeignKey('account.id', ondelete='CASCADE')
    ),
    db.Column(
        'group_id', db.Integer,
        db.ForeignKey('group.id', ondelete='CASCADE')
    )
)


class Group(db.Model):
    query_class = YuanQuery

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    permission = db.Column(db.String(10), default='read')
    # belong to an organization
    org_id = db.Column(
        db.Integer,
        db.ForeignKey('account.id', ondelete='CASCADE'),
        nullable=False
    )

    # contain members
    memebers = db.dynamic_loader(
        Account,
        secondary=group_member,
        query_class=YuanQuery,
    )
