# coding: utf-8

from flask import Blueprint
from flask import request
from flask import abort, render_template
from distutils.version import StrictVersion
from ..models import Project, Package, Account
from ..elastic import search_project


bp = Blueprint('front', __name__)


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/<name>/')
def profile(name):
    items = Project.list(name)
    items = map(_fill_project, items)
    account = Account.query.filter_by(name=name).first()
    if not account and not items:
        return abort(404)
    dct = {'projects': items, 'family': name, 'account': account}
    return render_template('profile.html', **dct)


@bp.route('/<family>/<name>')
def project(family, name):
    project = Project(family=family, name=name)
    if not project.created_at:
        return abort(404)
    latest = _fill_project(project)
    package = Package(family=family, name=name, version=latest['version'])
    project['latest'] = package
    project['versions'] = latest['versions']

    account = Account.query.filter_by(name=family).first()
    return render_template('project.html', project=project, account=account)


@bp.route('/search')
def search():
    q = request.args.get('q')
    data = search_project(q)
    return render_template('search.html', data=data)


def _fill_project(item):
    if 'versions' not in item:
        return item
    versions = item['versions']
    keys = versions.keys()
    keys = sorted(keys, key=lambda i: StrictVersion(i), reverse=True)
    latest = versions[keys[0]]
    latest['versions'] = keys
    return latest
