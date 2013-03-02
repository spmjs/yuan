# coding: utf-8

from flask import Blueprint
from flask import request
from flask import render_template
from ..models import Project
from ..elastic import search_project


bp = Blueprint('front', __name__)


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/<name>/')
def profile(name):
    items = Project.list(name)
    dct = {'projects': items, 'family': name}
    return render_template('profile.html', **dct)


@bp.route('/<family>/<name>')
def project(family, name):
    project = Project(family=family, name=name)
    return render_template('project.html', project=project)


@bp.route('/search')
def search():
    q = request.args.get('q')
    data = search_project(q)
    return render_template('search.html', data=data)
