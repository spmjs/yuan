# coding: utf-8

from flask import Blueprint
from flask import request
from flask import render_template
from ..models import Project, Account
from ..elastic import search_project


bp = Blueprint('front', __name__)


@bp.route('/')
def home():
    count = {
        'users': Account.query.filter_by(account_type='user').count(),
        'organizations': Account.query.filter_by(account_type='org').count(),
    }
    dct = {'count': count}
    return render_template('home.html', **dct)


@bp.route('/<name>/')
def profile(name):
    account = Account.query.filter_by(name=name).first_or_404()
    items = Project.query.filter_by(family=name).all()
    dct = {'projects': items, 'account': account}
    return render_template('profile.html', **dct)


@bp.route('/<family>/<name>')
def project(family, name):
    project = Project.query.filter_by(
        family=family, name=name).first_or_404()
    account = Account.query.filter_by(name=family).first()
    dct = {'account': account, 'project': project}
    return render_template('project.html', **dct)


@bp.route('/search')
def search():
    q = request.args.get('q')
    data = search_project(q)
    return render_template('search.html', data=data)
