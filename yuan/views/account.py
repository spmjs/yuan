# coding: utf-8

from flask import Blueprint

bp = Blueprint('account', __name__)


@bp.route('/signup')
def signup():
    pass


@bp.route('/signin')
def signin():
    pass


@bp.route('/signout')
def signout():
    pass


@bp.route('/settings')
def settings():
    pass


@bp.route('/group')
def group():
    pass
