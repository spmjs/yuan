from flask.ext.wtf import Form
from flask.ext.wtf import TextField, PasswordField
from flask.ext.wtf.html5 import EmailField
from flask.ext.wtf import Required, Email, Length
from flask.ext.babel import lazy_gettext as _

from .models import db, Account


class BaseForm(Form):
    pass


class SignupForm(Form):
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
