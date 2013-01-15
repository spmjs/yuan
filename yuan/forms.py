# coding: utf-8

from flask.ext.wtf import Form
from flask.ext.wtf import TextField, PasswordField, BooleanField
from flask.ext.wtf import TextAreaField, SelectField
from flask.ext.wtf.html5 import EmailField, URLField
from flask.ext.wtf import Required, Email, Length, Regexp, Optional, URL
from flask.ext.babel import lazy_gettext as _
from wtforms.compat import iteritems

from .models import db, Account, Team, Project

RESERVED_WORDS = [
    'root', 'admin', 'bot', 'robot', 'master', 'webmaster',
    'account', 'people', 'peoples', 'user', 'users',
    'project', 'team', 'teams', 'group', 'groups', 'organization',
    'organizations', 'package', 'packages', 'org', 'com', 'net',
    'help', 'doc', 'docs', 'document', 'documentation', 'blog',
]


class BaseForm(Form):
    def __init__(self, *args, **kwargs):
        self._obj = kwargs.get('obj', None)
        super(BaseForm, self).__init__(*args, **kwargs)


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
        db.session.add(user)
        db.session.commit()
        return user


class SigninForm(BaseForm):
    account = TextField(
        _('Account'), validators=[Required(), Length(min=3, max=20)]
    )
    password = PasswordField(
        _('Password'), validators=[Required()]
    )

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


class OrgForm(BaseForm):
    name = TextField(
        _('Name'), validators=[
            Required(), Length(min=3, max=20), Regexp('[a-z0-9A-Z]+')
        ], description=_('English Characters Only.'),
    )
    screen_name = TextField(_('Display Name'), validators=[Length(max=80)])
    email = EmailField(
        _('Gravatar Email'), validators=[Optional(), Email()],
        description=_('Avatar of your organization.'),
    )
    description = TextAreaField(
        _('Description'), validators=[Optional(), Length(max=400)],
        description=_('Markdown is supported.')
    )
    private = BooleanField(
        _('This is a private organization.'),
        description=_('We encourage public organizations.')
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

    def validate_name(self, field):
        if field.data.lower() in RESERVED_WORDS:
            raise ValueError(_('This name is a reserved name.'))
        if self._obj and self._obj.name == field.data.lower():
            return
        if Account.query.filter_by(name=field.data.lower()).count():
            raise ValueError(_('This name has been registered.'))

    def validate_email(self, field):
        if self._obj and self._obj.email == field.data.lower():
            return
        if field.data:
            if Account.query.filter_by(email=field.data.lower()).count():
                raise ValueError(_('This email has been registered.'))

    def populate_obj(self, obj):
        for name, field in iteritems(self._fields):
            if not name.startswith('comment_service'):
                field.populate_obj(obj, name)

        csn = self._fields['comment_service_name']
        csi = self._fields['comment_service_id']
        if csn and csi:
            obj.comment_service = '%s-%s' % (csn.data, csi.data)

    def save(self, user):
        data = dict(self.data)
        csn = data.pop('comment_service_name')
        csi = data.pop('comment_service_id')
        if csn and csi:
            data['comment_service'] = '%s-%s' % (csn, csi)

        email = data.pop('email')
        if email:
            data['email'] = email
        data['account_type'] = 'org'
        data['org_owner_id'] = user.id
        org = Account(**data)
        org.save()
        return org


class TeamForm(BaseForm):
    name = TextField(
        _('Name'), validators=[
            Required(), Length(min=3, max=100)
        ], description=_('3 to 100 characters.')
    )
    permission = SelectField(
        _('Permission'),
        choices=[
            ('write', 'Read & Write'),
            ('read', 'Read Only'),
            ('admin', 'Administractive'),
        ]
    )

    def save(self, org):
        data = dict(self.data)
        data['owner_id'] = org.id
        permission = data.pop('permission')
        if permission in ('read', 'write', 'admin'):
            dct = {'read': 1, 'write': 2, 'admin': 3}
            data['_permission'] = dct[permission]
        else:
            data['_permission'] = 1
        team = Team(**data)
        team.save()
        return team


class ProjectForm(BaseForm):
    name = TextField(
        _('Name'), validators=[Required(), Length(max=40)]
    )
    homepage = URLField(
        _('Homepage'), validators=[Optional(), URL()]
    )
    repository = TextField(
        _('Repository'), validators=[Optional()]
    )
    screen_name = TextField(
        _('Display Name'), validators=[Optional(), Length(max=80)]
    )
    description = TextField(
        _('Description'), validators=[Optional(), Length(max=400)]
    )
    private = BooleanField(
        _('This is a private project.'),
        description=_('We encourage public projects.')
    )

    def __init__(self, *args, **kwargs):
        self._owner = kwargs.get('owner', None)
        super(ProjectForm, self).__init__(*args, **kwargs)

    def validate_name(self, field):
        if self._obj and self._obj.name == field.data:
            return
        count = Project.query.filter_by(
            owner_id=self._owner.id, name=field.data
        ).count()
        if count:
            raise ValueError(_('This name has been registered.'))

    def save(self, org=None):
        data = dict(self.data)
        if org:
            data['owner_id'] = org.id
        else:
            data['owner_id'] = self._owner.id
        proj = Project(**data)
        proj.save()
        return proj
