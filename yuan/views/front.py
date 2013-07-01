# coding: utf-8

from flask import Blueprint
from flask import request
from flask import abort, render_template
from distutils.version import StrictVersion
from ..models import Project, Package, Account
from ..search import search_project


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


@bp.route('/<family:family>/<name>/')
def project(family, name):
    project = Project(family=family, name=name)
    if 'created_at' not in project:
        return abort(404)
    package = Package(family=family, name=name, version=project.version)

    project['latest'] = package

    versions = project.packages.keys()
    versions = sorted(versions, key=lambda i: StrictVersion(i), reverse=True)
    project['versions'] = versions

    account = Account.query.filter_by(name=family).first()
    return render_template('project.html', project=project, account=account)


@bp.route('/<family:family>/<name>/<version>/')
def version(family, name, version):
    pkg = Package(family=family, name=name, version=version)
    if 'created_at' not in pkg:
        return abort(404)
    return render_template('version.html', package=pkg)


@bp.route('/search')
def search():
    q = request.args.get('q')
    data = search_project(q)
    return render_template('search.html', data=data)
