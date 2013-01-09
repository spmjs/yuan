# coding: utf-8

from flask import Blueprint
from flask import g, request
from flask import render_template, redirect, url_for
from ..helpers import login_user, logout_user
from ..forms import SignupForm, SigninForm

bp = Blueprint('account', __name__)


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = form.save()
        login_user(user)
        return redirect(url_for('.settings'))
    return render_template('signup.html', form=form)


@bp.route('/signin', methods=['GET', 'POST'])
def signin():
    next_url = request.args.get('next', '/')
    if g.user:
        return redirect(next_url)
    form = SigninForm()
    if form.validate_on_submit():
        login_user(form.user)
        return redirect(next_url)
    return render_template('signin.html', form=form)


@bp.route('/signout')
def signout():
    next_url = request.args.get('next', '/')
    logout_user()
    return redirect(next_url)


@bp.route('/settings')
def settings():
    return render_template('settings.html')
