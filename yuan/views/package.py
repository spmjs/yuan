# coding: utf-8

import werkzeug
from flask import Blueprint
from flask import g, request, jsonify, abort
from distutils.version import StrictVersion
from flask.ext.babel import gettext as _
from ..models import db, Project, Package, Account
from ..forms import ProjectForm

__all__ = ['bp']

bp = Blueprint('package', __name__)


@bp.route('/')
def index():
    # only index public project
    projects = Project.query.filter_by(private=False)
    return projects


@bp.route('/<root>/')
def account():
    pass


@bp.route('/<root>/<pkg>', methods=['GET', 'POST', 'DELETE'])
def project(root, pkg):
    account = Account.query.filter_by(name=root).first()
    if not account:
        return abortify(404, message=_('Account not found.'))

    project = Project.query.filter_by(name=pkg).first()
    if request.method == 'GET':
        if not project:
            abortify(404, message=_('Project not found.'))
            return
        if project.private and not account.permission_read.can():
            return abortify(403)
        return jsonify(status='info', data=dict(project))

    if request.method == 'POST':
        if project and account.permission_write.can():
            update_project(project, account, pkg)
            return jsonify(status='info', message=_('Project updated.'))
        if not project and account.permission_admin.can():
            create_project(account, pkg)
            res = jsonify(status='info', message=_('Project created.'))
            res.status_code = 201
            return res
        return abortify(403)

    if not project:
        return abortify(404, message=_('Project not found.'))

    if not account.permission_admin.can():
        return abortify(403)
    project.delete()
    return jsonify(status='info', message=_('Project deleted.'))


@bp.route('/<root>/<pkg>/<version>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def package(root, pkg, version):
    account = Account.query.filter_by(name=root).first()
    if not account:
        return abortify(404, message=_('Account not found.'))

    project = Project.query.filter_by(name=pkg).first()
    if not project and request.method != 'POST':
        return abortify(404, message=_('Project not found.'))

    if not project:
        if not account.permission_admin.can():
            return abortify(403)
        project = create_project(account, pkg)

    if request.method == 'GET':
        if project.private and not account.permission_read.can():
            return abortify(403)
        package = Package.get_by_version(project.id, version)
        if not package:
            return abortify(404, message=_('Package not found.'))
        #TODO
        return
    if request.method == 'POST':
        if not account.permission_write.can():
            return abortify(403)
        package = Package.get_by_version(project.id, version)
        if not package:
            create_package(project, version)
            res = jsonify(status='info', message=_('Package created.'))
            res.status_code = 201
            return res

    if request.method == 'PUT':
        # stream file
        pass


@bp.route('/search')
def search():
    pass


# helpers

def abortify(code, **kwargs):
    if code == 403 and not g.user:
        code = 401
        kwargs = dict(message=_('Authorization required.'))

    if code == 403 and not kwargs:
        kwargs = dict(message=_('Permission denied.'))

    if 'status' not in kwargs:
        kwargs['status'] = 'error'
    response = jsonify(**kwargs)
    response.status_code = code
    return abort(response)


def _get_request_data():
    if not g.user:
        return abortify(
            401, message=_('Authorization required.')
        )
    if request.json:
        return request.json
    ctype = request.headers.get('CONTENT-TYPE')
    if not request.json and ctype == 'application/json':
        return {}
    return abortify(400, message=_('Only application/json is allowed.'))


def create_project(owner, name=None):
    data = _get_request_data()
    if name and 'name' not in data:
        data['name'] = name
    data = werkzeug.datastructures.MultiDict(data)
    form = ProjectForm(data, csrf_enabled=False, owner=owner)
    if form.validate():
        return form.save()
    return abortify(406, message=_('Request invalid.'))


def update_project(project, owner, name=None):
    data = _get_request_data()
    if name and 'name' not in data:
        data['name'] = name
    data = werkzeug.datastructures.MultiDict(data)
    form = ProjectForm(data, csrf_enabled=False, obj=project, owner=owner)
    if form.validate():
        form.populate_obj(project)
        project.save()
        return project
    return abortify(406, message=_('Request invalid.'))


def create_package(project, version=None):
    data = _get_request_data()
    if 'version' in data:
        version = data['version']
    try:
        version = StrictVersion(version)
    except:
        return abortify(406, message=_('Invalid version.'))
    dependencies = data.get('dependencies', [])
    if not isinstance(dependencies, list):
        return abortify(406, message=_('Invalid dependencies.'))
    dct = {}
    dct['version'] = str(version)
    dct['dependencies'] = ' '.join(dependencies)
    dct['md5value'] = data.get('md5')

    for key in ['tag', 'readme', 'download_url']:
        if data.get(key, None):
            dct[key] = data.get(key)

    if 'tag' not in dct and version.prerelease:
        dct['tag'] = 'unstable'
    dct['project_id'] = project.id
    pkg = Package(**dct)
    pkg.save()
    return pkg


def delete_package(project, package):
    # only owner can delete it
    if project.account_id == g.user.id:
        #TODO
        db.session.delete(package)
        db.session.commit()
        return jsonify(status='info', message=_('Package deleted.'))
    return jsonify(
        status='error',
        code=403,
        message=_('Permission denied.')
    )


def upload_package():
    pass
