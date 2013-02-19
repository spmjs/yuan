# coding: utf-8

from flask import Blueprint
from flask import request
from flask import render_template, abort
from ..models import Project, Account
from ..elastic import search_project


bp = Blueprint('front', __name__)


@bp.route('/')
def home():
    count = {
        'projects': Project.query.count(),
        'users': Account.query.filter_by(account_type='user').count(),
        'organizations': Account.query.filter_by(account_type='org').count(),
    }
    dct = {'count': count}
    return render_template('home.html', **dct)


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


@bp.route('/<name>/<pkg>')
def project(name, pkg):
    account = Account.query.filter_by(name=name).first_or_404()
    project = Project.query.filter_by(
        owner_id=account.id, name=pkg).first_or_404()
    if account.permission_read.can() or project.private is False:
        dct = {'account': account, 'project': project}
        return render_template('project.html', **dct)
    return abort(403)


@bp.route('/search')
def search():
    q = request.args.get('q')
    data = search_project(q)
    return render_template('search.html', data=data)
