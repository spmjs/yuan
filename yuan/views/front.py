# coding: utf-8

from flask import Blueprint
from flask import request
from flask import abort, render_template
from ..models import Project, Package, Account
from ..elastic import search_project


bp = Blueprint('front', __name__)


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/<name>/')
def profile(name):
    items = Project.list(name)
    account = Account.query.filter_by(name=name).first()
    if not account and not items:
        return abort(404)
    dct = {'projects': items, 'family': name, 'account': account}
    return render_template('profile.html', **dct)


@bp.route('/<family>/<name>')
def project(family, name):
    project = Project(family=family, name=name)
    if '__created_at' not in project:
        return abort(404)
    package = Package(family=family, name=name, version=project.__latest)

    project['latest'] = package
    project['versions'] = project.__versions.keys()
    project['updated_at'] = project.__updated_at

    account = Account.query.filter_by(name=family).first()
    return render_template('project.html', project=project, account=account)


@bp.route('/search')
def search():
    q = request.args.get('q')
    data = search_project(q)
    return render_template('search.html', data=data)
