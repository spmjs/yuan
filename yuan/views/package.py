# coding: utf-8

from flask import Blueprint
from ..models import Project

bp = Blueprint('front', __name__)


@bp.route('/')
def homeindex():
    # only index public project
    projects = Project.query.filter_by(private=False)
    return projects


@bp.route('/<name>/')
def accountindex():
    pass


@bp.route('/search')
def search():
    pass


@bp.route('/info')
def info():
    pass


@bp.route('/upload')
def upload():
    pass


@bp.route('/dowload')
def download():
    pass
