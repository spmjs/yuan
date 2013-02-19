# coding: utf-8

import os
import werkzeug
import hashlib
from flask import Blueprint, current_app
from flask import g, request, jsonify, abort
from distutils.version import StrictVersion
from flask.ext.babel import gettext as _
from ..models import Project, Package, Account, db
from ..forms import ProjectForm
from ..elastic import search_project

__all__ = ['bp']

bp = Blueprint('repository', __name__)


@bp.route('/')
def index():
    #TODO pagination
    data = db.session.query(Account.name).all()
    data = map(lambda o: o[0], data)
    return jsonify(status='success', data=data)


@bp.route('/<name>/')
def account(name):
    account = Account.query.filter_by(name=name).first()
    if not account:
        return abortify(404, message=_('Account not found.'))
    if account.permission_read.can():
        projects = db.session.query(Project.name)\
                .filter_by(owner_id=account.id).all()
    else:
        projects = db.session.query(Project.name)\
                .filter_by(owner_id=account.id, private=False).all()
    projects = map(lambda o: o[0], projects)
    data = {
        'account': {
            'name': name,
            'type': account.account_type,
        },
        'projects': projects,
    }
    return jsonify(status='success', data=data)


@bp.route('/<name>/<pkg>/', methods=['GET', 'POST', 'DELETE'])
def project(name, pkg):
    """Create, delete, and get information of a project on these conditions:

        1. Public projects can be read by all users.
        2. Private projects can be only accessable by group members.
        3. Projects can be only created by users who has write permission.
        4. Projects can be only deleted by users who has admin permission.
    """

    # account can be a user or organization
    account = Account.query.filter_by(name=name).first()
    if not account:
        return abortify(404, message=_('Account not found.'))

    #TODO: cache it
    project = Project.query.filter_by(owner_id=account.id, name=pkg).first()
    if request.method == 'GET':
        if not project:
            return abortify(404, message=_('Project not found.'))
        if project.private and not account.permission_read.can():
            return abortify(403)
        tag = request.args.get('tag', None)
        data = project.tagged_project(tag)
        data['account'] = name
        return jsonify(status='success', data=data)

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

    if account.permission_admin.can():
        project.delete()
        return jsonify(status='info', message=_('Project deleted.'))
    return abortify(403)


@bp.route('/<name>/<pkg>/<version>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def package(name, pkg, version):
    """Create, delete, upload, and get information of a package."""

    # account can be a user or organization
    account = Account.query.filter_by(name=name).first()
    if not account:
        return abortify(404, message=_('Account not found.'))

    project = Project.query.filter_by(owner_id=account.id, name=pkg).first()
    if not project and request.method != 'POST':
        return abortify(404, message=_('Project not found.'))

    if not project:
        if not account.permission_admin.can():
            return abortify(403)
        # POST method will create project
        project = create_project(account, pkg)

    # get information of a package
    if request.method == 'GET':
        if project.private and not account.permission_read.can():
            return abortify(403)
        package = Package.get_by_version(project.id, version)
        if not package:
            return abortify(404, message=_('Package not found.'))
        data = package.dict_with_project(project)
        data['account'] = name
        # TODO: analyse hits
        return jsonify(status='success', data=data)

    package = Package.get_by_version(project.id, version)
    # create or update information of a package
    if request.method == 'POST':
        if not account.permission_write.can():
            return abortify(403)
        if not package:
            data = _get_package_data(project, version)
            package = Package(**data)
            package.save()

            res = jsonify(
                status='success',
                data=package.dict_with_project(project)
            )
            res.status_code = 201
            return res
        isforce = request.headers.get('X-Yuan-Force', False)
        if not isforce:
            return abortify(444)
        data = _get_package_data(project, version)
        for key in data:
            setattr(package, key, data[key])
        package.save()
        # update project information
        update_project(project, account, pkg)
        return jsonify(
            status='success',
            data=package.dict_with_project(project)
        )

    # upload files for a package
    if request.method == 'PUT':
        if not account.permission_write.can():
            return abortify(403)
        if not package:
            return abortify(404, message=_('Package not found.'))
        upload_package(project, package, account)
        return jsonify(status='info', message=_('Package uploaded.'))

    # delete a package
    if account.permission_admin.can():
        if package:
            package.delete()
        return jsonify(status='info', message=_('Package deleted.'))
    return abortify(403)


@bp.route('/search')
def search():
    q = request.args.get('q', None)
    if not q:
        return abortify(404)
    data = search_project(q)
    return jsonify(status='success', data=data)


# helpers

def abortify(code, **kwargs):
    if code in (403, 406, 415) and not g.user:
        code = 401

    msgs = {
        400: _('Bad request.'),
        401: _('Authorization required.'),
        403: _('Permission denied.'),
        404: _('Not found.'),
        406: _('Not acceptable.'),
        415: _('Unsupported media type.'),
        426: _('Upgrade required.'),
        444: _('Force option required.'),
    }
    if 'message' not in kwargs and code in msgs:
        kwargs['message'] = msgs[code]

    if 'status' not in kwargs:
        kwargs['status'] = 'error'

    response = jsonify(**kwargs)
    response.status_code = code
    return abort(response)


def _get_request_data():
    if not g.user:
        return abortify(401)
    if request.json:
        if 'repository' in request.json and \
           isinstance(request.json['repository'], dict):
            repo = request.json['repository']
            if 'url' in repo:
                request.json['repository'] = repo['url']
            else:
                request.json['repository'] = None
        return request.json
    ctype = request.headers.get('Content-Type')
    if not request.json and ctype == 'application/json':
        return {}
    return abortify(415, message=_('Only application/json is allowed.'))


def create_project(owner, name=None):
    data = _get_request_data()
    if name and 'name' not in data:
        data['name'] = name

    data = werkzeug.datastructures.MultiDict(data)
    form = ProjectForm(data, csrf_enabled=False, owner=owner)
    if form.validate():
        proj = form.save()
        if 'keywords' in data and isinstance(data['keywords'], list):
            proj.keywords = ' '.join(data['keywords'])
        proj.save()
        return proj
    return abortify(406, message=_('Request invalid.'))


def update_project(project, owner, name=None):
    data = _get_request_data()
    if name and 'name' not in data:
        data['name'] = name
    data = werkzeug.datastructures.MultiDict(data)
    form = ProjectForm(data, csrf_enabled=False, obj=project, owner=owner)
    if form.validate():
        form.populate_obj(project)
        if 'keywords' in data and isinstance(data['keywords'], list):
            project.keywords = ' '.join(data['keywords'])
        project.save()
        return project
    return abortify(406, message=_('Request invalid.'))


def _get_package_data(project, version=None):
    data = _get_request_data()
    if 'version' in data:
        version = data['version']
    try:
        _ver = StrictVersion(version)
    except:
        return abortify(406, message=_(
            'Invalid version %(version)s.', version=version))
    dependencies = data.get('dependencies', [])
    if not isinstance(dependencies, list):
        return abortify(406, message=_('Invalid dependencies.'))
    dct = {}
    dct['version'] = version
    dct['dependencies'] = ' '.join(dependencies)
    dct['md5value'] = data.get('md5')

    for key in ['tag', 'readme', 'download_url']:
        if data.get(key, None):
            dct[key] = data.get(key)

    if 'tag' not in dct and _ver.prerelease:
        dct['tag'] = 'unstable'
    dct['project_id'] = project.id
    return dct


def upload_package(project, package, owner):
    encoding = request.headers.get('Content-Encoding')
    ctype = request.headers.get('Content-Type')
    if ctype == 'application/x-tar' and encoding == 'x-gzip':
        ctype = 'application/x-tar-gz'
    if ctype not in ('application/x-tar-gz', 'application/x-tgz'):
        return abortify(415, message=_('Only gziped tar file is allowed.'))

    force = request.headers.get('X-Yuan-Force', False)
    if package.download_url and not force:
        return abortify(444)

    package.md5value = hashlib.md5(request.data).hexdigest()
    md5 = request.headers.get('X-Package-MD5', None)
    if md5 and md5 != package.md5value:
        return abortify(400, message=_('MD5 does not match.'))

    if project.private:
        token = '%s-%s' % (current_app.secret_key, repr(package))
        hsh = hashlib.md5(token).hexdigest()
        filename = '%s-%s.tar.gz' % (project.name, hsh)
        directory = current_app.config['PACKAGE_STORAGE_PRIVATE']
    else:
        filename = '%s-%s.tar.gz' % (project.name, package.version)
        directory = current_app.config['PACKAGE_STORAGE_PUBLIC']
    filepath = os.path.join(directory, owner.name, project.name, filename)
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)

    f = open(filepath, 'wb')
    f.write(request.data)
    f.close()
    package.download_url = '%s/%s/%s' % (owner.name, project.name, filename)
    package.save()
    return package
