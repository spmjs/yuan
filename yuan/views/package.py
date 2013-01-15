# coding: utf-8

import werkzeug
from flask import Blueprint
from flask import g, request, jsonify, abort
from flask.ext.babel import gettext as _
from ..models import db, Project, Package, Account
from ..forms import ProjectForm

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
        return jsonify(status='success', data=dict(project))

    if request.method == 'POST':
        if project and account.permission_write.can():
            # edit project
            pass
        if not project and account.permission_admin.can():
            project = create_project(account)
            return jsonify(status='success', message=_('Project created.'))
        return abortify(403)

    if not project:
        return abortify(404, message=_('Project not found.'))

    if not account.permission_admin.can():
        return abortify(403)
    project.delete()
    return jsonify(status='success', message=_('Project deleted.'))


@bp.route('/<root>/<pkg>/<version>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def package(root, pkg, version):
    account = Account.query.filter_by(name=root).first()
    if not account:
        response = jsonify(
            status='error',
            message=_('Invalid account.'),
        )
        response.status_code = 404
        return response

    project = Project.query.filter_by(name=pkg).first()
    if not project and request.method != 'POST':
        response = jsonify(
            status='error',
            message=_('Package not exists.')
        )
        response.status_code = 404
        return response

    if not project:
        response = jsonify(
            status='info',
            message=_('Package created.')
        )
        response.status_code = 201
        return response

    if project.private:
        #TODO permission check
        return jsonify(
            status='error',
            message=_('This is a private package.')
        )

    package = Package.query.filter_by(
        project_id=project.id, version=version
    ).first()
    if package and request.method == 'POST':
        # if it is force?
        return jsonify(
            status='error',
            message=_('Package exists. Force to write it?')
        )

    if request.method == 'DELETE':
        return delete_package(project, package)


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
    if not request.json:
        return abortify(400, message=_('Only application/json is allowed.'))
    return request.json


def create_project(org):
    data = werkzeug.datastructures.MultiDict(_get_request_data())
    form = ProjectForm(data, csrf_enabled=False)
    if form.validate():
        return form.save(org)
    return abortify(406, message=_('Request invalid.'))


def create_package():
    pass


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
