# coding: utf-8

from flask import Blueprint
from flask import g, request, jsonify
from flask.ext.babel import gettext as _
from ..models import db, Project, Package, Account

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
        response = jsonify(status='error', message=_('Invalid account.'))
        response.status_code = 404
        return response

    project = Project.query.filter_by(name=pkg).first()
    if request.method == 'GET':
        if not project:
            response = jsonify(status='error', message=_('Project not found.'))
            response.status_code = 404
            return response
        if project.permission_read.can():
            # TODO return project json
            return
        response = jsonify(status='error', message=_('Permission denied.'))
        response.status_code = 403
        return response

    if request.method == 'POST':
        if project and account.permission_edit.can():
            # edit project
            pass
        if not project and account.permission_delete.can():
            # create project
            pass
        response = jsonify(status='error', message=_('Permission denied.'))
        response.status_code = 403
        return response

    if project.private:
        #TODO permission check
        return jsonify(
            status='warn', message=_('This is a private package.')
        )

    # TODO permission
    if request.method == 'GET':
        # get information of a project
        if not project:
            return jsonify(
                status='error', message=_('Not found this package.')
            )
    elif request.method == 'POST':
        # edit information of a project
        pass
    elif request.method == 'PUT':
        # upload a package
        pass
    else:
        # delete a package
        pass


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
        print request.data
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

def create_project():
    pass


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
