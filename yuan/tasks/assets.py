import os
import shutil
import tarfile
import tempfile
import werkzeug
from flask import current_app


def extract_assets(package, operation):
    assets = current_app.config.get('ASSETS_ROOT', None)
    if not assets:
        return

    pkgdir = os.path.dirname(package.datafile)
    if operation == 'delete' and os.path.exists(pkgdir):
        shutil.rmtree(pkgdir)
        return

    if operation != 'upload':
        return

    tarball = os.path.join(pkgdir, package.filename)
    if not os.path.exists(tarball):
        return

    try:
        tar = tarfile.open(tarball, mode='r:gz')
    except:
        return

    filename = '%s-%s' % (
        package.family, werkzeug.secure_filename(package.filename)
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

    distdir = os.path.join(rootdir, 'dist')
    if not os.path.exists(distdir):
        return
    pkgfile = os.path.join(rootdir, 'package.json')
    if not os.path.exists(pkgfile):
        return

    dest = os.path.join(assets, package.family, package.name, package.version)

    if os.path.exists(dest):
        shutil.rmtree(dest)

    shutil.move(distdir, dest)
    shutil.move(pkgfile, dest)
    try:
        shutil.rmtree(fpath)
    except:
        return
