# coding: utf-8

import os
import hashlib
import mimetypes
from flask import Blueprint, current_app
from flask import g, request, jsonify, abort
from flask import json, Response
from distutils.version import StrictVersion
from flask.ext.babel import gettext as _
from ..models import Project, Package, Account, package_signal
from ..elastic import search_project

__all__ = ['bp']

bp = Blueprint('repository', __name__)


@bp.route('/')
def index():
    projects = Project.query.order_by(Project.updated_at.desc()).all()

    if projects:
        projects = map(lambda p: p.to_dict(), projects)
    else:
        projects = []

    return Response(json.dumps(projects), content_type='application/json')


@bp.route('/<family>/')
def family(family):
    projects = Project.query.filter_by(family=family)\
            .order_by(Project.updated_at.desc()).all()
    if projects:
        projects = map(lambda p: p.to_dict(), projects)
        return Response(json.dumps(projects), content_type='application/json')

    projects = Project.list(family)
    if not projects:
        return abortify(404, message=_('Family not found.'))
    return Response(json.dumps(projects), content_type='application/json')


@bp.route('/<family>/<name>/', methods=['GET', 'DELETE'])
def project(family, name):
    project = Project.query.filter_by(family=family, name=name).first()

    if request.method == 'GET':
        if project:
            return jsonify(project.json)
        project = Project.read(family, name)
        if project:
            return jsonify(project)

    if not project:
        return abortify(404, message=_('Project not found.'))

    account = Account.query.filter_by(name=family).first()
    if not account:
        return abortify(404, message=_('Family not found.'))

    if not account.permission_write.can():
        return abortify(403)
    #TODO
    project.delete()
    return jsonify(status='info', message=_('Project is deleted.'))


@bp.route(
    '/<family>/<name>/<version>/',
    methods=['GET', 'POST', 'PUT', 'DELETE'])
def package(family, name, version):
    """Create, delete, upload, and get information of a package."""

    try:
        _ver = StrictVersion(version)
    except:
        return abortify(
            406, message=_('Invalid version %(version)s.', version=version)
        )

    # get information of a package
    if request.method == 'GET':
        package = Package(family=family, name=name, version=version)
        if not package.read():
            return abortify(404, message=_('Package not found.'))
        return jsonify(package)

    project = Project.query.filter_by(family=family, name=name).first()
    if not project and request.method != 'POST':
        return abortify(404, message=_('Project not found.'))

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
    if package.read() and package.md5 and not force:
        return abortify(444)

    # register package information
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

        data = request.json or {}
        if 'tag' not in data and _ver.prerelease:
            data['tag'] = 'unstable'
        else:
            data['tag'] = 'stable'

        package.update(data)
        package.save()
        return jsonify(package)

    # upload files for a package
    if request.method == 'PUT':
        if not package:
            return abortify(404, message=_('Package not found.'))
        upload(package)
        project.update(**package)
        package_signal.send(current_app, changes=(project, 'update'))
        return jsonify(package)

    # TODO delete package
    package.delete()


@bp.route('/<family>/<name>/<version>/<filename>')
def tarball(family, name, version, filename):
    root = current_app.config['WWW_ROOT']
    fpath = os.path.join(root, 'repository', family, name, version, filename)
    if not os.path.exists(fpath):
        return abortify(404)
    ctype, encoding = mimetypes.guess_type(filename)
    if not ctype:
        ctype = 'text/html'
    with open(fpath, 'rb') as f:
        data = f.read()
        resp = Response(data, content_type=ctype)
        if encoding:
            resp.content_encoding = encoding
        return resp


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


def upload(package):
    encoding = request.headers.get('Content-Encoding')
    ctype = request.headers.get('Content-Type')
    if ctype == 'application/x-tar' and encoding == 'gzip':
        ctype = 'application/x-tar-gz'
    if ctype not in ('application/x-tar-gz', 'application/x-tgz'):
        return abortify(415, message=_('Only gziped tar file is allowed.'))

    force = request.headers.get('X-Yuan-Force', False)
    if package.md5 and not force:
        return abortify(444)

    package.md5 = hashlib.md5(request.data).hexdigest()
    md5 = request.headers.get('X-Package-MD5', None)
    if md5 and md5 != package.md5:
        return abortify(400, message=_('MD5 does not match.'))

    filename = '%s-%s.tar.gz' % (package.name, package.version)
    directory = package.directory
    if not os.path.exists(directory):
        os.makedirs(directory)

    f = open(os.path.join(directory, filename), 'wb')
    f.write(request.data)
    f.close()
    package.filename = filename
    package.save()
    return package
