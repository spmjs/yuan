# coding: utf-8

from flask import Blueprint
from flask import request
from flask import abort, render_template
from distutils.version import StrictVersion
from ..models import Project, Package, Account
from ..search import search_project
import os
from flask import current_app, json
from datetime import datetime
import operator


bp = Blueprint('front', __name__)


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.utcnow()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"

def _read_json(fpath, default):
    if not os.path.exists(fpath):
        return default
    with open(fpath, 'r') as f:
        try:
            return json.load(f)
        except:
            return default

@bp.route('/')
def home():
    fpath = os.path.join(
        current_app.config["WWW_ROOT"], "repository",
        "index.json"
    )
    all_package = _read_json(fpath, {})

    fpath = os.path.join(
        current_app.config["WWW_ROOT"], "repository",
        "latest.json"
    )
    latest_publish_obj = _read_json(fpath, [])

    for obj in latest_publish_obj:
        obj["pretty_date"] = pretty_date(datetime.strptime(obj["update_at"], '%Y-%m-%dT%H:%M:%SZ'))
        obj["account"] = Account.query.filter_by(name=obj["publisher"]).first()

    def _get_max(filename):
        fpath = os.path.join(
            current_app.config["WWW_ROOT"], "repository",
            filename
        )
        obj_with_count = {}
        for key, val in _read_json(fpath, {}).iteritems():
            obj_with_count[key] = len(val)

        obj_with_count_sorted = sorted(obj_with_count.iteritems(), key=operator.itemgetter(1))
        obj_with_count_sorted.reverse()

        if len(obj_with_count_sorted) > current_app.config["LIST_MAX_COUNT"]:
            obj_with_count_sorted = obj_with_count_sorted[0:current_app.config["LIST_MAX_COUNT"]]
        return obj_with_count_sorted

    dct = {
        "total_package_count": len(all_package),
        "total_family_count": len(Project.all()),
        "total_user_count": Account.query.count(),
        "latest_publisher": latest_publish_obj,
        "most_depended_upon": _get_max("depend.json"),
        "top_submittors": _get_max("publishers.json")
    }
    return render_template('home.html', **dct)


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
