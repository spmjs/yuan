# coding: utf-8

from flask.ext.wtf import Form
from flask.ext.wtf import TextField, PasswordField, BooleanField
from flask.ext.wtf import TextAreaField, SelectField
from flask.ext.wtf.html5 import EmailField
from flask.ext.wtf import Required, Email, Length, Regexp, Optional
from flask.ext.babel import lazy_gettext as _

from .models import db, Account


class BaseForm(Form):
    pass


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


class GroupForm(BaseForm):
    name = TextField(
        _('Name'), validators=[
            Required(), Length(min=3, max=20), Regexp('[a-z0-9A-Z]+')
        ], description=_('English Characters Only.'),
    )
    screen_name = TextField(_('Display Name'), validators=[Length(max=80)])
    email = EmailField(
        _('Gravatar Email'), validators=[Optional(), Email()],
        description=_('Avatar of your group.'),
    )
    bio = TextAreaField(
        _('Description'), validators=[Optional(), Length(max=400)],
        description=_('Markdown is supported.')
    )
    private = BooleanField(
        _('This is a private group.'),
        description=_('We encourage public groups.')
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
        if Account.query.filter_by(name=field.data.lower()).count():
            raise ValueError(_('This name has been registered.'))

    def validate_email(self, field):
        if field.data:
            if Account.query.filter_by(email=field.data.lower()).count():
                raise ValueError(_('This email has been registered.'))

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
        data['role'] = user.id
        group = Account(**data)
        db.session.add(group)
        db.session.commit()
        return group
