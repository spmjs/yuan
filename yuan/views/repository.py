# coding: utf-8

import os
import hashlib
import mimetypes
import tarfile
import werkzeug
import tempfile
import shutil
from flask import Blueprint, current_app
from flask import g, request, jsonify, abort
from flask import json, Response
from distutils.version import StrictVersion
from flask.ext.babel import gettext as _
from ..models import Project, Package, Account
from ..models import project_signal, package_signal
from ..search import search_project

__all__ = ['bp']

bp = Blueprint('repository', __name__)


@bp.route('/')
def index():
    repo = os.path.join(current_app.config['WWW_ROOT'], 'repository')
    if not os.path.exists(repo):
        return Response('[]', content_type='application/json')

    def list_projects():
        for name in Project.all():
            yield Project.list(name)

    projects = []
    for proj in list_projects():
        projects.extend(proj)

    projects = map(lambda o: '%(family)s/%(name)s' % o, projects)
    return Response(json.dumps(projects), content_type='application/json')


@bp.route('/<path:filename>.json')
def jsonfile(filename):
    repo = os.path.join(current_app.config['WWW_ROOT'], 'repository')
    fpath = os.path.join(repo, '%s.json' % filename)

    if not os.path.exists(fpath):
        return abortify(404)

    with open(fpath, 'r') as f:
        data = json.load(f)
        return Response(json.dumps(data), content_type='application/json')


@bp.route('/<family>/')
def family(family):
    projects = Project.list(family)
    if not projects:
        return abortify(404, message=_('Family not found.'))
    return Response(json.dumps(projects), content_type='application/json')


@bp.route('/<family>/<name>/', methods=['GET', 'DELETE'])
def project(family, name):
    project = Project(family=family, name=name)
    if 'created_at' not in project:
        return abortify(404, message=_('Project not found.'))

    if request.method == 'GET':
        return jsonify(project)

    account = Account.query.filter_by(name=family).first()
    allow_anonymous = current_app.config.get('ALLOW_ANONYMOUS', False)
    if not account and not allow_anonymous:
        return abortify(404, message=_('Family not found.'))

    if account and not account.permission_write.can():
        return abortify(403)

    # anyone can delete an anonymous project
    project.delete()
    project_signal.send(current_app, changes=(project, 'delete'))
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

    # verify permission on non-GET request
    project = Project(family=family, name=name)
    if 'created_at' not in project and request.method != 'POST':
        # POST is to create a project, if not return 404
        return abortify(404, message=_('Project not found.'))

    allow_anonymous = current_app.config.get('ALLOW_ANONYMOUS', False)
    if not allow_anonymous and not g.user:
        return abortify(401)

    # account can be a user or organization
    account = Account.query.filter_by(name=family).first()

    if not allow_anonymous and not account:
        return abortify(404, message=_('Family not found.'))

    if account and not account.permission_write.can():
        return abortify(403)

    package = Package(family=family, name=name, version=version)
    if request.method == 'DELETE':
        # only registered user can delete a non-anonymous package
        # we have verified permission above
        project.remove(version)
        package.delete()
        package_signal.send(current_app, changes=(package, 'delete'))
        return jsonify(status='info', message=_('Package is deleted.'))

    # POST or PUT. if the package exists, you need --force option
    force = request.headers.get('X-Yuan-Force', False)
    if package.md5 and not force:
        return abortify(444)

    # register package information
    if request.method == 'POST':
        if package.revision and not force:
            return abortify(444)
        ctype = request.headers.get('Content-Type')
        if not request.json and ctype != 'application/json':
            return abortify(
                415,
                message=_('Only application/json is allowed.')
            )

        if 'created_at' not in project:
            project = Project(family=family, name=name)
            project.save()
            project_signal.send(current_app, changes=(project, 'create'))

        data = request.json or {}
        if 'tag' not in data and _ver.prerelease:
            data['tag'] = 'unstable'
        elif 'tag' not in data:
            data['tag'] = 'stable'

        package.update(data)

        if g.user:
            # record publisher
            package.publisher = g.user.name

        package.save()
        package_signal.send(current_app, changes=(package, 'update'))

        project.update(package)
        project = project.save()
        project_signal.send(current_app, changes=(project, 'update'))
        return jsonify(package)

    # upload files for a package
    if request.method == 'PUT':
        if not package:
            return abortify(404, message=_('Package not found.'))
        upload_package(package)
        package_signal.send(current_app, changes=(package, 'upload'))

        project.update(package)
        project.save()
        project_signal.send(current_app, changes=(project, 'update'))
        return jsonify(package)


@bp.route('/<family>/<name>/<version>/<filename>')
def tarball(family, name, version, filename):
    # this will not work in production
    # nginx will stop it

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
    results = search_project(q)
    ret = []
    for item in results:
        value = item.fields()
        keywords = value.get('keywords')
        if keywords:
            value['keywords'] = keywords.split(',')
        ret.append(value)
    data = dict(
        total=len(ret),
        results=ret,
    )
    return jsonify(status='success', data=data)


@bp.route('/upload/<family>', methods=['POST'])
def upload(family):
    allow_anonymous = current_app.config.get('ALLOW_ANONYMOUS', False)
    if not allow_anonymous and not g.user:
        # documentation are designed for registered users
        return abortify(401)

    account = Account.query.filter_by(name=family).first()

    if not allow_anonymous and not account:
        return abortify(404)

    if account and not account.permission_write.can():
        return abortify(403)

    tarball = request.files.get('file')
    if 'file' not in request.files:
        return abortify(406, message=_('file is missing.'))

    try:
        tar = tarfile.open(fileobj=tarball, mode='r:gz')
    except:
        return abortify(415)

    name = request.form.get('name', family)
    tag = request.form.get('tag', 'latest')

    filename = '%s-%s-%s' % (
        family, name, werkzeug.secure_filename(tarball.filename)
    )
    fpath = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(fpath):
        shutil.rmtree(fpath)

    def _members(tar):
        for info in tar:
            if os.path.basename(info.name).startswith('.'):
                continue
            ext = os.path.splitext(info.name)[1]
            # ignore some danger files
            if ext not in ['.php'] and not info.name.startswith('.'):
                yield info

    tar.extractall(path=fpath, members=_members(tar))

    rootdir = fpath
    indir = os.listdir(fpath)
    if len(indir) == 1 and os.path.isdir(os.path.join(fpath, indir[0])):
        rootdir = os.path.join(fpath, indir[0])

    if tag == 'latest':
        dest = os.path.join(
            current_app.config['WWW_ROOT'], 'docs', family, name
        )
    else:
        dest = os.path.join(
            current_app.config['WWW_ROOT'], 'archive', family, name, tag
        )

    if os.path.exists(dest):
        shutil.rmtree(dest)

    version = request.form.get('version')
    error = None
    if version:
        verdir = os.path.join(
            current_app.config['WWW_ROOT'], 'archive',
            family, name, version
        )
        if os.path.exists(verdir):
            shutil.rmtree(verdir)

        try:
            shutil.copytree(rootdir, verdir)
        except Exception as e:
            error = e.message

    shutil.move(rootdir, dest)
    if error:
        return jsonify(status='error', message=error)
    return jsonify(status='info', message=_('upload docs success.'))


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


def upload_package(package):
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
    directory = os.path.dirname(package.datafile)
    if not os.path.exists(directory):
        os.makedirs(directory)

    f = open(os.path.join(directory, filename), 'wb')
    f.write(request.data)
    f.close()
    package.filename = filename
    package.save()
    return package
