# coding: utf-8

from flask.ext.wtf import TextField, PasswordField, BooleanField
from flask.ext.wtf import TextAreaField, SelectField
from flask.ext.wtf.html5 import EmailField
from flask.ext.wtf import Required, Email, Length, Regexp, Optional
from flask.ext.babel import lazy_gettext as _
from wtforms.compat import iteritems

from ._base import BaseForm
from ..models import Account

RESERVED_WORDS = [
    'root', 'admin', 'bot', 'robot', 'master', 'webmaster',
    'account', 'people', 'user', 'users', 'project', 'projects',
    'team', 'teams', 'group', 'groups', 'organization',
    'organizations', 'package', 'packages', 'org', 'com', 'net',
    'help', 'doc', 'docs', 'document', 'documentation', 'blog',
    'bbs', 'forum', 'forums', 'static', 'assets', 'repository',
    'mac', 'windows', 'ios', 'lab',
]


class SignupForm(BaseForm):
    name = TextField(
        _('Username'), validators=[
            Required(), Length(min=3, max=20), Regexp('[a-z0-9A-Z]+')
        ], description=_('English Characters Only.'),
    )
    email = EmailField(
        _('Email'), validators=[Required(), Email()]
    )
    password = PasswordField(
        _('Password'), validators=[Required()]
    )

    def validate_name(self, field):
        if field.data.lower() in RESERVED_WORDS:
            raise ValueError(_('This name is a reserved name.'))
        if Account.query.filter_by(name=field.data.lower()).count():
            raise ValueError(_('This name has been registered.'))

    def validate_email(self, field):
        if Account.query.filter_by(email=field.data.lower()).count():
            raise ValueError(_('This email has been registered.'))

    def save(self):
        user = Account(**self.data)
        user.save()
        return user


class SigninForm(BaseForm):
    account = TextField(
        _('Account'), validators=[Required(), Length(min=3, max=20)]
    )
    password = PasswordField(
        _('Password'), validators=[Required()]
    )
    permanent = BooleanField(_('Remember me for a month.'))

    def validate_password(self, field):
        account = self.account.data
        if '@' in account:
            user = Account.query.filter_by(email=account).first()
        else:
            user = Account.query.filter_by(name=account).first()

        if not user:
            raise ValueError(_('Wrong account or password'))
        if user.check_password(field.data):
            self.user = user
            return user
        raise ValueError(_('Wrong account or password'))


class SettingForm(BaseForm):
    screen_name = TextField(_('Display Name'), validators=[Length(max=80)])
    description = TextAreaField(
        _('Description'), validators=[Optional(), Length(max=400)],
        description=_('Markdown is supported.')
    )
    comment_service_name = SelectField(
        _('Comment Service'),
        choices=[
            ('disqus', 'Disqus'),
            ('duoshuo', 'Duoshuo'),
        ]
    )
    comment_service_id = TextField(
        _('Service ID'), validators=[Length(max=80)]
    )

    def populate_obj(self, obj):
        for name, field in iteritems(self._fields):
            if not name.startswith('comment_service'):
                field.populate_obj(obj, name)

        csn = self._fields['comment_service_name']
        csi = self._fields['comment_service_id']
        if csn and csi:
            obj.comment_service = '%s-%s' % (csn.data, csi.data)


class OrgSettingForm(SettingForm):
    email = EmailField(
        _('Gravatar Email'), validators=[Optional(), Email()],
        description=_('Avatar of your organization.'),
    )

    def validate_email(self, field):
        if self._obj and self._obj.email == field.data.lower():
            return
        if field.data:
            if Account.query.filter_by(email=field.data.lower()).count():
                raise ValueError(_('This email has been registered.'))


class OrgForm(OrgSettingForm):
    name = TextField(
        _('Name'), validators=[
            Required(), Length(min=3, max=20), Regexp('[a-z0-9A-Z]+')
        ], description=_('English Characters Only.'),
    )

    def validate_name(self, field):
        if field.data.lower() in RESERVED_WORDS:
            raise ValueError(_('This name is a reserved name.'))
        if Account.query.filter_by(name=field.data.lower()).count():
            raise ValueError(_('This name has been registered.'))

    def save(self, user_id):
        data = dict(self.data)
        csn = data.pop('comment_service_name')
        csi = data.pop('comment_service_id')
        if csn and csi:
            data['comment_service'] = '%s-%s' % (csn, csi)

        email = data.pop('email')
        if email:
            data['email'] = email
        data['account_type'] = 'org'
        data['org_owner_id'] = user_id
        org = Account(**data)
        org.save()
        return org
