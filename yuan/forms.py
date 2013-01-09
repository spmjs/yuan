from flask.ext.wtf import Form
from flask.ext.wtf import TextField, PasswordField
from flask.ext.wtf.html5 import EmailField
from flask.ext.wtf import Required, Email, Length
from flask.ext.babel import lazy_gettext as _

from .models import db, Account


class BaseForm(Form):
    pass


class SignupForm(BaseForm):
    name = TextField(
        _('Username'), validators=[Required(), Length(min=3, max=20)]
    )
    email = EmailField(
        _('Email'), validators=[Required(), Email()]
    )
    password = PasswordField(
        _('Password'), validators=[Required()]
    )

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
