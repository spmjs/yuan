# coding: utf-8

from flask import Blueprint
from flask import render_template
from ..models import Project, Account


bp = Blueprint('front', __name__)


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/<name>/')
def profile(name):
    account = Account.query.filter_by(name=name).first_or_404()
    if account.permission_read.can():
        items = Project.query.filter_by(owner_id=account.id).all()
    else:
        items = Project.query.\
                filter_by(owner_id=account.id, private=False).all()
    dct = {'projects': items, 'account': account}
    return render_template('profile.html', **dct)
