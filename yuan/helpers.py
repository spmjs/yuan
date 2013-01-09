import functools
from flask import g, request, session
from flask import flash, url_for, redirect, abort
from flask.ext.babel import lazy_gettext as _
from .models import Account


class require_role(object):
    def __init__(self, role):
        self.role = role

    def __call__(self, method):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            if not g.user:
                url = url_for('account.signin')
                if '?' not in url:
                    url += '?next=' + request.url
                return redirect(url)
            if g.user.role is None:
                return method(*args, **kwargs)
            if g.user.id == 1:
                # this is superuser, have no limitation
                return method(*args, **kwargs)
            if g.user.role == 1:
                flash(_('Please verify your email'), 'warn')
                return redirect('/account/setting')
            if g.user.role < 1:
                #TODO
                return redirect('/doc/guideline')
            if g.user.role < self.role:
                return abort(403)
            return method(*args, **kwargs)
        return wrapper


require_login = require_role(None)
require_user = require_role(2)
require_staff = require_role(6)
require_admin = require_role(9)


def get_user():
    if 'id' in session and 'token' in session:
        user = Account.query.get(int(session['id']))
        if not user:
            return None
        if user.token != session['token']:
            return None
        return user
    # request header
    return None


def login_user(user, permanent=False):
    if not user:
        return None
    session.permanent = permanent
    session['id'] = user.id
    session['token'] = user.token
    return user


def logout_user():
    if 'id' not in session:
        return
    session.pop('id')
    session.pop('token')
