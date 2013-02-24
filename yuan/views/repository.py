# coding: utf-8

import os
import hashlib
from flask import Blueprint, current_app
from flask import g, request, jsonify, abort
from flask import json, Response
from distutils.version import StrictVersion
from flask.ext.babel import gettext as _
from ..models import Project, Package, Account
from ..elastic import search_project

__all__ = ['bp']

bp = Blueprint('repository', __name__)


@bp.route('/')
def index():
    projects = Project.query.all()

    if projects:
        projects = map(lambda p: p.to_dict(), projects)
    else:
        projects = []

    return Response(json.dumps(projects), content_type='application/json')


@bp.route('/<family>/')
def family(family):
    projects = Project.query.filter_by(family=family).all()

    if projects:
        projects = map(lambda p: p.to_dict(), projects)
    else:
        projects = []

    return Response(json.dumps(projects), content_type='application/json')


@bp.route('/<family>/<name>/', methods=['GET', 'DELETE'])
def project(family, name):
    project = Project.query.filter_by(family=family, name=name).first()
    if not project:
        return abortify(404, message=_('Project not found.'))

    if request.method == 'GET':
        return jsonify(project.json)

    account = Account.query.filter_by(name=family).first()
    if not account:
        return abortify(404, message=_('Family not found.'))

    if not account.permission_write.can():
        return abortify(403)
    project.delete()
    return jsonify(status='info', message=_('Project is deleted.'))


@bp.route(
    '/<family>/<name>/<version>/',
    methods=['GET', 'POST', 'PUT', 'DELETE'])
def package(family, name, version):
    """Create, delete, upload, and get information of a package."""

    project = Project.query.filter_by(family=family, name=name).first()

    if not project and request.method != 'POST':
        return abortify(404, message=_('Project not found.'))

    # get information of a package
    if request.method == 'GET':
        package = Package(family=family, name=name, version=version)
        if not package.read():
            return abortify(404, message=_('Package not found.'))
        return jsonify(package)

    # verify permissions and request data
    if not g.user:
        return abortify(401)

    # account can be a user or organization
    account = Account.query.filter_by(name=family).first()
    if not account:
        return abortify(404, message=_('Account not found.'))

    if not account.permission_write.can():
        return abortify(403)

    force = request.headers.get('X-Yuan-Force', False)
    package = Package(family=family, name=name, version=version)
    if package.read() and not force:
        return abortify(444)

    if request.method == 'POST':
        ctype = request.headers.get('Content-Type')
        if not request.json and ctype != 'application/json':
            return abortify(
                415,
                message=_('Only application/json is allowed.')
            )

        if not project:
            project = Project(family=family, name=name)
            project.save()

        package.update(request.json or {})
        project.update(package)
        return jsonify(project.json)

    # upload files for a package
    if request.method == 'PUT':
        if not package:
            return abortify(404, message=_('Package not found.'))
        upload_package(project, package, account)
        return jsonify(status='info', message=_('Package uploaded.'))
    # TODO delete package
    package.delete()


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
        return request.json
    ctype = request.headers.get('Content-Type')
    if not request.json and ctype == 'application/json':
        return {}
    return abortify(415, message=_('Only application/json is allowed.'))


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
