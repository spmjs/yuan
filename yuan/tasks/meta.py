import os
from flask import current_app, json
from ..models import Package


def latest_publish(package, operation):
    fpath = os.path.join(
        current_app.config["WWW_ROOT"], "repository",
        "latest.json"
    )
    latest_publish_obj = _read_json(fpath, [])

    if hasattr(package, "publisher"):
        publisher = package.publisher
    else:
        publisher = "anonymous"

    latest_publish_obj.insert(0, {
        "action": operation,
        "publisher": publisher,
        "family": package.family,
        "name": package.name,
        "version": package.version,
        "update_at": package.updated_at
    })

    if len(latest_publish_obj) > current_app.config["LIST_MAX_COUNT"]:
        latest_publish_obj = latest_publish_obj[0:current_app.config["LIST_MAX_COUNT"]]

    json.dump(latest_publish_obj, open(fpath, 'w'))


def most_depended_upon(package, operation):
    dependencies = package.get('dependencies', None)
    if not dependencies:
        return

    fpath = os.path.join(
        current_app.config["WWW_ROOT"], "repository",
        "depend.json"
    )
    depended_obj = _read_json(fpath, {})

    if isinstance(package, Package):
        p = str(package)
    else:
        p = '%s/%s@%s' % (package['family'], package['name'], package['version'])

    for dep in dependencies:
        if '@' not in dep or '/' not in dep:
            continue
        if depended_obj.has_key(dep):
            if dep not in depended_obj[dep]:
                depended_obj[dep].append(p)
        else:
            depended_obj[dep] = [p]

    json.dump(depended_obj, open(fpath, 'w'))


def top_submittors(package, operation):
    fpath = os.path.join(
        current_app.config["WWW_ROOT"], "repository",
        "publishers.json"
    )
    publishers_obj = _read_json(fpath, {})

    if isinstance(package, Package):
        p = str(package)
    else:
        p = '%s/%s@%s' % (package['family'], package['name'], package['version'])

    if hasattr(package, "publisher"):
        publisher = package.publisher
    else:
        publisher = "anonymous"

    if publishers_obj.has_key(publisher):
        publishers_obj[publisher].append(p)
    else:
        publishers_obj[publisher] = [p]

    json.dump(publishers_obj, open(fpath, 'w'))


def meta_info(package, operation):
    if operation == "delete" and os.path.exists(os.path.dirname(package.datafile)) or operation == "update":
        latest_publish(package, operation)
        most_depended_upon(package, operation)
        top_submittors(package, operation)


def _read_json(fpath, default):
    if not os.path.exists(fpath):
        return default
    with open(fpath, 'r') as f:
        try:
            return json.load(f)
        except:
            return default